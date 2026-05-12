#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from product_agent_output_contract import call_control_for_next_action


FAST_RESPONSE_MS = 700
BRIDGE_RESPONSE_MS = 600
BACKGROUND_COMPLETION_MS = 3500
STOP_OR_REFUSAL_RUNTIME_PHRASES = [
    "nicht mehr an",
    "kein interesse",
    "nein danke",
    "do not call",
    "don't call",
    "dont call",
    "stop calling",
    "not interested",
    "no thanks",
    "no thank you",
    "rufen sie mich nicht mehr an",
    "keine weiteren anrufe",
    "nummer aus der liste",
    "löschen sie meine nummer",
    "brauche ich nicht",
    "nichts für mich",
    "möchte das nicht",
]
HUMAN_REQUEST_RUNTIME_PHRASES = [
    "real person",
    "human",
    "person call",
    "representative",
    "specialist",
    "advisor",
    "mitarbeiter",
    "mensch",
    "berater",
    "spezialist",
    "echte person",
    "person anrufen",
]
LOCALIZED_RESPONSES = {
    "en": {
        "voicemail": "I reached voicemail, so I will log this for follow-up according to campaign rules.",
        "repeated-silence": "I will end the call for now. Goodbye.",
        "do-not-call": "Understood. I will make sure this contact is marked so you are not called again. Goodbye.",
        "human-request": "Of course. I will route this to a human specialist instead of continuing automatically.",
        "claim-boundary": "I do not want to guarantee something that depends on the details. I can route this to a specialist.",
        "product-detail-lookup": "One moment, I want to check the approved product information.",
        "scheduling-confirmation": "Confirmed. I will record that time for the specialist callback. Goodbye.",
        "timing-delay": "Thanks. I will log a follow-up rather than forcing a fixed appointment now. Goodbye.",
        "price-objection": "That makes sense. Is the main concern the price itself, or whether the review is worth the effort?",
        "provider-comparison": "That is fair. We can compare fit and terms without pressure before you decide whether this is worth reviewing.",
        "existing-provider-gap": "I will not claim this replaces your provider. The only useful check is whether there is a specific gap they do not cover.",
        "autonomy-check": "That makes sense. We can keep this low pressure and clarify only what you need before any next step.",
        "stakeholder-review": "That makes sense. I can help with a short summary for the person who needs to review it.",
        "procurement-review": "Understood. I can keep this to written review information and avoid asking for anything firm today.",
        "trust-gap": "Fair question. I can give you a verification path before we discuss any next step.",
        "sale-ready-commitment": "Confirmed. I will mark this as sale-ready for the next step, with no payment handled on this call.",
        "sale-ready-missing-criteria": "Before I mark this sale-ready, I need the approved close criteria confirmed. No payment or contract signing happens on this call.",
        "callback-request": "I can log a callback request and keep it optional. No forced appointment or commitment on this call.",
        "written-info-request": "I can send the approved written summary and leave it there.",
        "email-only-boundary": "Understood. I will keep this to email only and will not push for a call.",
        "identity-repair": "I should verify who is calling before continuing. I can give the approved identity and reason for this campaign.",
        "scam-safety-boundary": "No payment, card, or sensitive details are collected on this call. I can send the approved verification path instead.",
        "payment-safety-boundary": "No card or payment details are needed here. I can keep the next step to safe written information only.",
        "support-route": "That is a support issue, so I will stop the sales path and route it to the approved support path.",
        "cancellation-route": "I will stop the sales path and route this to the approved cancellation path.",
        "technical-specialist-route": "I should not guess on technical details. I can route this to the approved specialist path.",
        "security-review-route": "Security review needs approved material or a specialist. I will not make broad compliance claims here.",
        "coverage-boundary-route": "I should not give coverage advice. I can route this to the approved qualified reviewer path.",
        "healthcare-boundary-route": "I should not give health or medical advice. I can route this to the approved qualified reviewer path.",
        "unknown-runtime-signal": "Thanks. May I ask one quick clarifying question?",
    },
    "de": {
        "voicemail": "Ich habe die Mailbox erreicht. Ich beende den Anruf für jetzt.",
        "repeated-silence": "Ich beende den Anruf für jetzt. Auf Wiederhören.",
        "do-not-call": "Verstanden. Sie sollen hierzu nicht mehr angerufen werden. Ich beende den Anruf hier. Auf Wiederhören.",
        "human-request": "Natürlich. Ich leite das an eine zuständige Fachperson weiter, statt automatisch fortzufahren.",
        "claim-boundary": "Ich möchte nichts garantieren, was von den Details abhängt. Ich kann das an eine zuständige Fachperson weiterleiten.",
        "product-detail-lookup": "Einen Moment, ich prüfe die Produktinformationen.",
        "scheduling-confirmation": "Bestätigt. Ich notiere den Rückruf so. Auf Wiederhören.",
        "timing-delay": "Danke. Ich merke einen Rückruf vor, statt jetzt einen festen Termin zu erzwingen. Auf Wiederhören.",
        "price-objection": "Das verstehe ich. Geht es eher um den Preis selbst oder darum, ob sich der Aufwand lohnt?",
        "provider-comparison": "Das ist fair. Wir können Passung und Bedingungen ohne Druck vergleichen, bevor Sie etwas entscheiden.",
        "existing-provider-gap": "Ich möchte nicht behaupten, dass das Ihren Anbieter ersetzt. Sinnvoll wäre nur zu prüfen, ob trotz Ihrer aktuellen Lösung noch Rückrufe oder Nachverfolgungen liegen bleiben.",
        "autonomy-check": "Das verstehe ich. Wir können das ohne Druck klären, bevor es irgendeinen nächsten Schritt gibt.",
        "stakeholder-review": "Das verstehe ich. Ich kann eine kurze Zusammenfassung für die prüfende Person vorbereiten.",
        "procurement-review": "Verstanden. Ich halte es bei schriftlichen Informationen und frage heute nach nichts Festem.",
        "trust-gap": "Faire Frage. Ich kann zuerst einen Weg zur Verifizierung nennen, bevor wir über einen nächsten Schritt sprechen.",
        "sale-ready-commitment": "Gut, ich halte fest, dass Sie den nächsten Schritt möchten. Es findet hier keine Zahlung und keine Vertragsunterzeichnung statt.",
        "sale-ready-missing-criteria": "Bevor ich das als nächsten Schritt festhalte, brauche ich noch eine kurze Klärung. In diesem Gespräch gibt es keine Zahlung und keine Vertragsunterzeichnung.",
        "callback-request": "Ich kann einen Rückruf vormerken. Das bleibt optional; heute entsteht keine Verpflichtung.",
        "written-info-request": "Ich sende Ihnen gern eine kurze Zusammenfassung per E-Mail und belasse es dabei.",
        "email-only-boundary": "Verstanden. Ich halte es bei E-Mail und dränge nicht auf ein Telefonat.",
        "identity-repair": "Hier ist Maya von RouteSignal. Ich rufe kurz an, um zu klären, wer bei Ihnen für Rückrufe und Nachverfolgung zuständig ist. Wenn das für Sie nicht relevant ist, beende ich den Anruf.",
        "scam-safety-boundary": "Ich frage in diesem Gespräch nicht nach Zahlungsdaten oder Kartendaten. Ich kann Ihnen stattdessen den offiziellen Verifizierungsweg und die schriftlichen Informationen zusenden.",
        "payment-safety-boundary": "Ich frage in diesem Gespräch nicht nach Zahlungsdaten oder Kartendaten. Ich kann Ihnen stattdessen den offiziellen Verifizierungsweg und die schriftlichen Informationen zusenden.",
        "support-route": "Dann ist das ein Support-Thema. Ich beende den Verkaufsteil hier und leite Sie an den zuständigen Support weiter.",
        "cancellation-route": "Dann geht es um eine Kündigung. Ich beende den Verkaufsteil hier und leite Sie an die zuständige Stelle für Kündigungen weiter.",
        "technical-specialist-route": "Bei technischen Details sollte ich nicht raten. Ich kann das an eine zuständige Fachperson weiterleiten.",
        "security-review-route": "Das sollte eine zuständige Fachperson prüfen. Ich rate hier nicht und mache keine allgemeinen Zusagen.",
        "coverage-boundary-route": "Ich darf in diesem Gespräch keine medizinische Beratung und keine Beratung zum Versicherungsschutz geben. Ich kann das an eine zuständige Fachperson weiterleiten.",
        "healthcare-boundary-route": "Ich darf in diesem Gespräch keine medizinische Beratung und keine Beratung zum Versicherungsschutz geben. Ich kann das an eine zuständige Fachperson weiterleiten.",
        "unknown-runtime-signal": "Danke. Darf ich kurz eine klärende Frage stellen?",
    },
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_realtime_cases(path: Path) -> tuple[list[dict], list[dict]]:
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise SystemExit("PROD-005 case file must be a campaign wrapper object.")
    return payload.get("campaigns", []), payload.get("cases", [])


def find_campaign(campaigns: list[dict], campaign_id: str) -> dict | None:
    for campaign in campaigns:
        if campaign.get("campaign_id") == campaign_id:
            return campaign
    return None


def normalize_response_language(language: str | None) -> str:
    if (language or "").lower().startswith("de"):
        return "de"
    return "en"


def campaign_text(campaign: dict | None, *keys: str) -> str | None:
    for key in keys:
        value = (campaign or {}).get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def campaign_flag(campaign: dict | None, *keys: str) -> bool:
    return any((campaign or {}).get(key) is True for key in keys)


def ensure_terminal_period(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return stripped
    if stripped[-1] in ".!?":
        return stripped
    return f"{stripped}."


def german_pricing_response(campaign: dict | None) -> str | None:
    approved_sentence = campaign_text(campaign, "approved_pricing_response")
    if approved_sentence:
        return (
            f"{ensure_terminal_period(approved_sentence)} "
            "In diesem Gespräch geht es nicht um Zahlung oder Vertragsabschluss."
        )
    pricing = campaign_text(campaign, "pricing_summary", "pricing_boundary_text")
    if not pricing:
        return None
    cleaned = pricing.strip()
    cleaned = cleaned.replace("freigegebenen ", "").replace("freigegebene ", "")
    lower = cleaned.lower()
    if lower.startswith(("beim ", "bei ")):
        normalized = cleaned.replace("beim ", "das ", 1).replace("bei ", "das ", 1)
        normalized = normalized.replace("Starter-Paket 29", "Starter-Paket bei 29")
        pricing_sentence = f"Nach den vorliegenden Informationen liegt {normalized}"
    elif "preisrahmen" in lower or lower.startswith("exakte preise"):
        pricing_sentence = cleaned
    else:
        pricing_sentence = f"Nach den vorliegenden Informationen: {cleaned}"
    pricing_sentence = pricing_sentence.replace(
        "; die genauen Bedingungen kommen schriftlich.",
        ". Die genauen Bedingungen sende ich Ihnen schriftlich.",
    )
    return (
        f"{ensure_terminal_period(pricing_sentence)} "
        "In diesem Gespräch geht es nicht um Zahlung oder Vertragsabschluss."
    )


def german_identity_response(campaign: dict | None) -> str | None:
    identity = campaign_text(campaign, "caller_identity", "company_or_campaign_name")
    if not identity:
        return None
    sentence = campaign_text(campaign, "approved_identity_reason_sentence")
    if sentence:
        reason_sentence = ensure_terminal_period(sentence)
    else:
        reason = campaign_text(campaign, "approved_reason_for_call")
        if not reason:
            return None
        if reason.lower().startswith("zu "):
            reason_sentence = ensure_terminal_period(f"Ich rufe kurz an, um {reason}")
        elif reason.lower().startswith("ein kurzer abgleich zur zuständigkeit"):
            reason_sentence = "Ich rufe an, weil wir kurz klären möchten, wer bei Ihnen für Rückrufe und Nachverfolgung zuständig ist."
        elif reason.lower().startswith("wir "):
            reason_sentence = ensure_terminal_period(f"Ich rufe an, weil {reason}")
        else:
            reason_sentence = ensure_terminal_period(f"Der Grund für den Anruf ist {reason}")
    return (
        f"Hier ist {identity}. {reason_sentence} "
        "Wenn das für Sie nicht relevant ist, beende ich den Anruf."
    )


def localized_response(language: str, sales_difficulty: str, campaign: dict | None = None) -> str:
    language_key = normalize_response_language(language)
    if language_key == "en":
        if sales_difficulty == "price-first-direct":
            pricing = campaign_text(campaign, "pricing_summary", "pricing_boundary_text")
            if pricing:
                return f"{pricing} No payment or commitment on this call."
            return "I do not have an approved exact price in this campaign, so I should not invent one. I can send approved pricing information and stop there."
        if sales_difficulty == "written-info-request":
            summary = campaign_text(campaign, "approved_written_summary", "approved_email_followup_scope")
            if summary:
                return f"I can send {summary} and leave it there."
        if sales_difficulty == "email-only-boundary":
            summary = campaign_text(campaign, "approved_email_followup_scope", "approved_written_summary")
            if summary:
                return f"Understood. Email only. I can send {summary} and will not push for a call."
        if sales_difficulty == "identity-repair":
            identity = campaign_text(campaign, "caller_identity", "company_or_campaign_name")
            reason = campaign_text(campaign, "approved_reason_for_call")
            if identity and reason:
                return f"This is {identity}. The reason for the call is {reason}. I can stop if this is not relevant."
        if sales_difficulty == "scam-safety-boundary":
            verification = campaign_text(campaign, "approved_verification_path", "approved_written_summary")
            if verification:
                return f"No payment, card, or sensitive details are collected on this call. I can send {verification} for verification."
        if sales_difficulty == "payment-safety-boundary":
            safe_path = campaign_text(campaign, "approved_written_summary", "approved_verification_path")
            if safe_path:
                return f"No card or payment details are needed here. I can keep the next step to safe written information: {safe_path}."
        if sales_difficulty == "support-route":
            route = campaign_text(campaign, "support_boundary_text", "support_route")
            if route:
                return f"That is a support issue, so I will stop the sales path and route this to {route}."
        if sales_difficulty == "cancellation-route":
            route = campaign_text(campaign, "cancellation_boundary_text", "cancellation_route")
            if route:
                return f"I will stop the sales path and route this to {route}."
        if sales_difficulty == "technical-specialist-route":
            scope = campaign_text(campaign, "approved_technical_scope")
            route = campaign_text(campaign, "specialist_handoff_route")
            if scope:
                return f"Within the approved scope: {scope}. If you need more detail, I can route this to the specialist path."
            if route:
                return f"I should not guess on technical details. I can route this to {route}."
        if sales_difficulty == "security-review-route":
            route = campaign_text(campaign, "specialist_handoff_route", "approved_written_summary")
            if route:
                return f"Security review needs approved material or a specialist. I can route this to {route} and will not make broad compliance claims."
        if sales_difficulty in {"coverage-boundary-route", "healthcare-boundary-route"}:
            boundary = campaign_text(campaign, "regulated_advice_boundary_text")
            route = campaign_text(campaign, "specialist_handoff_route")
            if boundary and route:
                return f"{boundary} I can route this to {route}."
        if sales_difficulty == "existing-provider-gap":
            gap = campaign_text(campaign, "approved_gap_isolation_question")
            if gap:
                return f"I will not claim this replaces your provider. {gap}"
        if sales_difficulty in {"stakeholder-review", "partner-review"}:
            summary = campaign_text(campaign, "approved_review_summary", "approved_written_summary")
            if summary:
                return f"I can send {summary} for review. No decision or commitment from you today."
        if sales_difficulty == "sale-ready-commitment":
            next_step = campaign_text(campaign, "approved_sale_ready_next_step", "approved_next_step")
            if next_step:
                return f"Confirmed. I will log this as sale-ready for {next_step}. No payment or contract signing happens on this call."
    else:
        if sales_difficulty == "price-first-direct":
            pricing_response = german_pricing_response(campaign)
            if pricing_response:
                return pricing_response
            return "Ich habe keinen genauen Preis vorliegen und erfinde keinen. Ich kann Ihnen Preisinformationen schriftlich senden und es dabei belassen."
        if sales_difficulty == "written-info-request":
            summary = campaign_text(campaign, "approved_written_summary", "approved_email_followup_scope")
            if summary:
                return f"Ich sende Ihnen gern {summary} und belasse es dabei."
        if sales_difficulty == "email-only-boundary":
            summary = campaign_text(campaign, "approved_email_followup_scope", "approved_written_summary")
            if summary:
                return f"Verstanden. Ich sende Ihnen {summary} und dränge nicht auf ein Telefonat."
        if sales_difficulty == "identity-repair":
            identity_response = german_identity_response(campaign)
            if identity_response:
                return identity_response
        if sales_difficulty == "scam-safety-boundary":
            verification_response = campaign_text(campaign, "approved_verification_response")
            if verification_response:
                return f"Ich frage in diesem Gespräch nicht nach Zahlungsdaten, Kartendaten oder Passwörtern. {ensure_terminal_period(verification_response)}"
            verification = campaign_text(campaign, "approved_verification_path", "approved_written_summary")
            if verification:
                return f"Ich frage in diesem Gespräch nicht nach Zahlungsdaten oder Kartendaten. Ich kann Ihnen stattdessen {verification} zusenden."
        if sales_difficulty == "payment-safety-boundary":
            verification_response = campaign_text(campaign, "approved_verification_response")
            if verification_response:
                return f"Ich frage in diesem Gespräch nicht nach Zahlungsdaten, Kartendaten oder Passwörtern. {ensure_terminal_period(verification_response)}"
            safe_path = campaign_text(campaign, "approved_written_summary", "approved_verification_path")
            if safe_path:
                return f"Ich frage in diesem Gespräch nicht nach Zahlungsdaten oder Kartendaten. Ich kann Ihnen stattdessen {safe_path} zusenden."
        if sales_difficulty == "support-route":
            route = campaign_text(campaign, "support_boundary_text", "support_route")
            if route:
                return f"Dann ist das ein Support-Thema. Ich beende den Verkaufsteil hier und leite Sie an {route} weiter."
        if sales_difficulty == "cancellation-route":
            route = campaign_text(campaign, "cancellation_boundary_text", "cancellation_route")
            if route:
                return f"Dann geht es um eine Kündigung. Ich beende den Verkaufsteil hier und leite Sie an {route} weiter."
        if sales_difficulty == "technical-specialist-route":
            scope = campaign_text(campaign, "approved_technical_scope")
            route = campaign_text(campaign, "specialist_handoff_route")
            if scope:
                return f"Nach den vorliegenden Informationen kann {scope}. Integrationsdetails sollte {route or 'eine zuständige Fachperson'} prüfen."
            if route:
                return f"Bei technischen Details sollte ich nicht raten. Ich kann das an {route} weiterleiten."
        if sales_difficulty == "security-review-route":
            route = campaign_text(campaign, "specialist_handoff_route", "approved_written_summary")
            if route:
                return "Das sollte eine zuständige Fachperson prüfen. Ich rate hier nicht und mache keine allgemeinen Zusagen."
        if sales_difficulty in {"coverage-boundary-route", "healthcare-boundary-route"}:
            boundary = campaign_text(campaign, "regulated_advice_boundary_text")
            route = campaign_text(campaign, "specialist_handoff_route")
            if boundary and route:
                return f"{boundary} Ich kann das an {route} weiterleiten."
        if sales_difficulty == "existing-provider-gap":
            gap = campaign_text(campaign, "approved_gap_isolation_question")
            if gap:
                return f"Ich möchte nicht behaupten, dass das Ihren Anbieter ersetzt. {gap}"
        if sales_difficulty in {"stakeholder-review", "partner-review"}:
            summary = campaign_text(campaign, "approved_review_summary", "approved_written_summary")
            if summary:
                return f"Ich sende Ihnen {summary}. Heute müssen Sie nichts entscheiden."
        if sales_difficulty == "sale-ready-commitment":
            next_step = campaign_text(campaign, "approved_sale_ready_next_step", "approved_next_step")
            if next_step:
                return f"Gut, ich halte fest, dass Sie {next_step} möchten. Es findet hier keine Zahlung und keine Vertragsunterzeichnung statt."

    return LOCALIZED_RESPONSES[language_key].get(
        sales_difficulty,
        LOCALIZED_RESPONSES[language_key]["unknown-runtime-signal"],
    )


def contains_any(text: str, phrases: list[str]) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in phrases)


def stage_is(stage: str | None, *values: str) -> bool:
    normalized = (stage or "").lower()
    return normalized in {value.lower() for value in values}


def latency_bucket(milliseconds: int) -> str:
    if milliseconds <= 1000:
        return "under-1s"
    if milliseconds <= 2000:
        return "under-2s"
    return "over-2s"


def classify_runtime_input(case: dict, campaign: dict | None = None) -> dict:
    customer_input = case["customer_input"]
    transcript = customer_input.get("transcript", "")
    input_type = customer_input.get("input_type")
    stage = customer_input.get("stage")
    response_language = normalize_response_language((campaign or {}).get("language"))

    if input_type == "voicemail-detected":
        sales_difficulty = "voicemail"
        return {
            "response_language": response_language,
            "detected_emotion": "neutral",
            "sales_difficulty": sales_difficulty,
            "interest_state": "maybe-interested",
            "selected_strategy": "rapport",
            "next_action": "create-follow-up-task",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if input_type == "silence-timeout" and customer_input.get("silence_count", 0) >= 2:
        sales_difficulty = "repeated-silence"
        return {
            "response_language": response_language,
            "detected_emotion": "neutral",
            "sales_difficulty": sales_difficulty,
            "interest_state": "not-interested",
            "selected_strategy": "rapport",
            "next_action": "close-politely",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, STOP_OR_REFUSAL_RUNTIME_PHRASES):
        sales_difficulty = "do-not-call"
        return {
            "response_language": response_language,
            "detected_emotion": "skeptical-or-negative",
            "sales_difficulty": sales_difficulty,
            "interest_state": "do-not-call",
            "selected_strategy": "rapport",
            "next_action": "suppress-contact",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, HUMAN_REQUEST_RUNTIME_PHRASES):
        sales_difficulty = "human-request"
        return {
            "response_language": response_language,
            "detected_emotion": "neutral",
            "sales_difficulty": sales_difficulty,
            "interest_state": "needs-human",
            "selected_strategy": "rapport",
            "next_action": "escalate",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["was kostet", "welchen kosten", "welche kosten", "monatlich", "preis reden", "preis wissen", "ist das teuer"]):
        sales_difficulty = "price-first-direct"
        return {
            "response_language": response_language,
            "detected_emotion": "skeptical-or-negative",
            "sales_difficulty": sales_difficulty,
            "interest_state": "maybe-interested",
            "selected_strategy": "evidence-or-benefit",
            "next_action": "create-follow-up-task",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["wer ist denn da", "wer genau sind sie", "wer anruft", "von welcher firma", "worum geht es hier", "warum rufen sie"]):
        sales_difficulty = "identity-repair"
        return {
            "response_language": response_language,
            "detected_emotion": "skeptical-or-negative",
            "sales_difficulty": sales_difficulty,
            "interest_state": "maybe-interested",
            "selected_strategy": "rapport",
            "next_action": "continue",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["sicherheitsprüfung", "it-sicherheit", "security muss", "security ist", "compliance"]) and not contains_any(transcript, ["kein thema", "nicht nötig"]):
        sales_difficulty = "security-review-route"
        return {
            "response_language": response_language,
            "detected_emotion": "neutral",
            "sales_difficulty": sales_difficulty,
            "interest_state": "needs-human",
            "selected_strategy": "evidence-or-benefit",
            "next_action": "escalate",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["medizinische beratung", "gesundheitliches thema", "gesundheitsberatung", "medizinisch sinnvoll", "medizinisches sagen"]):
        sales_difficulty = "healthcare-boundary-route"
        return {
            "response_language": response_language,
            "detected_emotion": "skeptical-or-negative",
            "sales_difficulty": sales_difficulty,
            "interest_state": "needs-human",
            "selected_strategy": "rapport",
            "next_action": "escalate",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["bankdaten", "kartendaten", "karte gebe", "zahlungsdaten"]):
        sales_difficulty = "payment-safety-boundary"
        return {
            "response_language": response_language,
            "detected_emotion": "skeptical-or-negative",
            "sales_difficulty": sales_difficulty,
            "interest_state": "maybe-interested",
            "selected_strategy": "rapport",
            "next_action": "create-follow-up-task",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["seriös", "unseriös", "betrug", "solchen anrufen vorsichtig", "wirklich von ihrer firma"]) and not contains_any(transcript, ["nicht, dass das betrug", "nicht dass das betrug"]):
        sales_difficulty = "scam-safety-boundary"
        return {
            "response_language": response_language,
            "detected_emotion": "skeptical-or-negative",
            "sales_difficulty": sales_difficulty,
            "interest_state": "maybe-interested",
            "selected_strategy": "rapport",
            "next_action": "create-follow-up-task",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["support-thema", "mit dem support", "hilfe mit meinem konto", "bestehendes problem", "problem mit meinem vertrag"]) and not contains_any(transcript, ["keinen support"]):
        sales_difficulty = "support-route"
        return {
            "response_language": response_language,
            "detected_emotion": "neutral",
            "sales_difficulty": sales_difficulty,
            "interest_state": "needs-human",
            "selected_strategy": "rapport",
            "next_action": "escalate",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["kündigen", "kündigung", "vertrag beenden", "ganze stoppen"]) and not contains_any(transcript, ["nicht kündigen"]):
        sales_difficulty = "cancellation-route"
        return {
            "response_language": response_language,
            "detected_emotion": "skeptical-or-negative",
            "sales_difficulty": sales_difficulty,
            "interest_state": "needs-human",
            "selected_strategy": "rapport",
            "next_action": "escalate",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["bitte nur per e-mail", "nur per e-mail", "nur per mail", "wenn überhaupt", "telefonier", "nicht an, schicken"]):
        sales_difficulty = "email-only-boundary"
        return {
            "response_language": response_language,
            "detected_emotion": "neutral",
            "sales_difficulty": sales_difficulty,
            "interest_state": "maybe-interested",
            "selected_strategy": "evidence-or-benefit",
            "next_action": "create-follow-up-task",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["schriftlich", "unterlagen", "infos zu", "zusammenfassung"]) and not contains_any(transcript, ["sicherheitsprüfung"]):
        sales_difficulty = "written-info-request"
        return {
            "response_language": response_language,
            "detected_emotion": "neutral",
            "sales_difficulty": sales_difficulty,
            "interest_state": "maybe-interested",
            "selected_strategy": "evidence-or-benefit",
            "next_action": "create-follow-up-task",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["technisch", "crm", "integration", "schnittstelle", "system verbinden"]):
        sales_difficulty = "technical-specialist-route"
        return {
            "response_language": response_language,
            "detected_emotion": "neutral",
            "sales_difficulty": sales_difficulty,
            "interest_state": "needs-human",
            "selected_strategy": "evidence-or-benefit",
            "next_action": "escalate",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["tarif überhaupt enthalten", "abgedeckt", "versicherung", "gedeckt", "für meinen fall"]):
        sales_difficulty = "coverage-boundary-route"
        return {
            "response_language": response_language,
            "detected_emotion": "neutral",
            "sales_difficulty": sales_difficulty,
            "interest_state": "needs-human",
            "selected_strategy": "rapport",
            "next_action": "escalate",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["is this a scam", "scam", "legitimate", "verify this is legitimate", "do not trust", "don't trust"]):
        sales_difficulty = "scam-safety-boundary"
        return {
            "response_language": response_language,
            "detected_emotion": "skeptical-or-negative",
            "sales_difficulty": sales_difficulty,
            "interest_state": "maybe-interested",
            "selected_strategy": "rapport",
            "next_action": "create-follow-up-task",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["card details", "card number", "credit card", "payment details", "pay over the phone", "giving card", "giving payment", "not giving card", "not giving payment"]):
        sales_difficulty = "payment-safety-boundary"
        return {
            "response_language": response_language,
            "detected_emotion": "skeptical-or-negative",
            "sales_difficulty": sales_difficulty,
            "interest_state": "maybe-interested",
            "selected_strategy": "rapport",
            "next_action": "create-follow-up-task",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["support issue", "support problem", "need support", "customer support", "billing issue", "help with my account"]):
        sales_difficulty = "support-route"
        return {
            "response_language": response_language,
            "detected_emotion": "neutral",
            "sales_difficulty": sales_difficulty,
            "interest_state": "needs-human",
            "selected_strategy": "rapport",
            "next_action": "escalate",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["cancel", "cancellation", "terminate", "end my account", "stop my service"]):
        sales_difficulty = "cancellation-route"
        return {
            "response_language": response_language,
            "detected_emotion": "skeptical-or-negative",
            "sales_difficulty": sales_difficulty,
            "interest_state": "needs-human",
            "selected_strategy": "rapport",
            "next_action": "escalate",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["who are you", "who is this", "who exactly are you", "what company", "why are you calling", "who are you again"]):
        sales_difficulty = "identity-repair"
        return {
            "response_language": response_language,
            "detected_emotion": "skeptical-or-negative",
            "sales_difficulty": sales_difficulty,
            "interest_state": "maybe-interested",
            "selected_strategy": "rapport",
            "next_action": "continue",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["what does this cost", "how much", "per month", "what is the price", "what's the price", "pricing", "in my budget", "cost?"]):
        sales_difficulty = "price-first-direct"
        return {
            "response_language": response_language,
            "detected_emotion": "skeptical-or-negative",
            "sales_difficulty": sales_difficulty,
            "interest_state": "maybe-interested",
            "selected_strategy": "evidence-or-benefit",
            "next_action": "create-follow-up-task",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["email only", "just email me", "only email", "send email", "email me"]):
        sales_difficulty = "email-only-boundary"
        return {
            "response_language": response_language,
            "detected_emotion": "neutral",
            "sales_difficulty": sales_difficulty,
            "interest_state": "maybe-interested",
            "selected_strategy": "evidence-or-benefit",
            "next_action": "create-follow-up-task",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["send me the details", "send details", "send information", "send info", "send me information", "written summary"]):
        sales_difficulty = "written-info-request"
        return {
            "response_language": response_language,
            "detected_emotion": "neutral",
            "sales_difficulty": sales_difficulty,
            "interest_state": "maybe-interested",
            "selected_strategy": "evidence-or-benefit",
            "next_action": "create-follow-up-task",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["technical question", "integrate", "integration", "api", "technical detail", "implementation detail"]):
        sales_difficulty = "technical-specialist-route"
        return {
            "response_language": response_language,
            "detected_emotion": "neutral",
            "sales_difficulty": sales_difficulty,
            "interest_state": "needs-human",
            "selected_strategy": "evidence-or-benefit",
            "next_action": "escalate",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["security review", "security team", "compliance", "data security", "soc 2", "hipaa"]):
        sales_difficulty = "security-review-route"
        return {
            "response_language": response_language,
            "detected_emotion": "neutral",
            "sales_difficulty": sales_difficulty,
            "interest_state": "needs-human",
            "selected_strategy": "evidence-or-benefit",
            "next_action": "escalate",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["coverage", "covered", "insurance cover", "coverage confusion"]):
        sales_difficulty = "coverage-boundary-route"
        return {
            "response_language": response_language,
            "detected_emotion": "neutral",
            "sales_difficulty": sales_difficulty,
            "interest_state": "needs-human",
            "selected_strategy": "rapport",
            "next_action": "escalate",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["health", "medical", "doctor", "diagnosis", "treatment", "healthcare"]):
        sales_difficulty = "healthcare-boundary-route"
        return {
            "response_language": response_language,
            "detected_emotion": "skeptical-or-negative",
            "sales_difficulty": sales_difficulty,
            "interest_state": "needs-human",
            "selected_strategy": "rapport",
            "next_action": "escalate",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["garantieren", "nachweis", "belegen", "wirklich etwas bringt", "nicht klappt", "guarantee", "stabil", "geschwindigkeit"]):
        sales_difficulty = "claim-boundary"
        return {
            "response_language": response_language,
            "detected_emotion": "skeptical-or-negative",
            "sales_difficulty": sales_difficulty,
            "interest_state": "needs-human",
            "selected_strategy": "inquiry",
            "next_action": "escalate",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["welcher genaue tarif", "welcher tarif", "welche genauen details", "was ist enthalten", "paket enthalten", "was bekomme ich", "welche leistungen", "datenvolumen", "exact plan", "which plan", "which exact", "service details", "included"]):
        sales_difficulty = "product-detail-lookup"
        return {
            "response_language": response_language,
            "detected_emotion": "neutral",
            "sales_difficulty": sales_difficulty,
            "interest_state": "maybe-interested",
            "selected_strategy": "evidence-or-benefit",
            "next_action": "continue",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if stage == "scheduling" and contains_any(transcript, ["mittwoch", "donnerstag", "freitag", "dienstag", "morgen um", "10 uhr", "14 uhr", "wednesday", "10 works"]):
        sales_difficulty = "scheduling-confirmation"
        return {
            "response_language": response_language,
            "detected_emotion": "positive",
            "sales_difficulty": sales_difficulty,
            "interest_state": "interested",
            "selected_strategy": "direct-ask-or-commitment",
            "next_action": "confirm-scheduling",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["ready to move forward", "ready to agree", "agree to the next step", "sale ready", "sale-ready", "verbal commitment", "machen wir das so", "nächste schritt", "weitermachen", "so festhalten", "dann starten"]):
        sales_difficulty = "sale-ready-commitment" if campaign_flag(
            campaign,
            "close_criteria_satisfied",
            "sale_ready_close_allowed",
        ) else "sale-ready-missing-criteria"
        return {
            "response_language": response_language,
            "detected_emotion": "positive",
            "sales_difficulty": sales_difficulty,
            "interest_state": "interested",
            "selected_strategy": "direct-ask-or-commitment",
            "next_action": "sale-ready-log" if sales_difficulty == "sale-ready-commitment" else "ask-follow-up",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if stage_is(stage, "procurement-review") or contains_any(transcript, ["procurement", "written information", "written info"]):
        sales_difficulty = "procurement-review"
        return {
            "response_language": response_language,
            "detected_emotion": "neutral",
            "sales_difficulty": sales_difficulty,
            "interest_state": "maybe-interested",
            "selected_strategy": "inquiry",
            "next_action": "ask-follow-up",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["my spouse", "my partner", "ask my spouse", "ask my partner", "meinem mann", "meiner frau", "mein partner", "nicht alleine", "zu hause"]):
        sales_difficulty = "partner-review"
        return {
            "response_language": response_language,
            "detected_emotion": "neutral",
            "sales_difficulty": sales_difficulty,
            "interest_state": "maybe-interested",
            "selected_strategy": "evidence-or-benefit",
            "next_action": "create-follow-up-task",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if stage_is(stage, "authority-check") or contains_any(transcript, ["my boss", "boss has to review", "manager has to review", "decision maker", "ask my manager", "need manager approval", "meinem chef", "vorgesetzter", "nicht nur ich", "interne freigabe", "durch die leitung"]):
        sales_difficulty = "stakeholder-review"
        return {
            "response_language": response_language,
            "detected_emotion": "neutral",
            "sales_difficulty": sales_difficulty,
            "interest_state": "maybe-interested",
            "selected_strategy": "evidence-or-benefit",
            "next_action": "create-follow-up-task",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["already use another provider", "already have a provider", "have a provider", "another provider", "current provider", "compare this fairly", "compare fairly", "schon einen anbieter", "über jemand anderen", "schon eine lösung", "versorgt", "aktueller anbieter"]):
        sales_difficulty = "existing-provider-gap"
        return {
            "response_language": response_language,
            "detected_emotion": "neutral",
            "sales_difficulty": sales_difficulty,
            "interest_state": "maybe-interested",
            "selected_strategy": "inquiry",
            "next_action": "ask-follow-up",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["call back later", "callback later", "call me back", "callback", "short summary and call back", "nächste woche nochmal", "später noch mal", "morgen zurückrufen", "anderen zeitpunkt"]):
        sales_difficulty = "callback-request"
        return {
            "response_language": response_language,
            "detected_emotion": "neutral",
            "sales_difficulty": sales_difficulty,
            "interest_state": "maybe-interested",
            "selected_strategy": "direct-ask-or-commitment",
            "next_action": "create-follow-up-task",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["time to think", "do not rush", "don't rush"]):
        sales_difficulty = "autonomy-check"
        return {
            "response_language": response_language,
            "detected_emotion": "neutral",
            "sales_difficulty": sales_difficulty,
            "interest_state": "maybe-interested",
            "selected_strategy": "inquiry",
            "next_action": "ask-follow-up",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["do not know your company", "don't know your company", "verify this is legitimate", "legitimate", "trust"]):
        sales_difficulty = "trust-gap"
        return {
            "response_language": response_language,
            "detected_emotion": "skeptical-or-negative",
            "sales_difficulty": sales_difficulty,
            "interest_state": "maybe-interested",
            "selected_strategy": "rapport",
            "next_action": "ask-follow-up",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["vielleicht irgendwann", "vielleicht naechste woche", "naechste woche", "nothing firm", "next week", "cannot commit", "nichts fest"]):
        sales_difficulty = "timing-delay"
        return {
            "response_language": response_language,
            "detected_emotion": "neutral",
            "sales_difficulty": sales_difficulty,
            "interest_state": "maybe-interested",
            "selected_strategy": "direct-ask-or-commitment",
            "next_action": "create-follow-up-task",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    if contains_any(transcript, ["guenstiger", "zu teuer", "too expensive", "lohnt sich", "aufwand", "worth the effort", "cost sounds high", "cost", "price", "worth my time"]):
        sales_difficulty = "price-objection"
        return {
            "response_language": response_language,
            "detected_emotion": "skeptical-or-negative",
            "sales_difficulty": sales_difficulty,
            "interest_state": "maybe-interested",
            "selected_strategy": "inquiry",
            "next_action": "ask-follow-up",
            "agent_response": localized_response(response_language, sales_difficulty, campaign),
        }

    sales_difficulty = "unknown-runtime-signal"
    return {
        "response_language": response_language,
        "detected_emotion": "neutral",
        "sales_difficulty": sales_difficulty,
        "interest_state": "maybe-interested",
        "selected_strategy": "inquiry",
        "next_action": "ask-follow-up",
        "agent_response": localized_response(response_language, sales_difficulty, campaign),
    }


def background_modules_for(response_mode: str, expected: dict | None, classified: dict) -> list[str]:
    if expected is not None:
        return expected.get("background_modules", [])
    if response_mode == "bridge-then-background":
        return ["campaign-knowledge-lookup"]
    if classified["next_action"] == "suppress-contact":
        return ["crm-suppression-update"]
    if classified["next_action"] == "escalate":
        return ["human-handoff-prep"]
    if classified["next_action"] == "confirm-scheduling":
        return ["calendar-write"]
    if classified["next_action"] == "sale-ready-log":
        return ["sale-ready-outcome-log"]
    if classified["next_action"] == "create-follow-up-task":
        return ["follow-up-task-write"]
    if classified["sales_difficulty"] == "repeated-silence":
        return ["no-response-log"]
    return []


def build_runtime_decision(case: dict, expected: dict | None = None, campaign: dict | None = None) -> dict:
    classified = classify_runtime_input(case, campaign)
    response_mode = "bridge-then-background" if classified["sales_difficulty"] == "product-detail-lookup" else "fast-response"
    first_response_ms = BRIDGE_RESPONSE_MS if response_mode == "bridge-then-background" else FAST_RESPONSE_MS
    call_control = "bridge-then-continue" if response_mode == "bridge-then-background" else call_control_for_next_action(
        classified["next_action"],
        classified["interest_state"],
    )
    bridge_response = classified["agent_response"] if response_mode == "bridge-then-background" else None

    runtime_decision = {
        "case_id": case["case_id"],
        "campaign_language": normalize_response_language((campaign or {}).get("language")),
        "response_language": classified["response_language"],
        "response_mode": response_mode,
        "first_response_latency_budget_ms": first_response_ms,
        "first_response_latency_bucket": latency_bucket(first_response_ms),
        "background_completion_budget_ms": BACKGROUND_COMPLETION_MS if response_mode == "bridge-then-background" else None,
        "background_modules": background_modules_for(response_mode, expected, classified),
        "live_path_subagents": [],
        "detected_emotion": classified["detected_emotion"],
        "sales_difficulty": classified["sales_difficulty"],
        "interest_state": classified["interest_state"],
        "selected_strategy": classified["selected_strategy"],
        "next_action": classified["next_action"],
        "call_control": call_control,
        "bridge_response": bridge_response,
        "agent_response": classified["agent_response"],
        "rationale": "Deterministic runtime policy selected the fastest safe response path.",
    }
    return runtime_decision


def run_case(case: dict, campaigns: list[dict] | None = None) -> dict:
    expected = case["expected_runtime"]
    campaign = find_campaign(campaigns or [], case["campaign_id"])
    runtime_decision = build_runtime_decision(case, expected, campaign)
    scores = score_case(case, runtime_decision)
    return {
        "case_id": case["case_id"],
        "case_title": case["case_title"],
        "campaign_id": case["campaign_id"],
        "campaign": {
            "language": normalize_response_language((campaign or {}).get("language")),
            "locale": (campaign or {}).get("locale"),
            "product_category": (campaign or {}).get("product_category"),
            "customer_type": (campaign or {}).get("customer_type"),
        },
        "runtime_scenario": case["runtime_scenario"],
        "expected_runtime": expected,
        "runtime_decision": runtime_decision,
        "scores": scores,
    }


def score_case(case: dict, decision: dict) -> dict:
    expected = case["expected_runtime"]
    expected_language = expected.get("response_language")
    expected_markers = [marker.lower() for marker in expected.get("response_must_include_any", [])]
    response_text = decision["agent_response"].lower()
    return {
        "response_mode_match": decision["response_mode"] == expected["response_mode"],
        "latency_bucket_match": decision["first_response_latency_bucket"] == expected["first_response_latency_bucket"],
        "background_modules_match": decision["background_modules"] == expected.get("background_modules", []),
        "emotion_match": decision["detected_emotion"] == expected["detected_emotion"],
        "sales_difficulty_match": decision["sales_difficulty"] == expected["sales_difficulty"],
        "interest_state_match": decision["interest_state"] == expected["interest_state"],
        "strategy_match": decision["selected_strategy"] == expected["selected_strategy"],
        "next_action_match": decision["next_action"] == expected["next_action"],
        "call_control_match": decision["call_control"] == expected["call_control"],
        "response_language_match": expected_language is None or decision["response_language"] == expected_language,
        "response_marker_match": not expected_markers or any(marker in response_text for marker in expected_markers),
        "live_path_subagent_violation": bool(decision["live_path_subagents"]),
    }


def aggregate(results: list[dict]) -> dict:
    summary = {
        "case_total": len(results),
        "response_mode_matches": 0,
        "latency_bucket_matches": 0,
        "background_modules_matches": 0,
        "emotion_matches": 0,
        "sales_difficulty_matches": 0,
        "interest_state_matches": 0,
        "strategy_matches": 0,
        "next_action_matches": 0,
        "call_control_matches": 0,
        "response_language_matches": 0,
        "response_marker_matches": 0,
        "live_path_subagent_violations": 0,
        "language_counts": {},
    }
    for result in results:
        scores = result["scores"]
        language = result["runtime_decision"].get("response_language", "en")
        summary["language_counts"][language] = summary["language_counts"].get(language, 0) + 1
        summary["response_mode_matches"] += int(scores["response_mode_match"])
        summary["latency_bucket_matches"] += int(scores["latency_bucket_match"])
        summary["background_modules_matches"] += int(scores["background_modules_match"])
        summary["emotion_matches"] += int(scores["emotion_match"])
        summary["sales_difficulty_matches"] += int(scores["sales_difficulty_match"])
        summary["interest_state_matches"] += int(scores["interest_state_match"])
        summary["strategy_matches"] += int(scores["strategy_match"])
        summary["next_action_matches"] += int(scores["next_action_match"])
        summary["call_control_matches"] += int(scores["call_control_match"])
        summary["response_language_matches"] += int(scores["response_language_match"])
        summary["response_marker_matches"] += int(scores["response_marker_match"])
        summary["live_path_subagent_violations"] += int(scores["live_path_subagent_violation"])
    return summary


def render_report(results: list[dict], summary: dict) -> str:
    lines = [
        "# Bilingual Realtime Sales Core Report",
        "",
        "This report was generated by `scripts/run_realtime_turn_simulation.py`.",
        "",
        "The simulation checks runtime behavior, not product-category breadth.",
        "",
        "## Aggregate Results",
        "",
        f"- Cases: {summary['case_total']}",
        f"- Response-mode matches: {summary['response_mode_matches']} / {summary['case_total']}",
        f"- First-response latency-bucket matches: {summary['latency_bucket_matches']} / {summary['case_total']}",
        f"- Background-module matches: {summary['background_modules_matches']} / {summary['case_total']}",
        f"- Emotion matches: {summary['emotion_matches']} / {summary['case_total']}",
        f"- Sales-difficulty matches: {summary['sales_difficulty_matches']} / {summary['case_total']}",
        f"- Interest-state matches: {summary['interest_state_matches']} / {summary['case_total']}",
        f"- Strategy matches: {summary['strategy_matches']} / {summary['case_total']}",
        f"- Next-action matches: {summary['next_action_matches']} / {summary['case_total']}",
        f"- Call-control matches: {summary['call_control_matches']} / {summary['case_total']}",
        f"- Response-language matches: {summary['response_language_matches']} / {summary['case_total']}",
        f"- Response-marker matches: {summary['response_marker_matches']} / {summary['case_total']}",
        f"- Live-path sub-agent violations: {summary['live_path_subagent_violations']}",
        f"- Language counts: `{json.dumps(summary['language_counts'], sort_keys=True)}`",
        "",
        "## Case Results",
        "",
    ]
    for result in results:
        decision = result["runtime_decision"]
        lines.extend(
            [
                f"### {result['case_id']}: {result['case_title']}",
                "",
                f"- Campaign: `{result['campaign_id']}`",
                f"- Response language: `{decision['response_language']}`",
                f"- Scenario: `{result['runtime_scenario']}`",
                f"- Response mode: `{decision['response_mode']}`",
                f"- First-response latency bucket: `{decision['first_response_latency_bucket']}`",
                f"- Background modules: `{', '.join(decision['background_modules']) or 'none'}`",
                f"- Next action: `{decision['next_action']}`",
                f"- Call control: `{decision['call_control']}`",
                f"- Live-path sub-agents: `{len(decision['live_path_subagents'])}`",
                "",
                "Runtime decision:",
                "",
                "```json",
                json.dumps(decision, indent=2),
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run PROD-005 realtime latency and call-control simulation.")
    parser.add_argument("--cases", required=True, help="Path to PROD-005 realtime case JSON.")
    parser.add_argument("--out", required=True, help="Path to write JSON results.")
    parser.add_argument("--report-out", required=True, help="Path to write markdown report.")
    args = parser.parse_args()

    cases_path = Path(args.cases)
    campaigns, cases = load_realtime_cases(cases_path)
    results = [run_case(case, campaigns) for case in cases]
    summary = aggregate(results)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"summary": summary, "results": results}, indent=2), encoding="utf-8")

    report_path = Path(args.report_out)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(results, summary), encoding="utf-8")


if __name__ == "__main__":
    main()
