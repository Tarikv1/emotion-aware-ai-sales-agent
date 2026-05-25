from __future__ import annotations

import hashlib
import re

from runtime.campaigns import public_openai_chatgpt_plans_dialogue as public_openai_dialogue
from runtime.speech.asr_quality_gate import asr_fragment_response, looks_like_asr_fragment, normalize_transcript

AGENT_OPEN_TRANSCRIPT = "__agent_open__"
CALLBACK_WORKFLOW_GAP = "callback_workflow_gap"
CALLBACK_SCHEDULING_REQUEST = "callback_scheduling_request"
CALLBACK_TIME_CONFIRMATION = "callback_time_confirmation"
ROUTESIGNAL_CAMPAIGN_IDS = {"live-demo-001-routesignal", "campaign-prod-005-b2b-software"}


def normalize_text(text: str) -> str:
    return normalize_transcript(text)


def normalized_contains_any(normalized: str, phrases: set[str]) -> bool:
    return any(normalize_text(phrase) in normalized for phrase in phrases)


def live_demo_price_answer(language: str) -> str:
    if language.startswith("de"):
        return "Der Demo-Preis liegt bei 29 Dollar pro Monat oder 59 Dollar pro Monat, je nach Umfang."
    return "Starter is $29/month for basic routing. Growth is $59/month with priority routing, reminders, and handoff review. Which gap costs more time today: routing, callbacks, or handoffs?"


def is_direct_price_question(normalized: str) -> bool:
    if not normalized:
        return False
    if normalized_contains_any(
        normalized,
        {
            "price later",
            "talk about the price later",
            "talk about price later",
        },
    ):
        return False
    return normalized_contains_any(
        normalized,
        {
            "what is the price",
            "what s the price",
            "how much",
            "pricing",
            "monthly price",
            "what does it cost",
            "what does this cost",
            "what does routesignal cost",
            "cost per month",
            "price per month",
        },
    )


def is_starter_growth_plan_boundary_question(normalized: str) -> bool:
    if not normalized or "starter" not in normalized:
        return False
    mentions_growth_only_feature = normalized_contains_any(
        normalized,
        {
            "reminder",
            "reminders",
            "follow up reminder",
            "follow-up reminder",
            "handoff review",
            "handoff",
            "priority routing",
            "slack alert",
            "slack alerts",
            "duplicate check",
            "duplicate checks",
        },
    )
    asks_boundary = normalized_contains_any(
        normalized,
        {
            "does not cover",
            "doesnt cover",
            "doesn t cover",
            "do not cover",
            "dont cover",
            "not cover",
            "not include",
            "does not include",
            "doesnt include",
            "doesn t include",
            "is not included",
            "isn t included",
            "isnt included",
            "only growth",
            "growth only",
            "in growth",
            "included in starter",
            "starter include",
            "starter cover",
        },
    )
    return mentions_growth_only_feature and asks_boundary


def answered_topic_in_turns(turns: list[dict], topic: str) -> bool:
    for turn in turns:
        memory = turn.get("conversation_memory") or {}
        continuity = turn.get("continuity") or {}
        if isinstance(memory, dict) and topic in set(memory.get("answered_topics") or []):
            return True
        if str(continuity.get("reason") or "") == topic:
            return True
    return False


def starter_growth_plan_boundary_response(language: str, turns: list[dict] | None = None) -> str:
    if language.startswith("de"):
        return "Nein. Starter deckt Basis-Routing ab; Erinnerungen und Uebergabepruefung gehoeren zu Growth."
    turns = list(turns or [])
    if answered_topic_in_turns(turns, "plan_boundary"):
        return (
            "Same plan boundary: Starter handles lead capture, basic routing, callback tasks, reports, and CSV import. "
            "Growth is where reminders, priority routing, and handoff review live. Is that Growth workflow the part worth checking?"
        )
    return (
        "No. Starter covers lead capture, basic routing, callback tasks, reports, and CSV import. "
        "Reminders and handoff review are Growth features. Are those the parts you actually need?"
    )


def is_live_demo_price_answer(response: str) -> bool:
    return "$29/month" in response and "$59/month" in response


def is_opening_greeting(normalized: str) -> bool:
    return normalized in {
        "hi",
        "hello",
        "hey",
        "what s up",
        "whats up",
        "hey what s up",
        "hey whats up",
        "hey how s it going",
        "hey how is it going",
        "how s it going",
        "hows it going",
        "hi how are you",
        "hi how are you doing",
        "how are you",
        "how are you doing",
    }


def is_agent_open_turn(normalized: str) -> bool:
    return normalized == normalize_text(AGENT_OPEN_TRANSCRIPT)


def campaign_value(campaign: dict | None, key: str, fallback: str) -> str:
    value = str((campaign or {}).get(key) or "").strip()
    return value or fallback


def customer_campaign_value(campaign: dict | None, customer_key: str, legacy_key: str, fallback: str) -> str:
    return campaign_value(campaign, customer_key, campaign_value(campaign, legacy_key, fallback))


def nested_campaign_value(campaign: dict | None, section: str, key: str, fallback: str) -> str:
    data = (campaign or {}).get(section) or {}
    value = str(data.get(key) or "").strip() if isinstance(data, dict) else ""
    return value or fallback


def is_generic_campaign_config(campaign: dict | None) -> bool:
    if not isinstance(campaign, dict):
        return False
    campaign_id = str(campaign.get("campaign_id") or "")
    if campaign_id in ROUTESIGNAL_CAMPAIGN_IDS:
        return False
    return bool(campaign.get("vertical_id") and isinstance(campaign.get("diagnostic_gaps"), dict) and campaign.get("diagnostic_gaps"))


def generic_campaign_gap_clause(campaign: dict | None) -> str:
    if not is_generic_campaign_config(campaign):
        return "the relevant fit areas"
    gaps = campaign.get("core_diagnostic_gaps") or list((campaign.get("diagnostic_gaps") or {}).keys())
    labels: list[str] = []
    for gap_id in gaps:
        definition = (campaign.get("diagnostic_gaps") or {}).get(gap_id) or {}
        label = str(definition.get("label") or gap_id).replace("_", " ").strip()
        if label:
            labels.append(label)
    if not labels:
        return "the relevant fit areas"
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f"{labels[0]} or {labels[1]}"
    return f"{', '.join(labels[:-1])}, or {labels[-1]}"


def generic_campaign_role_phrase(role: str) -> str:
    role = str(role or "").strip()
    if not role:
        return "a qualified specialist"
    lowered = role.lower()
    if lowered.startswith(("a ", "an ", "the ", "someone ", "somebody ", "your ")):
        return role
    article = "an" if lowered[:1] in {"a", "e", "i", "o", "u"} else "a"
    return f"{article} {role}"


def sentence_start(text: str) -> str:
    text = str(text or "").strip()
    return text[:1].upper() + text[1:] if text else text


def generic_campaign_context(campaign: dict | None) -> dict[str, str]:
    owner = campaign_value(campaign, "human_followup_owner", "qualified specialist")
    owner_phrase = generic_campaign_role_phrase(owner)
    offer = customer_campaign_value(campaign, "customer_facing_offer_name", "product_or_offer_name", campaign_value(campaign, "product_name", "this review"))
    return {
        "client": customer_campaign_value(campaign, "customer_facing_company_name", "client_name", "the campaign team"),
        "offer": offer,
        "owner": owner,
        "owner_phrase": owner_phrase,
        "owner_sentence": sentence_start(owner_phrase),
        "target": campaign_value(campaign, "appointment_target", "human review"),
        "gaps": generic_campaign_gap_clause(campaign),
        "summary": customer_campaign_value(campaign, "customer_facing_offer_summary", "product_or_offer_summary", f"a high-level {offer}"),
        "scope": customer_campaign_value(campaign, "customer_facing_human_review_scope", "human_review_scope", generic_campaign_gap_clause(campaign)),
    }


def generic_campaign_spoken_area_phrase(campaign: dict | None) -> str:
    context = generic_campaign_context(campaign)
    scope = context["scope"]
    for marker in (" against ", " before ", " without "):
        if marker in scope:
            scope = scope.split(marker, 1)[0]
    parts = [part.strip(" .") for part in re.split(r",|\band\b", scope) if part.strip(" .")]
    if len(parts) >= 3:
        return f"{parts[0]}, {parts[1]}, or {parts[2]}"
    if len(parts) == 2:
        return f"{parts[0]} or {parts[1]}"
    return parts[0] if parts else _generic_primary_issue_phrase(campaign)


def _question_sentence(question: str) -> str:
    cleaned = " ".join(str(question or "").split()).strip()
    if not cleaned:
        return ""
    if cleaned[-1] not in ".?!":
        cleaned = f"{cleaned}?"
    return cleaned


def _generic_primary_issue_phrase(campaign: dict | None) -> str:
    phrase = campaign_value(campaign, "primary_customer_issue_phrase", campaign_value(campaign, "primary_issue_phrase", ""))
    if phrase:
        return phrase
    if is_generic_campaign_config(campaign):
        gap_ids = campaign.get("core_diagnostic_gaps") or list((campaign.get("diagnostic_gaps") or {}).keys())
        if gap_ids:
            definition = (campaign.get("diagnostic_gaps") or {}).get(gap_ids[0]) or {}
            return str(definition.get("customer_facing_phrase") or definition.get("label") or gap_ids[0]).replace("_", " ").strip()
    return "the relevant issue"


def generic_campaign_primary_question(language: str, campaign: dict | None) -> str:
    configured = campaign_value(campaign, "short_relevance_question", "")
    if configured:
        return _question_sentence(configured)
    issue = _generic_primary_issue_phrase(campaign)
    if language.startswith("de"):
        return f"Ist {issue} gerade relevant?"
    return f"Is {issue} causing any issue right now?"


def generic_campaign_review_question(language: str, campaign: dict | None) -> str:
    context = generic_campaign_context(campaign)
    if language.startswith("de"):
        return f"Kurze Pruefung fuer {context['target']}: {generic_campaign_primary_question(language, campaign)}"
    return f"Quick check for a short {context['target']}: {generic_campaign_primary_question(language, campaign)}"


def generic_campaign_next_step_text(language: str, campaign: dict | None) -> str:
    context = generic_campaign_context(campaign)
    if language.startswith("de"):
        return f"Der naechste Schritt ist nur eine sichere Pruefung mit {context['owner']}. {generic_campaign_primary_question(language, campaign)}"
    return f"If it is relevant, {context['owner_phrase']} can do a short {context['target']}. {generic_campaign_primary_question(language, campaign)}"


def is_human_review_scope_question(normalized: str) -> bool:
    if not normalized:
        return False
    return normalized_contains_any(
        normalized,
        {
            "what will the specialist check",
            "what would the specialist check",
            "what does the specialist check",
            "what will the reviewer check",
            "what would the reviewer check",
            "what will the human review",
            "what would the human review",
            "what will they check",
            "why can't the ai answer that",
            "why can t the ai answer that",
            "why cant the ai answer that",
        },
    )


def human_review_scope_response(language: str, campaign: dict | None) -> str:
    if is_generic_campaign_config(campaign):
        context = generic_campaign_context(campaign)
        scope = generic_campaign_spoken_area_phrase(campaign)
        if language.startswith("de"):
            return f"{context['owner']} prueft {scope} und die konkreten Details. Ich kann nur klaeren, ob diese Pruefung sinnvoll ist."
        return (
            f"I can keep this high-level. {context['owner_sentence']} would review {scope} "
            "and the actual details before any recommendation."
        )
    if language.startswith("de"):
        return "Die Workflow-Pruefung schaut darauf, wem der Lead gehoert, wann nachgefasst wird und wo Erinnerungen oder Uebergaben rutschen."
    return (
        "The workflow reviewer would check who owns the lead, when follow-up happens, "
        "and where reminders or handoffs slip. I can only check whether that review is worth a callback."
    )


def generic_campaign_product_detail_text(language: str, campaign: dict | None) -> str:
    context = generic_campaign_context(campaign)
    scope = generic_campaign_spoken_area_phrase(campaign)
    if language.startswith("de"):
        return (
            f"{context['summary']} Ich kann den Rahmen nur allgemein erklaeren; "
            f"{context['owner']} prueft die Details."
        )
    return (
        f"It is a quick {context['offer']}. I can explain the high-level scope; "
        f"{context['owner_sentence']} would review {scope} and the actual details."
    )


def is_generic_product_detail_limitation_ack(normalized: str) -> bool:
    if not normalized:
        return False
    return normalized_contains_any(
        normalized,
        {
            "cannot give me any details",
            "can you not give me any details",
            "can t give me any details",
            "cant give me any details",
            "cannot give me details",
            "can t give me details",
            "cant give me details",
            "cannot give detailed",
            "can t give detailed",
            "cant give detailed",
            "cannot give me any information",
            "can t give me any information",
            "cant give me any information",
            "cannot give me information",
            "can t give me information",
            "cant give me information",
            "only a licensed",
            "only a license",
            "only licensed",
            "only license",
        },
    )


def generic_campaign_product_detail_limitation_text(language: str, campaign: dict | None, *, repeated: bool = False) -> str:
    context = generic_campaign_context(campaign)
    if language.startswith("de"):
        return (
            f"Ja, genau. Ich kann den Zweck des Anrufs erklaeren, aber keine detaillierte Beratung geben. "
            f"{context['owner_sentence']} uebernimmt die {context['target']}. Ich kann eine Zeit notieren oder hier stoppen."
        )
    owner = context["owner_phrase"]
    if "insurance" in str((campaign or {}).get("vertical_id") or ""):
        owner = "a licensed insurance specialist"
    if repeated:
        return (
            "Yes, that is right. I can explain the purpose of the call, but not detailed advice. "
            f"{session_role_sentence(owner)} would review the actual details. I can note a time, or stop here."
        )
    return (
        "Correct, I cannot give detailed policy or product advice on this call. "
        f"I can only check whether this should go to {context['owner_phrase']}. "
        "I can note a time, or stop here."
    )


def session_role_sentence(role: str) -> str:
    return sentence_start(generic_campaign_role_phrase(role))


def generic_campaign_price_text(language: str, campaign: dict | None) -> str:
    context = generic_campaign_context(campaign)
    if language.startswith("de"):
        return (
            f"Ich habe keinen freigegebenen Preis, den ich hier zitieren sollte. "
            f"{context['owner']} sollte Kosten und Bedingungen bestaetigen; zuerst geht es darum, ob {context['gaps']} relevant sind."
        )
    return (
        f"I do not have approved pricing to quote here. "
        f"{context['owner_sentence']} should confirm cost and terms before any next step."
    )


def generic_campaign_claim_boundary_text(language: str, campaign: dict | None) -> str:
    context = generic_campaign_context(campaign)
    if language.startswith("de"):
        return (
            f"Das kann ich hier nicht verifizieren oder als Compliance-Aussage bestaetigen. "
            f"{context['owner']} braucht verifizierte Details. Soll ich es bei {context['gaps']} belassen?"
        )
    return (
        f"I cannot verify that or make a compliance claim here. {context['owner_sentence']} needs verified details first. "
        f"Should I keep this to {context['gaps']}?"
    )


def generic_campaign_focus_text(
    language: str,
    focus: str,
    campaign: dict | None,
    *,
    normalized: str = "",
    persisted: bool = False,
) -> str | None:
    if not is_generic_campaign_config(campaign):
        return None
    if focus == "price":
        return generic_campaign_price_text(language, campaign)
    if focus in {"details", "product", "security"}:
        if normalized_contains_any(normalized, {"guarantee", "guaranteed", "promise", "promised", "compliance", "compliant"}):
            return generic_campaign_claim_boundary_text(language, campaign)
        if is_generic_product_detail_limitation_ack(normalized):
            return generic_campaign_product_detail_limitation_text(language, campaign, repeated=True)
        return generic_campaign_product_detail_text(language, campaign)
    if focus in {"fit", "qualification", "provider_gap"}:
        return generic_campaign_review_question(language, campaign)
    if focus == "effort":
        if language.startswith("de"):
            return f"Der Aufwand lohnt nur, wenn es gerade relevant ist. {generic_campaign_primary_question(language, campaign)}"
        return f"This is only worth time if the primary issue is active. {generic_campaign_primary_question(language, campaign)}"
    if focus == "timing":
        if language.startswith("de"):
            return "Kein Problem. Ohne konkrete Zeit bestaetige ich nichts; wir koennen es bei einer spaeteren menschlichen Pruefung belassen."
        return "No problem. I will not schedule anything without a specific time; we can leave this for a later human review."
    if focus == "terms":
        context = generic_campaign_context(campaign)
        if language.startswith("de"):
            return f"Bedingungen sollten von {context['owner']} bestaetigt werden, bevor ich dazu etwas verspreche."
        return f"Terms should be confirmed by {context['owner_phrase']} before I promise anything about them."
    return generic_campaign_review_question(language, campaign)


def sales_opening_response(language: str, campaign: dict | None = None) -> str:
    if is_generic_campaign_config(campaign):
        opening_options = (campaign or {}).get("opening_options")
        if isinstance(opening_options, dict):
            configured_opening = str(opening_options.get("preferred") or "").strip()
            if configured_opening:
                return configured_opening
        context = generic_campaign_context(campaign)
        client_name = context["client"]
        offer_name = context["offer"]
        representative = nested_campaign_value(campaign, "caller_identity", "representative_name", "Maya")
        areas = generic_campaign_spoken_area_phrase(campaign)
        if language.startswith("de"):
            return (
                f"Hallo, hier ist {representative} von {client_name} wegen {offer_name}. "
                f"Ich pruefe kurz {areas}; haben Sie kurz Zeit?"
            )
        return (
            f"Hi, this is {representative} from {client_name}. "
            f"I'm doing a quick {offer_name} - mainly {areas}. "
            "Do you have a minute?"
        )
    client_name = campaign_value(campaign, "client_name", "Northstar Workflow Labs")
    product_name = campaign_value(campaign, "product_name", "RouteSignal CRM")
    representative = nested_campaign_value(campaign, "caller_identity", "representative_name", "Maya")
    product_relationship = nested_campaign_value(
        campaign,
        "caller_identity",
        "product_relationship",
        f"the team behind {product_name}",
    )
    buyer_role = nested_campaign_value(
        campaign,
        "target_account_context",
        "buyer_role",
        "the person handling inbound demo follow-up",
    )
    if language.startswith("de"):
        return (
            f"Hallo, hier ist {representative} von {client_name}, dem Team hinter {product_name}. "
            "Wir helfen bei verpassten Rueckrufen und Uebergaben nach Demo-Anfragen. "
            "Haben Sie kurz Zeit?"
        )
    return (
        f"Hi, this is {representative} calling from {client_name}, {product_relationship}. "
        f"I am looking for {buyer_role}. We help stop missed callbacks and messy handoffs. "
        "Do you have a minute?"
    )


def opening_greeting_response(language: str, campaign: dict | None = None) -> str:
    return sales_opening_response(language, campaign)


def has_caller_identity_question(normalized: str) -> bool:
    if not normalized:
        return False
    return normalized_contains_any(
        normalized,
        {
            "where are you calling from",
            "where were you calling from",
            "where did you call from",
            "where are you from",
            "calling from again",
            "who are you",
            "who is calling",
            "who s calling",
            "what company",
            "which company",
            "company are you",
            "company you are from",
            "company are you calling from",
            "who do you work for",
        },
    )


def caller_identity_recall_response(language: str, campaign: dict | None = None) -> str:
    if is_generic_campaign_config(campaign):
        context = generic_campaign_context(campaign)
        client_name = context["client"]
        offer_name = context["offer"]
        representative = nested_campaign_value(campaign, "caller_identity", "representative_name", "Maya")
        owner = context["owner"]
        if language.startswith("de"):
            return (
                f"Ich bin {representative} von {client_name}. Es geht um {offer_name} "
                f"und darum, ob eine kurze Pruefung mit {owner} sinnvoll waere."
            )
        return (
            f"I am {representative} calling from {client_name} about {offer_name}. "
            f"The reason is to see whether this is worth review by {owner}. "
            "Should I restate the quick question?"
        )
    client_name = campaign_value(campaign, "client_name", "Northstar Workflow Labs")
    product_name = campaign_value(campaign, "product_name", "RouteSignal CRM")
    representative = nested_campaign_value(campaign, "caller_identity", "representative_name", "Maya")
    product_relationship = nested_campaign_value(
        campaign,
        "caller_identity",
        "product_relationship",
        f"the team behind {product_name}",
    )
    if language.startswith("de"):
        return (
            f"Ich bin {representative} von {client_name}, dem Team hinter {product_name}. "
            "Es geht um verpasste Rueckrufe und Uebergaben nach Demo-Anfragen."
        )
    return (
        f"I am {representative} calling from {client_name}, {product_relationship}. "
        "I was calling about missed callbacks and handoffs in inbound demo follow-up. "
        "Should I restate the quick reason?"
    )


def callback_request_time_response(language: str) -> str:
    if language.startswith("de"):
        return "Verstanden. Zu welcher Zeit soll ich den Rueckruf notieren?"
    return "Of course. What time should I note for the callback?"


def callback_later_time_request_response(language: str) -> str:
    if language.startswith("de"):
        return "Ja. Zu welcher Zeit soll ich den Rueckruf notieren?"
    return "Sure. What time should I call back?"


def callback_request_time_response_for_transcript(language: str, normalized: str) -> str:
    if language.startswith("de"):
        return callback_request_time_response(language)
    if normalized_contains_any(normalized, {"not now call me later", "not now call me back"}):
        return "Sure. What time should I note for the callback?"
    if normalized_contains_any(normalized, {"tomorrow", "next week", "monday", "tuesday", "wednesday", "thursday", "friday"}):
        return "That can work. What time should I note for the callback?"
    if normalized_contains_any(normalized, {"not now", "later", "no time", "busy"}):
        return "No problem. What time should I note for the callback?"
    return callback_request_time_response(language)


def callback_time_confirmed_response(language: str, campaign: dict | None = None) -> str:
    if language.startswith("de"):
        return "Bestaetigt. Ich notiere den Rueckruf so. Auf Wiederhoeren."
    if is_generic_campaign_config(campaign):
        context = generic_campaign_context(campaign)
        return f"Confirmed. I will note that time for your {context['target']}. Goodbye."
    return "Confirmed. I will record that callback time for the specialist. Goodbye."


def appointment_time_confirmed_response(language: str) -> str:
    if language.startswith("de"):
        return "Bestaetigt. Ich notiere diese Zeit fuer die Workflow-Pruefung. Auf Wiederhoeren."
    return "Confirmed. I will note that time for the workflow review. Goodbye."


def callback_workflow_clarification_response(language: str) -> str:
    if language.startswith("de"):
        return "Mit Rueckrufen meine ich Nachfass-Erinnerungen nach Demo-Anfragen, nicht diesen Anruf. RouteSignal haelt Besitzer und naechsten Schritt sichtbar. Passieren verpasste Nachfassaktionen oft genug?"
    return (
        "Callbacks here mean follow-up reminders after an inbound demo request, not scheduling this call. "
        "Which part is confusing: what callback means here, who owns it, or whether missed follow-ups happen?"
    )


def appointment_think_about_it_response(language: str, gap: str | None) -> str:
    if language.startswith("de"):
        return "Kein Problem. Sie muessen die Workflow-Pruefung jetzt nicht zusagen. Ich kann eine kurze Zusammenfassung senden und spaeter zurueckrufen. Zu welcher Zeit soll ich den Rueckruf notieren?"
    del gap
    return (
        "No problem. You do not have to accept the workflow review now. "
        "I can keep it to a short summary and call back later. What time should I call back?"
    )


def has_callback_time_signal(normalized: str) -> bool:
    if not normalized:
        return False
    has_numeric_time = bool(
        re.search(r"\b(?:[1-9]|1[0-2])\s*(?:a\s*m|p\s*m|am|pm|uhr)\b", normalized)
        or re.search(r"\bat\s+(?:[1-9]|1[0-2])\b", normalized)
        or re.search(r"\b(?:[1-9]|1[0-2])\s+works\b", normalized)
    )
    has_day_or_callback_context = normalized_contains_any(
        normalized,
        {
            "tomorrow",
            "today",
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "next week",
            "morgen",
            "mittwoch",
            "donnerstag",
            "freitag",
            "dienstag",
            "call me",
            "call back",
            "callback",
            "works",
        },
    )
    return has_numeric_time and has_day_or_callback_context


def has_callback_request_signal(normalized: str) -> bool:
    if not normalized:
        return False
    return normalized_contains_any(
        normalized,
        {
            "call back later",
            "callback later",
            "call me back",
            "call me later",
            "can you call back",
            "can you call me",
            "short summary and call back",
            "i do not have time",
            "i dont have time",
            "do not have time",
            "dont have time",
            "no time right now",
            "i cannot talk now",
            "i cant talk now",
            "too busy right now",
            "busy right now",
            "not now",
            "naechste woche nochmal",
            "spaeter noch mal",
            "morgen zurueckrufen",
            "anderen zeitpunkt",
        },
    )


def is_permission_time_refusal_reply(normalized: str) -> bool:
    if not normalized:
        return False
    if has_callback_request_signal(normalized):
        return True
    if normalized in {
        "no i don t",
        "no i dont",
        "no i do not",
        "no i cannot",
        "no i can t",
        "no i cant",
    }:
        return True
    return normalized_contains_any(
        normalized,
        {
            "do not have a minute",
            "dont have a minute",
            "don t have a minute",
            "do not have a min",
            "dont have a min",
            "not a good time",
            "bad time",
        },
    )


def has_callback_scheduling_request_signal(normalized: str) -> bool:
    return has_callback_request_signal(normalized)


def is_callback_stop_reply(normalized: str) -> bool:
    if not normalized:
        return False
    if normalized in {"never", "not ever"}:
        return True
    return normalized_contains_any(
        normalized,
        {
            "maybe just don t",
            "maybe just dont",
            "maybe just do not",
            "maybe don t",
            "maybe dont",
            "maybe do not",
            "just don t",
            "just dont",
            "just do not",
            "no callback",
            "no call back",
            "do not call back",
            "dont call back",
            "don t call back",
            "do not call me back",
            "dont call me back",
            "don t call me back",
            "do not call again",
            "dont call again",
            "don t call again",
            "never call",
            "never call me",
        },
    )


def previous_response_offered_callback_later(turns: list[dict]) -> bool:
    if not turns:
        return False
    response = normalize_text(str((turns[-1].get("summary") or {}).get("final_response") or ""))
    return normalized_contains_any(
        response,
        {
            "call back later",
            "callback later",
            "what time should i call back",
            "what time should i note for the callback",
            "what time should i note for callback",
        },
    )


def has_callback_time_confirmation_signal(normalized: str, session_state: dict | None = None) -> bool:
    if not has_callback_time_signal(normalized):
        return False
    if normalized_contains_any(
        normalized,
        {
            "call me",
            "call back",
            "callback",
            "uhr",
        },
    ):
        return True
    turns = list((session_state or {}).get("turns") or [])
    for turn in reversed(turns[-3:]):
        continuity = turn.get("continuity") or {}
        reason = str(continuity.get("reason") or "")
        summary = turn.get("summary") or {}
        if reason == "callback_request_time_needed" or str(summary.get("sales_difficulty") or "") == "callback-request":
            return True
    return False


def has_callback_workflow_gap_signal(normalized: str) -> bool:
    if not normalized:
        return False
    if has_callback_scheduling_request_signal(normalized) or has_callback_time_signal(normalized):
        return False
    return normalized_contains_any(
        normalized,
        {
            "callback",
            "callbacks",
            "call backs",
            "callback reminders",
            "missed callbacks",
            "missed callback",
            "callbacks are the problem",
            "callback is the problem",
            "demo callbacks",
            "follow up",
            "follow-up",
            "followup",
            "missed follow ups",
            "missed follow-ups",
            "misses follow ups",
            "misses follow-ups",
            "missed follow up",
            "missed follow-up",
            "follow ups keep slipping",
            "follow-ups keep slipping",
            "next step gap",
        },
    )


def is_callback_workflow_question(normalized: str) -> bool:
    if not normalized:
        return False
    if not normalized_contains_any(normalized, {"callback", "callbacks", "call backs", "missed calls", "missed callbacks"}):
        return False
    if has_callback_time_signal(normalized) or has_callback_scheduling_request_signal(normalized):
        return False
    return normalized_contains_any(
        normalized,
        {
            "what do you mean",
            "what does",
            "what is",
            "what are",
            "what about",
            "explain",
            "mean by",
            "how does",
        },
    )


def callback_semantic_from_transcript(normalized: str, session_state: dict | None = None) -> str | None:
    if not normalized:
        return None
    if has_callback_time_confirmation_signal(normalized, session_state):
        return CALLBACK_TIME_CONFIRMATION
    if has_callback_scheduling_request_signal(normalized):
        return CALLBACK_SCHEDULING_REQUEST
    if is_callback_workflow_question(normalized) or has_callback_workflow_gap_signal(normalized):
        return CALLBACK_WORKFLOW_GAP
    return None


def has_time_pressure_signal(normalized: str) -> bool:
    return normalized_contains_any(
        normalized,
        {
            "i do not have a lot of time",
            "i dont have a lot of time",
            "i don t have a lot of time",
            "do not have a lot of time",
            "dont have a lot of time",
            "don t have a lot of time",
            "not much time",
            "no time right now",
            "busy right now",
        },
    )


def is_time_constrained_agenda_request(normalized: str) -> bool:
    return has_time_pressure_signal(normalized) and normalized_contains_any(
        normalized,
        {
            "what do you want",
            "what exactly",
            "what is this about",
            "why are you calling",
            "why did you call",
            "what are you asking",
        },
    )


def is_call_purpose_question(normalized: str) -> bool:
    return normalized_contains_any(
        normalized,
        {
            "why are you calling",
            "why did you call",
            "what is this about",
            "what is this call about",
            "what is this called about",
            "what is this called",
            "what s this about",
            "what are you calling about",
            "what are you trying to say",
            "what are you trying to sell",
            "what are you saying",
            "why this call",
        },
    )


def is_buyer_expects_agent_to_lead(normalized: str) -> bool:
    return normalized_contains_any(
        normalized,
        {
            "you called me",
            "i do not have a question",
            "i dont have a question",
            "i don t have a question",
            "you should ask",
            "ask whatever you want",
        },
    )


def is_next_step_question(normalized: str) -> bool:
    return normalized_contains_any(
        normalized,
        {"what is the next step", "what s the next step", "what next", "next step", "what happens next"},
    )


def is_written_summary_request(normalized: str) -> bool:
    return normalized_contains_any(
        normalized,
        {
            "send me the short summary",
            "send a short summary",
            "send me a summary",
            "send me information",
            "written summary",
            "email me",
        },
    )


def is_workflow_review_scope_question(normalized: str) -> bool:
    return normalized_contains_any(
        normalized,
        {
            "how short",
            "how long",
            "workflow review",
            "review that you re talking about",
            "review you are talking about",
        },
    )


def is_time_waste_friction(normalized: str) -> bool:
    return normalized_contains_any(
        normalized,
        {
            "wasting time",
            "waste time",
            "wasting my time",
            "taking too long",
            "you are wasting",
        },
    )


def is_buyer_stop_request(normalized: str) -> bool:
    if normalized in {"stop", "please stop", "bro stop", "bruh stop", "bra stop"}:
        return True
    return normalized_contains_any(
        normalized,
        {
            "stop talking",
            "stop here",
            "stop the call",
            "end the call",
            "i do not want to talk",
            "i dont want to talk",
            "i don t want to talk",
            "i do not want to talk anymore",
            "i dont want to talk anymore",
            "i don t want to talk anymore",
            "do not call us again",
            "dont call us again",
            "don t call us again",
            "do not call me again",
            "dont call me again",
            "don t call me again",
        },
    )


def is_topic_confusion(normalized: str) -> bool:
    return normalized_contains_any(
        normalized,
        {
            "i do not know what",
            "i dont know what",
            "i don t know what",
            "i do not know what you re talking about",
            "i dont know what you re talking about",
            "i don t know what you re talking about",
            "what are you talking about",
            "not making sense",
            "not clear",
        },
    )


def is_uncertain_gap(normalized: str) -> bool:
    return normalized in {
        "i do not know",
        "i dont know",
        "i don t know",
        "not sure",
        "i m not sure",
        "im not sure",
        "not familiar",
        "not really familiar",
        "not familiar to me",
        "they are not familiar to me",
        "they re not familiar to me",
        "they re not really familiar to me",
        "theyre not familiar to me",
        "theyre not really familiar to me",
    }


def is_frustrated_confusion(normalized: str) -> bool:
    return normalized_contains_any(normalized, {"the fuck", "what the fuck", "what the hell", "bullshit"})


def is_new_trial_request_clarification(normalized: str) -> bool:
    return normalized_contains_any(
        normalized,
        {
            "what do you mean by new trial request",
            "what do you mean by new trial requests",
            "what is a new trial request",
            "what are new trial requests",
            "new trial request",
            "new trial requests",
        },
    )


def is_buyer_no_question_repair(normalized: str) -> bool:
    return normalized_contains_any(
        normalized,
        {
            "i did not ask a question",
            "i didnt ask a question",
            "i didn t ask a question",
            "i do not have a question",
            "i dont have a question",
            "i don t have a question",
        },
    )


def is_value_relevance_question(normalized: str) -> bool:
    return normalized_contains_any(
        normalized,
        {
            "why does that matter",
            "why would that matter",
            "why this matters",
            "why does this matter",
            "why does it matter",
            "why it matters",
            "what this means for us",
            "what this mean for us",
            "what does this mean for us",
            "what does it mean for us",
            "what does that mean for us",
            "why is this useful",
            "why would this help",
            "how would it help",
            "how does that help",
            "would it",
            "i dont know would it",
            "i don t know would it",
        },
    )


def buyer_stop_response(language: str) -> str:
    if language.startswith("de"):
        return "Verstanden. Ich stoppe hier. Auf Wiederhoeren."
    return "Understood. I will stop here. Goodbye."


def new_trial_request_clarification_response(language: str) -> str:
    if language.startswith("de"):
        return "Mit neuen Testanfragen meine ich eingehende Demo- oder Testanfragen, die einen Besitzer und eine Nachfassung brauchen. Passiert dort etwas wie ein verpasster Rueckruf?"
    return "I meant inbound demo or trial inquiries that need an owner and a follow-up step. Does that handoff ever get missed?"


def buyer_no_question_response(language: str, campaign: dict | None = None) -> str:
    if is_generic_campaign_config(campaign):
        return generic_campaign_review_question(language, campaign)
    if language.startswith("de"):
        return "Stimmt, Sie haben keine Frage gestellt. Ich rufe wegen einer Sache an: gehen Demo-Nachfassaktionen bei Besitzer, Rueckruf oder Uebergabe verloren?"
    return "Fair, you did not ask a question. I called to check one thing: are demo leads getting assigned, reminded, and followed up, or are some slipping?"


def value_relevance_response(language: str, campaign: dict | None = None) -> str:
    if is_generic_campaign_config(campaign):
        return generic_campaign_focus_text(language, "effort", campaign) or generic_campaign_review_question(language, campaign)
    if language.startswith("de"):
        return "Es zaehlt nur, wenn diese Luecke heute Zeit kostet: verpasste Rueckrufe, unklare Besitzer oder verlorene Uebergaben. Was kostet heute wirklich Zeit?"
    return "In plain terms, it matters only if that gap costs time today: missed callbacks, unclear owners, or lost handoffs. Which one costs time today?"


def time_constrained_agenda_response(language: str, campaign: dict | None = None) -> str:
    if is_generic_campaign_config(campaign):
        return generic_campaign_review_question(language, campaign)
    if language.startswith("de"):
        return "Ich halte es bei einer Frage: gehen Demo-Nachfassaktionen bei Besitzer, Rueckruf-Erinnerung oder Uebergabe verloren?"
    return "I will keep it to one question: are inbound demo follow-ups missing owners, callback reminders, or handoffs?"


def seller_agenda_recovered_response(language: str, campaign: dict | None = None) -> str:
    if is_generic_campaign_config(campaign):
        return call_purpose_response(language, campaign)
    if language.startswith("de"):
        return "Fair. Ich pruefe einen Ablauf: verlieren Demo-Nachfassaktionen Besitzer, Rueckruf-Erinnerungen oder Uebergabestatus?"
    return (
        "Fair. RouteSignal helps with inbound demo follow-up: making sure demo leads get assigned, reminded, and followed up. "
        "I called to check one thing: are any demo leads slipping through today?"
    )


def call_purpose_response(language: str, campaign: dict | None = None) -> str:
    if is_generic_campaign_config(campaign):
        client_name = campaign_value(campaign, "client_name", "the campaign team")
        offer_name = campaign_value(campaign, "product_or_offer_name", campaign_value(campaign, "product_name", "this review"))
        appointment_target = campaign_value(campaign, "appointment_target", "human review")
        gaps = generic_campaign_gap_clause(campaign)
        if language.startswith("de"):
            return (
                f"Ich rufe von {client_name} wegen {offer_name} an. "
                f"Ich pruefe, ob {gaps} eine kurze {appointment_target} brauchen."
            )
        return (
            f"I am calling from {client_name} about {offer_name}, and asking whether {gaps} are worth a short {appointment_target}. "
            "If none of those apply, I can stop here."
        )
    if language.startswith("de"):
        return "Ich rufe wegen Demo-Nachfassaktionen an: Besitzer, Rueckruf-Erinnerung und Uebergabestatus. Soll ich eine dieser Luecken pruefen?"
    return (
        "I am calling because RouteSignal helps with inbound demo follow-up: demo leads getting assigned, reminded, and followed up. "
        "Northstar is asking for a short workflow review if leads are slipping today."
    )


def workflow_review_next_step_response(language: str, campaign: dict | None = None) -> str:
    if is_generic_campaign_config(campaign):
        return generic_campaign_next_step_text(language, campaign)
    if language.startswith("de"):
        return "Der naechste Schritt ist eine kurze Pruefung: Besitzer, Rueckruf-Erinnerung oder Uebergabe. Welche Luecke soll ich pruefen?"
    return "The quick check is one inbound demo follow-up gap. Should I check who gets the lead, the reminder, or the next reply?"


def written_summary_response(language: str, campaign: dict | None = None) -> str:
    if is_generic_campaign_config(campaign):
        context = generic_campaign_context(campaign)
        return f"I can note a short summary for {context['offer']}. Should it focus on {context['gaps']}, or should I stop here?"
    if language.startswith("de"):
        return "Ich kann eine kurze Workflow-Zusammenfassung schicken: Besitzer, Rueckruf-Erinnerung und Uebergabestatus. Soll sie sich auf Rueckruf-Erinnerungen konzentrieren?"
    return "I can send a short workflow summary: who gets the demo lead, when the reminder happens, and whether the next reply happened. Should it focus on the callback gap you mentioned?"


def workflow_review_scope_response(language: str, campaign: dict | None = None) -> str:
    if is_generic_campaign_config(campaign):
        return generic_campaign_product_detail_text(language, campaign)
    if language.startswith("de"):
        return "Kurz heisst eine Workflow-Luecke, keine volle Demo: Besitzer, Rueckruf-Erinnerung oder Uebergabe. Welche soll ich pruefen?"
    return "Short means one inbound demo follow-up gap, not a full demo. Should I check who gets the lead, the reminder, or the next reply?"


def time_waste_repair_response(language: str, campaign: dict | None = None) -> str:
    if is_generic_campaign_config(campaign):
        return generic_campaign_focus_text(language, "effort", campaign) or generic_campaign_review_question(language, campaign)
    if language.startswith("de"):
        return "Fair. Ich kann hier stoppen. Die kurze Pruefung ist, ob Demo-Nachfassaktionen Besitzer oder Rueckruf-Erinnerungen verlieren. Soll ich beenden?"
    return "Fair. I can stop here. The quick check is whether demo follow-ups lose owners or callback reminders. Should I end the call?"


def uncertain_gap_response(language: str, campaign: dict | None = None) -> str:
    if is_generic_campaign_config(campaign):
        return generic_campaign_review_question(language, campaign)
    if language.startswith("de"):
        return "Kein Problem. Die kurze Pruefung ist einfacher: fehlt Demo-Nachfassaktionen manchmal Besitzer, Rueckruf-Erinnerung oder Uebergabe?"
    return "No problem. The quick check is simpler: do demo follow-ups ever miss an owner, callback reminder, or handoff?"


def topic_confusion_response(language: str, campaign: dict | None = None) -> str:
    if is_generic_campaign_config(campaign):
        return generic_campaign_review_question(language, campaign)
    if language.startswith("de"):
        return "Ich war nicht klar. RouteSignal betrifft Demo-Nachfassaktionen: Besitzer, Rueckruf-Erinnerung und Uebergabestatus. Soll ich stoppen?"
    return "I am not being clear. RouteSignal is for demo follow-up: getting leads assigned, reminded, and followed up. Should I keep it to callback reminders, or stop here?"


def frustrated_confusion_response(language: str, campaign: dict | None = None) -> str:
    if is_generic_campaign_config(campaign):
        return generic_campaign_review_question(language, campaign)
    if language.startswith("de"):
        return "Fair, ich habe den Faden verloren. Die kurze Pruefung ist Demo-Nachfassung: Besitzer, Rueckruf-Erinnerung oder Uebergabe. Soll ich stoppen?"
    return "Fair, I lost the thread. The quick check is demo follow-up owners, callback reminders, or handoffs. Should I stop?"


def call_context_recovery_response(normalized: str, resolved_focus: str | None, language: str, campaign: dict | None = None) -> dict | None:
    focus = resolved_focus or "qualification"
    checks = [
        (is_time_constrained_agenda_request, "time_constrained_agenda_answered", time_constrained_agenda_response),
        (is_call_purpose_question, "call_purpose_explained", call_purpose_response),
        (is_buyer_expects_agent_to_lead, "seller_agenda_recovered", seller_agenda_recovered_response),
        (is_next_step_question, "workflow_review_next_step_explained", workflow_review_next_step_response),
        (is_written_summary_request, "written_summary_next_step_offered", written_summary_response),
        (is_workflow_review_scope_question, "workflow_review_scope_explained", workflow_review_scope_response),
        (is_time_waste_friction, "time_waste_repair_offered", time_waste_repair_response),
        (is_frustrated_confusion, "frustration_confusion_repaired", frustrated_confusion_response),
        (is_topic_confusion, "topic_confusion_repaired", topic_confusion_response),
        (is_uncertain_gap, "uncertain_gap_simplified", uncertain_gap_response),
    ]
    for detector, reason, response_builder in checks:
        if detector(normalized):
            dialogue_focus = "qualification" if reason in {"call_purpose_explained", "seller_agenda_recovered"} else focus
            try:
                candidate_response = response_builder(language, campaign)
            except TypeError:
                candidate_response = response_builder(language)
            return {
                "applied": True,
                "reason": reason,
                "dialogue_focus": dialogue_focus,
                "candidate_response": candidate_response,
            }
    return None


def is_crm_replacement_question(normalized: str) -> bool:
    return bool(normalized and "crm" in normalized and normalized_contains_any(normalized, {"replace", "replacing", "instead of"}))


def public_crm_boundary_response(normalized: str, campaign: dict | None) -> str:
    if is_generic_campaign_config(campaign):
        return generic_campaign_product_detail_text(language=str((campaign or {}).get("language") or "en"), campaign=campaign)
    product_name = campaign_value(campaign, "product_name", "RouteSignal CRM")
    if is_crm_replacement_question(normalized):
        return (
            f"No. {product_name} is not meant to replace a CRM that already works. "
            "It is worth reviewing only if demo leads still miss assignment, reminders, or follow-up around the CRM. "
            "Is that the gap you are checking?"
        )
    if normalized_contains_any(normalized, {"salesforce"}):
        crm_name = "Salesforce"
    elif normalized_contains_any(normalized, {"hubspot"}):
        crm_name = "HubSpot"
    else:
        crm_name = "your CRM"
    return (
        f"For {crm_name}, someone from Northstar would need to verify exact setup and permissions before I claim fit. "
        "The useful check here is simpler: are demo leads still missing assignment, reminders, or follow-up?"
    )


def structured_reasoning_continuity_response(
    normalized: str,
    language: str,
    campaign: dict,
    turns: list[dict],
    resolved_focus: str | None,
    dialogue_reasoning: dict | None,
) -> dict | None:
    if not isinstance(dialogue_reasoning, dict):
        return None
    try:
        confidence = float(dialogue_reasoning.get("confidence") or 0.0)
    except (TypeError, ValueError):
        confidence = 0.0
    if confidence < 0.86:
        return None

    dialogue_act = str(dialogue_reasoning.get("dialogue_act") or "")
    if dialogue_act == "integration_question" and not language.startswith("de"):
        reason = (
            "structured_reasoner_crm_replacement_answered"
            if is_crm_replacement_question(normalized)
            else "structured_reasoner_integration_boundary_answered"
        )
        return {
            "applied": True,
            "reason": reason,
            "dialogue_focus": "qualification" if is_crm_replacement_question(normalized) else "details",
            "structured_reasoner_used": True,
            "dialogue_reasoning": dialogue_reasoning,
            "candidate_response": public_crm_boundary_response(normalized, campaign),
        }

    if dialogue_act == "previous_question_clarification":
        if (
            is_callback_workflow_question(normalized)
            or is_new_trial_request_clarification(normalized)
            or is_value_relevance_question(normalized)
            or is_buyer_no_question_repair(normalized)
            or is_topic_confusion(normalized)
            or is_frustrated_confusion(normalized)
            or plain_qualification_term_clarification_text(language, normalized) is not None
        ):
            return None
        focus = resolved_focus or "qualification"
        return {
            "applied": True,
            "reason": "previous_question_clarified",
            "dialogue_focus": focus,
            "structured_reasoner_used": True,
            "dialogue_reasoning": dialogue_reasoning,
            "candidate_response": clarify_previous_question_text(language, focus, previous_agent_question(turns), campaign),
        }
    return None


def english_live_demo_campaign_response(normalized: str, campaign: dict) -> dict | None:
    knowledge = campaign.get("product_knowledge") or {}
    if not knowledge or str(campaign.get("language") or "en").lower().startswith("de"):
        return None

    def candidate(reason: str, dialogue_focus: str, response: str) -> dict:
        return {
            "applied": True,
            "reason": reason,
            "dialogue_focus": dialogue_focus,
            "candidate_response": response,
        }

    if normalized_contains_any(normalized, {"social security", "ssn", "personal id", "account number", "diagnosis", "medical condition"}):
        return candidate(
            "sensitive_personal_data_boundary_answered",
            "sensitive_data",
            "Please don't share sensitive personal details on this call. This is not the right place for that information, so I'll stop here.",
        )
    if normalized_contains_any(normalized, {"soc 2", "soc2", "security", "secure", "compliance"}):
        return candidate(
            "campaign_depth_security_boundary_answered",
            "security",
            "I cannot claim that here. Use verified security material before any serious rollout discussion.",
        )
    if normalized_contains_any(normalized, {"salesforce", "hubspot", "integrate", "integration", "connect with", "crm"}):
        return candidate(
            "campaign_depth_crm_replacement_answered" if is_crm_replacement_question(normalized) else "campaign_depth_integration_boundary_answered",
            "qualification" if is_crm_replacement_question(normalized) else "details",
            public_crm_boundary_response(normalized, campaign),
        )
    if normalized_contains_any(normalized, {"do i need to talk to a specialist", "need a specialist", "talk to a specialist"}):
        return candidate(
            "campaign_depth_unnecessary_handoff_answered",
            "details",
            "Not for basics. I can cover price, fit, and workflow here. Exact security or integration proof needs verified review.",
        )
    if normalized_contains_any(normalized, {"fifty nine", "59 dollars", "$59", "growth plan", "growth"}) and normalized_contains_any(
        normalized,
        {"get", "include", "included", "value", "what do i", "what does"},
    ):
        return candidate(
            "campaign_depth_growth_plan_answered",
            "price",
            "It adds priority routing, reminders, duplicate checks, Slack alerts, and handoff review when missed callbacks cost time. Which gap shows up more: callbacks, duplicates, or visibility?",
        )
    if normalized_contains_any(normalized, {"manual", "spreadsheet", "tracking leads manually", "track leads manually"}):
        return candidate(
            "campaign_depth_manual_tracking_answered",
            "fit",
            "That breaks when follow-up is split between tools. RouteSignal keeps the demo lead, reminder, and next reply in one workflow. Where does it break first today?",
        )
    if normalized_contains_any(normalized, {"small team", "small teams"}):
        return candidate(
            "campaign_depth_small_team_fit_answered",
            "fit",
            "Start with Starter if missed follow-up is occasional. Use Growth only when routing saves real time. Are missed callbacks occasional, or frequent enough to automate?",
        )
    if normalized_contains_any(
        normalized,
        {
            "what does your product",
            "what does the product",
            "what do you do",
            "what does it do",
            "what is your product",
            "product actually do",
        },
    ):
        return candidate(
            "campaign_depth_product_explanation_answered",
            "details",
            (
                knowledge.get("short_product_explanation")
                or "RouteSignal CRM assigns demo leads, captures follow-up tasks, and shows which replies still need action."
            )
            + " Where does follow-up break first today: assignment, reminders, or missed replies?",
        )
    if normalized_contains_any(normalized, {"workflow include", "workflow includes", "what is included", "included in the workflow"}):
        return candidate(
            "campaign_depth_workflow_scope_answered",
            "details",
            "It covers lead capture, qualification, routing, reminders, and handoff review. Which part is weakest today: capture, routing, reminders, or handoff review?",
        )
    return None


def response_asked_price_choice(response: str) -> bool:
    lowered = response.lower()
    return (
        "bigger concern the monthly price" in lowered
        or "main concern price" in lowered
        or "preis, die bedingungen" in lowered
        or "preis selbst oder darum" in lowered
    )


def response_asked_main_focus_choice(response: str) -> bool:
    lowered = response.lower()
    return (
        "main question about price, fit, timing, or exact product details" in lowered
        or "price, fit, timing" in lowered
        or "main concern whether this is relevant for your situation, the price, or the timing" in lowered
        or "passung, zeitpunkt oder genaue details" in lowered
    )


def response_reopens_focus_menu(response: str) -> bool:
    lowered = normalize_text(response)
    return (
        response_asked_main_focus_choice(response)
        or response_asked_price_choice(response)
        or normalized_contains_any(
            lowered,
            {
                "which part is least clear",
                "which part is more familiar",
                "which part should i check first",
                "which one is causing trouble",
                "which part causes trouble",
                "manual tracking or missed callbacks",
                "premium or budget, coverage fit",
                "plan fit, coverage or availability",
                "manual work, integration",
                "vehicle issue, repair timing",
            },
        )
    )


def focus_menu_count(turns: list[dict]) -> int:
    return sum(
        1
        for turn in turns
        if response_reopens_focus_menu(str((turn.get("summary") or {}).get("final_response") or ""))
    )


def previous_response_list(turns: list[dict]) -> list[str]:
    responses: list[str] = []
    for turn in turns:
        response = str((turn.get("summary") or {}).get("final_response") or "").strip()
        if response:
            responses.append(response)
    return responses


def previous_responses(turns: list[dict]) -> set[str]:
    return set(previous_response_list(turns))


def focus_turn_count(turns: list[dict], focus: str) -> int:
    return sum(
        1
        for turn in turns
        if str((turn.get("continuity") or {}).get("dialogue_focus") or "") == focus
    )


def dialogue_focus_from_turns(turns: list[dict]) -> str | None:
    for turn in reversed(turns):
        continuity = turn.get("continuity") or {}
        explicit_focus = continuity.get("dialogue_focus")
        if explicit_focus:
            return str(explicit_focus)
        reason = str(continuity.get("reason") or "")
        if not continuity.get("applied") and not reason.startswith(("short_answer_selected_", "focus_shift_to_", "resolved_")):
            continue
        response = str((turn.get("summary") or {}).get("final_response") or "").lower()
        if "selected_price" in reason or "focus only on price" in response or "stay on price" in response:
            return "price"
        if "selected_terms" in reason or "review the terms clearly" in response or "terms clearly first" in response:
            return "terms"
        if "selected_effort" in reason or "worth your time" in response or "worth the review" in response:
            return "effort"
        if "selected_fit" in reason or "focus on fit" in response:
            return "fit"
        if "selected_timing" in reason or "keep timing first" in response:
            return "timing"
        if "selected_details" in reason or "product details" in response:
            return "details"
    return None


def continuity_text(language: str, focus: str, *, persisted: bool = False, campaign: dict | None = None) -> str:
    generic = generic_campaign_focus_text(language, focus, campaign, persisted=persisted)
    if generic:
        return generic
    german = language.startswith("de")
    if focus == "price":
        if german:
            return (
                "Verstanden. Wir bleiben beim Preis: Sinnvoll ist ein klarer Vergleich von Kosten und Bedingungen, "
                "ohne in diesem Anruf eine Entscheidung zu verlangen."
            )
        if persisted:
            return live_demo_price_answer(language)
        return live_demo_price_answer(language)
    if focus == "terms":
        if german:
            if persisted:
                return "Dann bleiben wir bei den Bedingungen. Der naechste sinnvolle Schritt ist, die Laufzeit, den Umfang und die Ausstiegsmoeglichkeit schriftlich zu vergleichen."
            return "Verstanden. Dann pruefen wir zuerst die Bedingungen klar, bevor ueberhaupt ein Wechsel im Raum steht."
        if persisted:
            return "Terms should be written first: contract length, scope, and exit path. No commitment on this call."
        return "Terms should be checked in writing first: length, scope, and exit path. No commitment on this call."
    if focus == "effort":
        if german:
            if persisted:
                return "Dann machen wir den Aufwand konkret: Die Durchsicht lohnt sich nur, wenn Rueckrufe oder Nachverfolgung heute wirklich Zeit kosten."
            return "Verstanden. Dann pruefen wir zuerst, ob sich die Durchsicht fuer Ihre Zeit lohnt; wenn nicht, gibt es keinen Grund zu draengen."
        if persisted:
            return "The effort question is simple: would missed follow-up cost more time than a short review?"
        return "The effort question is simple: would missed follow-up cost more time than a short review?"
    if focus == "fit":
        if german:
            if persisted:
                return "Dann bleiben wir bei der Passung. Entscheidend ist, ob Rueckruf- oder Nachverfolgungsarbeit in Ihrem aktuellen Ablauf wirklich offen bleibt."
            return "Verstanden. Dann geht es zuerst um Passung: ob das Problem in Ihrer Situation wirklich existiert, bevor wir ueber einen naechsten Schritt sprechen."
        if persisted:
            return "Fit depends on actual missed leads, callbacks, or handoffs. If your team is seeing that, a short review is the next step."
        return "Fit depends on actual missed leads, callbacks, or handoffs. If your team is seeing that, a short review is the next step."
    if focus == "timing":
        if german:
            if persisted:
                return "Dann bleibt der Zeitpunkt der Engpass. Ich wuerde es bei einer schriftlichen Zusammenfassung oder einem spaeteren Rueckruf belassen."
            return "Verstanden. Dann steht der Zeitpunkt im Vordergrund. Heute muss nichts entschieden werden; hoechstens eine kurze schriftliche Zusammenfassung oder ein spaeterer Rueckruf."
        if persisted:
            return "No problem. We do not need to decide anything now."
        return "No problem. We do not need to decide anything now."
    if focus == "details":
        if german:
            if persisted:
                return "Dann bleiben wir bei den Details. Ich wuerde nur klaeren, was der Workflow abdeckt, was er nicht abdeckt und was ein Spezialist pruefen muss."
            return "Verstanden. Dann bleiben wir bei den Produktdetails: was der Workflow umfasst, was er nicht umfasst, und was ein Spezialist pruefen sollte."
        if persisted:
            return "The workflow scope is lead routing, follow-up, and handoff review. Exact integrations need verified checks."
        return "The workflow scope is lead routing, follow-up, and handoff review. Exact integrations need verified checks."
    if focus == "security":
        if german:
            return "Bei Sicherheit sollte ich nur verifiziertes Material nutzen. Der sinnvolle naechste Schritt ist eine schriftliche Sicherheitspruefung."
        return "For security, I should only use verified material. The useful next step is written security review, not a live guess."
    if focus == "provider_gap":
        if german:
            return "Dann pruefen wir nur die echte Luecke: Routing, Rueckrufe oder Uebergaben. Welche davon rutscht heute durch?"
        return "The useful check is whether routing, callbacks, or handoffs still slip with your current setup. Which one is still a gap?"
    return "I can answer that directly if you name the point: workflow routing, price, security, or callback timing."


def focus_followup_text(language: str, focus: str, normalized: str, campaign: dict | None = None) -> str:
    generic = generic_campaign_focus_text(language, focus, campaign, normalized=normalized)
    if generic:
        return generic
    german = language.startswith("de")
    asks_for_explanation = normalized_contains_any(
        normalized,
        {
            "explain",
            "tell me",
            "what does",
            "what is",
            "what's",
            "what would",
            "how does",
            "include",
            "includes",
            "why does",
            "why would",
            "why is",
        },
    )
    asks_for_recommendation = normalized_contains_any(
        normalized,
        {"recommend", "what do you recommend", "what would you choose", "what should i choose"},
    )
    agrees_to_continue = normalized_contains_any(
        normalized,
        {"do that", "let's do that", "lets do that", "all right", "okay", "ok", "yes", "sure", "sounds good"},
    )
    if focus == "price":
        if asks_for_recommendation:
            if german:
                return live_demo_price_answer(language)
            return live_demo_price_answer(language)
        if asks_for_explanation:
            if german:
                return live_demo_price_answer(language)
            return live_demo_price_answer(language)
        if agrees_to_continue:
            if german:
                return live_demo_price_answer(language)
            return live_demo_price_answer(language)
    if focus == "effort":
        if asks_for_explanation:
            if german:
                return "Die Aufwandfrage ist konkret: Lohnt sich die Durchsicht nur dann, wenn Rueckrufe oder Nachverfolgung heute wirklich Zeit kosten?"
            return "The effort question is concrete: is a review worth it only if missed callbacks or follow-up work are costing time today?"
        if agrees_to_continue:
            if german:
                return "Gut, dann pruefen wir nur den Aufwand. Wenn der Zeitverlust heute nicht klar ist, sollte ich keinen naechsten Schritt draengen."
            return "Then keep it to the effort question: is missed follow-up costing enough time to justify a short review?"
    if focus == "details":
        if asks_for_explanation:
            if german:
                return "Bei den Details geht es hier um Lead-Routing und Nachverfolgung. Was genau integriert wird, sollte ein Spezialist pruefen."
            return "The workflow scope is lead routing, follow-up, and handoff review. Exact integrations need verified checks."
        if agrees_to_continue:
            if german:
                return "Gut, dann bleiben wir bei den Details: was der Workflow abdeckt, was offen bleibt und was ein Spezialist pruefen sollte."
            return "Keep the scope narrow: what the workflow covers, what remains open, and what needs verified review."
    if focus == "fit":
        if asks_for_explanation:
            if german:
                return "Bei der Passung geht es darum, ob Lead-Routing oder Nachverfolgung in Ihrem aktuellen Ablauf wirklich ein Problem ist."
            return "Fit depends on actual missed leads, callbacks, or handoffs. If your team is seeing that, a short review is the next step."
        if agrees_to_continue:
            if german:
                return "Gut, dann bleiben wir bei der Passung und pruefen nur, ob das Problem in Ihrem Ablauf wirklich existiert."
            return "Then keep it to fit: are leads, callbacks, or handoffs actually getting missed today?"
    if focus == "timing":
        if asks_for_explanation or agrees_to_continue:
            return continuity_text(language, "timing", persisted=True)
    if focus == "qualification":
        if is_value_relevance_question(normalized):
            return value_relevance_response(language, campaign)
        if asks_for_explanation:
            if german:
                return "Einfach gesagt: RouteSignal ist nur relevant, wenn Demo-Nachfassung rutscht: verpasste Rueckrufe, unklare Besitzer oder Uebergabestatus. Was davon passiert wirklich?"
            return "In plain terms, RouteSignal is only relevant if demo follow-up is slipping: missed callbacks, unclear assignment, or missed replies. Which of those actually happens?"
        if agrees_to_continue:
            return modular_qualification_guidance_text(language, 1)
    return continuity_text(language, focus, persisted=True)


def same_focus_progression_response(
    normalized: str,
    resolved_focus: str | None,
    language: str,
    turns: list[dict],
    campaign: dict | None = None,
) -> dict | None:
    if not resolved_focus:
        return None
    selected_focus = focus_from_transcript(normalized)
    generic_progression = normalized_contains_any(
        normalized,
        {
            "tell me more",
            "more information",
            "more info",
            "what else",
            "what else should i know",
            "anything else",
            "can you explain",
            "explain more",
            "go deeper",
            "keep going",
            "why does that matter",
            "why would that matter",
            "how would it help",
            "how does that help",
            "do that",
            "let s do that",
            "lets do that",
            "go ahead",
            "okay tell me more",
        },
    )
    if selected_focus == resolved_focus or generic_progression:
        if resolved_focus == "qualification" and is_value_relevance_question(normalized):
            candidate_response = value_relevance_response(language, campaign)
        else:
            candidate_response = proactive_guidance_text(
                language,
                resolved_focus,
                max(0, focus_turn_count(turns, resolved_focus) - 1),
                campaign,
            )
        return {
            "applied": True,
            "reason": f"resolved_{resolved_focus}_focus_progressed",
            "dialogue_focus": resolved_focus,
            "candidate_response": candidate_response,
        }
    return None


def modular_qualification_guidance_text(language: str, step: int, campaign: dict | None = None) -> str:
    if is_generic_campaign_config(campaign):
        return generic_campaign_review_question(language, campaign)
    if language.startswith("de"):
        options = [
            "Die kurze Pruefung ist verpasste Nachverfolgung: Routing, Rueckrufe oder Uebergaben. Welche Luecke kostet heute die meiste Zeit?",
            "Wenn diese Luecken real sind, gibt RouteSignal Besitzer, Erinnerung und Uebergabe einen Ablauf. Welcher Teil rutscht am haeufigsten durch?",
            "Der Verkaufsgrund ist einfach: weniger verpasste Rueckrufe und klarere Besitzer. Waere eine kurze Workflow-Pruefung sinnvoll?",
        ]
        return options[step % len(options)]
    options = [
        "Thanks. Is inbound demo follow-up slipping right now?",
        "Quick check: are demo leads missing an owner or next reply right now?",
        "Is manual follow-up after demo requests slowing anyone down right now?",
        "Are callback reminders after demo requests getting missed right now?",
        "For inbound demo or trial requests, quick routing means the next reply is assigned fast. Are missed follow-ups frequent enough to check?",
        "For managers, a short workflow review shows whether inbound demo follow-up is waiting too long. Would a short workflow review be worth checking?",
    ]
    return options[step % len(options)]


def progressive_focus_text(
    language: str,
    focus: str,
    normalized: str,
    step: int,
    campaign: dict | None = None,
) -> str:
    generic = generic_campaign_focus_text(language, focus, campaign, normalized=normalized)
    if generic:
        return generic
    german = language.startswith("de")
    if focus == "qualification":
        return modular_qualification_guidance_text(language, step, campaign)
    variants = {
        "price": [
            (
                live_demo_price_answer(language)
                if not german
                else "Zum Preis kann ich nur sauber bleiben: Kosten, Bedingungen und Umfang vergleichen; genaue freigegebene Preise sollten schriftlich oder vom Spezialisten kommen."
            ),
            (
                "Starter covers basic lead capture and routing. Growth adds priority routing, reminders, and handoff review."
                if not german
                else "Die konkrete Preisfrage ist: was enthalten ist, welche Laufzeit gilt und ob der naechste Schritt unverbindlich bleibt."
            ),
            (
                "Use Starter for basic routing. Use Growth only when missed callbacks or slow handoffs cost time."
                if not german
                else "Wenn der Preis weiter der Engpass ist, wuerde ich nicht weiter verkaufen, sondern einen schriftlichen Preis- und Umfangsvergleich nutzen."
            ),
        ],
        "fit": [
            (
                "Fit depends on actual missed leads, callbacks, or handoffs. If your team is seeing that, a short review is the next step."
                if not german
                else "Bei der Passung geht es darum, ob Lead-Routing oder Nachverfolgung in Ihrem aktuellen Ablauf wirklich ein Problem ist."
            ),
            (
                "The practical fit check is whether inbound leads, callbacks, or handoffs get missed today."
                if not german
                else "Die naechste Passungsfrage ist praktisch: Bleiben heute Leads, Rueckrufe oder Uebergaben liegen?"
            ),
            (
                "If that problem is real, the next step is a short workflow review with someone from Northstar. What time works for a quick call?"
                if not german
                else "Wenn dieses Problem real ist, kann ein Spezialist die Passung pruefen; wenn nicht, gibt es keinen Grund weiterzumachen."
            ),
            (
                "If missed handoffs are real, the workflow review should focus there. What time works for a quick call?"
                if not german
                else "Die praktische Ja-Nein-Frage ist, ob verpasste Uebergaben oft genug passieren, um eine kurze Spezialistenpruefung zu rechtfertigen."
            ),
            (
                "If fit stays unclear after that, I can keep it to a written summary."
                if not german
                else "Wenn die Passung danach noch unklar ist, wuerde ich bei einer schriftlichen Zusammenfassung bleiben."
            ),
        ],
        "details": [
            (
                "The workflow scope is lead routing, follow-up, and handoff review. Exact integrations need verified checks."
                if not german
                else "Bei den Details geht es um Lead-Routing und Nachverfolgung. Genaue Integrationen sollte ein Spezialist pruefen."
            ),
            (
                "Safe product detail means scope only: routing inbound leads, follow-up work, and handoff review."
                if not german
                else "Das sichere Produktdetail ist der Umfang: Lead-Routing, Nachverfolgung und Uebergabepruefung; Integrationen sollte ich nicht erfinden."
            ),
            (
                "For details beyond that, use verified review instead of live guessing."
                if not german
                else "Wenn Sie darueber hinaus Details wollen, ist eine Spezialistenpruefung besser als Live-Raten."
            ),
        ],
        "effort": [
            (
                "The effort question is simple: would missed follow-up cost more time than a short review?"
                if not german
                else "Die Aufwandfrage ist konkret: Lohnt sich die Durchsicht nur, wenn Rueckrufe oder Nachverfolgung heute Zeit kosten?"
            ),
            (
                "If the review takes more time than the problem costs, there is no reason to push it."
                if not german
                else "Wenn die Durchsicht mehr Zeit kostet als das Problem selbst, sollte man sie nicht draengen."
            ),
            (
                "The next check is whether missed follow-up justifies even a short review."
                if not german
                else "Die naechste sinnvolle Frage ist einfach: Gibt es genug verpasste Nachverfolgung fuer eine kurze Pruefung?"
            ),
        ],
        "terms": [
            (
                "Terms should be written first: contract length, scope, and exit path. No commitment on this call."
                if not german
                else "Dann bleiben wir bei den Bedingungen: Laufzeit, Umfang und Ausstieg sollten zuerst schriftlich verglichen werden."
            ),
            (
                "The terms check comes before any decision: length, included scope, and exit path."
                if not german
                else "Die Bedingungspruefung kommt vor jeder Entscheidung: Laufzeit, Umfang und was passiert, wenn es nicht nuetzt."
            ),
        ],
        "timing": [
            (
                "No problem. We do not need to decide anything now."
                if not german
                else "Dann bleibt der Zeitpunkt der Engpass. Ich wuerde es bei schriftlicher Zusammenfassung oder spaeterem Rueckruf belassen."
            ),
            (
                "No problem. We can leave it here."
                if not german
                else "Wenn jetzt nicht der richtige Zeitpunkt ist, bleibt nur ein spaeterer Rueckruf oder eine schriftliche Zusammenfassung."
            ),
            (
                "No problem. I can keep this to a short written summary."
                if not german
                else "Die sinnvolle Zeitfrage ist, ob verpasste Nachverfolgung heute schon Zeit kostet. Wenn nicht, warten."
            ),
        ],
    }
    options = variants.get(focus) or [continuity_text(language, focus, persisted=True)]
    return options[min(step, len(options) - 1)]


def is_all_clear_or_no_pain_reply(normalized: str) -> bool:
    if not normalized:
        return False
    negative_clear_signals = {
        "not all clear",
        "not clear",
        "isn t clear",
        "isnt clear",
        "is not clear",
        "nothing is clear",
    }
    if normalized_contains_any(normalized, negative_clear_signals):
        return False
    exact_replies = {
        "all clear",
        "it s all clear",
        "its all clear",
        "it is all clear",
        "everything is clear",
        "that is clear",
        "that s clear",
        "thats clear",
        "no pain point",
        "no pain points",
        "no issue",
        "no issues",
        "no problem",
        "no problems",
        "we are good",
        "we re good",
        "were good",
    }
    if normalized in exact_replies:
        return True
    return normalized_contains_any(
        normalized,
        {
            "all clear on our side",
            "everything is clear on our side",
            "no pain point there",
            "no pain points there",
            "no real issue",
            "no real problem",
            "nothing is slipping",
            "nothing gets missed",
        },
    )


def clear_no_pain_response(language: str, campaign: dict | None = None) -> str:
    if is_generic_campaign_config(campaign):
        context = generic_campaign_context(campaign)
        if language.startswith("de"):
            return f"Verstanden. Wenn {context['gaps']} kein Thema sind, sollte ich keine Pruefung draengen. Soll ich hier stoppen?"
        return f"Got it. If {context['gaps']} are not an issue, I should not push a review. Should I stop here?"
    if language.startswith("de"):
        return "Verstanden. Wenn die Nachverfolgung klar laeuft, sollte ich keine Pruefung draengen. Bevor ich auflege: Gibt es verpasste Rueckrufe, manuelle Nachverfolgung oder Uebergaben ueberhaupt, oder ist das fuer Sie nicht relevant?"
    return (
        "Got it. If the follow-up flow is already clear, I should not push a review. "
        "Before I let you go, do missed callbacks, manual tracking, or handoffs ever create a problem, "
        "or is this not relevant for you?"
    )


def exhausted_progression_options(language: str, focus: str, campaign: dict | None = None) -> list[str]:
    generic = generic_campaign_focus_text(language, focus, campaign)
    if generic:
        return [
            generic,
            generic_campaign_next_step_text(language, campaign),
        ]
    if language.startswith("de"):
        return [
            "Dann ist der naechste sinnvolle Schritt eine kurze Zusammenfassung statt weiterer Wiederholung. Soll ich die offene Workflow-Luecke schriftlich festhalten?",
            "Um weiterzukommen, brauche ich eine konkrete Luecke: Routing, Rueckruf-Erinnerung oder Uebergabe. Welche soll ich notieren?",
        ]
    if focus == "price":
        return [
            "The price part is covered. The useful move now is choosing the gap to test: reminders, routing, or handoff review.",
            "At this point, Growth only makes sense if reminders or handoffs are a real problem. Should I keep the next step to that comparison?",
            "A short written comparison is the clean next step: Starter for basic routing, Growth for reminders and handoff review. Should I keep it that narrow?",
        ]
    if focus == "qualification":
        return [
            uncertain_gap_response(language),
            workflow_review_next_step_response(language),
            time_waste_repair_response(language),
        ]
    if focus == "fit":
        return [
            "The fit check is covered at a high level. The next useful move is one fact: do callbacks, routing, or handoffs actually slip today?",
            "If no workflow gap is happening, there is no fit. If one is happening, a short written review is enough to test it.",
        ]
    if focus == "details":
        return [
            "The safe detail is scope: routing, reminders, and handoff review. Anything beyond that needs verified review.",
            "For more detail, I should keep it narrow: which exact workflow part do you want checked in writing?",
        ]
    if focus == "timing":
        return [
            "No problem. We do not need to decide anything now.",
            "No problem. I can keep this to a short written summary.",
        ]
    if focus == "effort":
        return [
            "The effort question is covered. The next useful test is whether missed follow-up costs enough time to justify even a short review.",
            "If the time loss is unclear, stop here. If it is clear, a short workflow review is the next step.",
        ]
    return [
        "The high-level answer is covered. The useful next step is one concrete workflow gap to check.",
        workflow_review_next_step_response(language),
    ]


def unique_progressive_focus_text(
    language: str,
    focus: str,
    normalized: str,
    step: int,
    seen: set[str],
    campaign: dict | None = None,
) -> str:
    if isinstance(campaign, dict):
        campaign_options = campaign.get("focus_progression_options")
        if isinstance(campaign_options, dict):
            raw_options = campaign_options.get(focus) or campaign_options.get("default") or []
            if isinstance(raw_options, str):
                raw_options = [raw_options]
            if isinstance(raw_options, list):
                options = [str(item) for item in raw_options if str(item or "").strip()]
                for candidate in options:
                    if candidate not in seen:
                        return candidate
                if options:
                    return options[-1]
    if is_generic_campaign_config(campaign):
        options = [
            generic_campaign_focus_text(language, focus, campaign, normalized=normalized),
            generic_campaign_review_question(language, campaign),
            generic_campaign_next_step_text(language, campaign),
            "I can only keep this to the current call scope. Should I keep checking that, or stop here?"
            if not language.startswith("de")
            else "Ich kann das nur im aktuellen Anrufskontext halten. Soll ich dort weiter pruefen oder hier stoppen?",
        ]
        for candidate in options:
            if candidate and candidate not in seen:
                return candidate
        return options[-1] or generic_campaign_review_question(language, campaign)
    if focus == "qualification" and is_value_relevance_question(normalized):
        options = [
            (
                "It helps only when inbound demo follow-up has no clear owner, callback reminder, or handoff. Which one is costing time today?"
                if not language.startswith("de")
                else "Es hilft nur, wenn Demo-Nachfassung keinen klaren Besitzer, keine Rueckruf-Erinnerung oder keine saubere Uebergabe hat. Was kostet heute Zeit?"
            ),
            (
                "The useful value is not generic software; it is fewer missed demo replies, clearer owners, and cleaner handoffs. Which gap is active now?"
                if not language.startswith("de")
                else "Der Nutzen ist nicht allgemeine Software, sondern weniger verpasste Demo-Antworten, klarere Besitzer und sauberere Uebergaben. Welche Luecke ist aktiv?"
            ),
        ]
        for candidate in options:
            if candidate not in seen:
                return candidate
    for offset in range(8):
        candidate = progressive_focus_text(language, focus, normalized, step + offset, campaign)
        if candidate not in seen:
            return candidate
    for candidate in exhausted_progression_options(language, focus, campaign):
        if candidate not in seen:
            return candidate
    fallback = progressive_focus_text(language, focus, normalized, step, campaign)
    suffix = (
        " The next concrete question is whether that is worth verified review."
        if not language.startswith("de")
        else " Die naechste konkrete Frage ist, ob sich dafuer eine Spezialistenpruefung lohnt."
    )
    return fallback + suffix


def is_low_information_acknowledgement(normalized: str) -> bool:
    if not normalized:
        return False
    content_signals = {
        "price",
        "cost",
        "expensive",
        "budget",
        "fit",
        "relevant",
        "situation",
        "workflow",
        "product",
        "details",
        "terms",
        "contract",
        "security",
        "integration",
        "salesforce",
        "worth",
        "time",
        "effort",
        "what",
        "why",
        "how",
        "when",
        "where",
        "which",
        "who",
        "recommend",
    }
    if normalized_contains_any(normalized, content_signals):
        return False
    acknowledgement_words = {
        "hm",
        "hmm",
        "um",
        "uh",
        "okay",
        "ok",
        "alright",
        "all",
        "right",
        "yeah",
        "yes",
        "sure",
        "interesting",
        "that",
        "that s",
        "thats",
        "s",
        "is",
        "it",
        "sounds",
        "good",
        "guess",
    }
    words = normalized.split()
    return len(words) <= 7 and all(word in acknowledgement_words for word in words)


def selected_sales_gap_from_transcript(normalized: str) -> str | None:
    if normalized_contains_any(normalized, {"assign", "assigned", "assignment", "assigning", "owner assignment", "different person"}):
        return "routing"
    if normalized_contains_any(normalized, {"owner", "owners", "lead owner", "wrong owner", "owner routing"}):
        return "routing"
    if normalized_contains_any(normalized, {"missed callback", "missed callbacks", "callbacks happen more often", "callback happens more often"}):
        return "callbacks"
    if normalized_contains_any(
        normalized,
        {
            "leads are getting missed",
            "lead is getting missed",
            "leads getting missed",
            "lead getting missed",
            "leads get missed",
            "lead gets missed",
            "leads missing",
            "lead missing",
            "leads are missing",
            "lead is missing",
            "leads go missing",
            "lead goes missing",
            "missed leads",
            "leads are missed",
            "lead is missed",
            "leeds are getting missed",
            "leed is getting missed",
            "leeds getting missed",
            "leed getting missed",
            "leeds get missed",
            "leed gets missed",
            "leeds are missed",
            "leed is missed",
            "leads get lost",
            "lead gets lost",
            "leeds get lost",
            "leed gets lost",
            "lost in the mail",
            "lost in the mails",
            "falls through the cracks",
            "fall through the cracks",
            "falls through cracks",
            "fall through cracks",
            "we just miss it",
            "we miss it",
        },
    ):
        return "handoffs"
    if normalized_contains_any(normalized, {"handoff", "handoffs", "handoff review", "ownership", "owner changes"}):
        return "handoffs"
    if normalized_contains_any(normalized, {"callback", "callbacks", "call backs", "missed calls", "missed callbacks"}):
        return "callbacks"
    if normalized_contains_any(normalized, {"reminder", "reminders", "follow up", "follow-up", "followup"}):
        return "reminders"
    if normalized_contains_any(normalized, {"routing", "route", "assignment", "assigning", "assigned", "owner assignment"}):
        return "routing"
    if normalized_contains_any(normalized, {"duplicate", "duplicates", "duplicate checks"}):
        return "duplicates"
    if normalized_contains_any(normalized, {"visibility", "status", "reporting"}):
        return "visibility"
    return None


def seller_guided_next_step_text(language: str, gap: str) -> str:
    if language.startswith("de"):
        return "Dann ist das die konkrete Luecke. Der naechste Schritt waere eine kurze Workflow-Pruefung, keine lange Demo. Soll ich es auf genau diese Pruefung begrenzen?"
    gap_claims = {
        "handoffs": "RouteSignal helps keep the next person and next follow-up visible so demo leads do not get lost",
        "callbacks": "RouteSignal helps remind the team before demo leads wait too long",
        "reminders": "RouteSignal helps the team stop chasing follow-ups by hand",
        "routing": "RouteSignal helps each demo lead get a clear next owner faster",
        "duplicates": "RouteSignal helps keep duplicate demo leads from splitting ownership",
        "visibility": "RouteSignal helps managers see which demo leads still need follow-up",
    }
    claim = gap_claims.get(gap, "RouteSignal helps keep that follow-up gap visible")
    return (
        f"Then {claim}. I would keep the workflow review focused on that one gap. Would a short workflow review be useful for that gap?"
    )


def gap_turn_count(turns: list[dict], gap: str) -> int:
    count = 0
    for turn in turns:
        memory = turn.get("conversation_memory") or {}
        if isinstance(memory, dict) and memory.get("selected_gap") == gap:
            count += 1
            continue
        if selected_sales_gap_from_transcript(normalize_text(str(turn.get("transcript") or ""))) == gap:
            count += 1
            continue
        response = str((turn.get("summary") or {}).get("final_response") or "").lower()
        if gap == "callbacks" and ("callback reminder" in response or "missed follow-up" in response):
            count += 1
        elif gap == "handoffs" and "handoff" in response:
            count += 1
    return count


def sales_gap_from_response_text(response: str) -> str | None:
    normalized = normalize_text(response)
    if not normalized:
        return None
    if normalized_contains_any(normalized, {"callback reminder", "callback reminders", "missed callback", "missed callbacks", "missed follow up", "missed follow-up", "speed to lead"}):
        return "callbacks"
    if normalized_contains_any(normalized, {"handoff review", "handoff status", "handoff", "handoffs"}):
        return "handoffs"
    if normalized_contains_any(normalized, {"owner assignment", "assigning the reply", "assigned fast", "priority routing", "basic routing", "clear owner"}):
        return "routing"
    if normalized_contains_any(normalized, {"manual tracking", "reminder before it waits", "missed reminders", "missed reminder"}):
        return "reminders"
    return None


def appointment_gap_from_turns(turns: list[dict]) -> str | None:
    selected_gap = last_selected_gap_from_turns(turns)
    if selected_gap:
        return selected_gap
    review_signals = {
        "workflow review",
        "short check",
        "short workflow",
        "worth checking",
        "frequent enough to check",
        "useful for that gap",
        "written summary",
    }
    for response in reversed(previous_response_list(turns[-5:])):
        normalized = normalize_text(response)
        if not normalized_contains_any(normalized, review_signals):
            continue
        gap = sales_gap_from_response_text(response)
        if gap:
            return gap
    return None


def has_recent_review_next_step_question(turns: list[dict]) -> bool:
    review_question_types = {"workflow_review_next_step", "value_review_check", "summary_next_step"}
    for response in reversed(previous_response_list(turns[-4:])):
        if question_type_from_response(response) in review_question_types:
            return True
        normalized = normalize_text(response)
        if normalized_contains_any(
            normalized,
            {
                "would a short workflow review be useful",
                "would a short check be useful",
                "would a short workflow review be worth",
                "are missed follow ups frequent enough to check",
                "are missed follow-ups frequent enough to check",
                "would a short written summary help",
                "would that be useful for this gap",
                "useful for that gap",
            },
        ):
            return True
    return False


def is_affirmative_next_step_reply(normalized: str) -> bool:
    if not normalized:
        return False
    if is_previous_question_clarification_request(normalized) or "?" in normalized:
        return False
    exact_affirmatives = {
        "yes",
        "yes yes",
        "yeah",
        "yeah yeah",
        "yeah sure",
        "yep",
        "yep sure",
        "sure",
        "sure sure",
        "yes sure",
        "okay sure",
        "ok sure",
        "i guess",
        "i guess so",
        "yeah i guess",
        "yes i guess",
        "sure i guess",
        "ok",
        "okay",
        "sounds good",
        "go ahead",
        "do that",
        "lets do that",
        "let s do that",
        "yeah lets do that",
        "yeah let s do that",
        "yes lets do that",
        "yes let s do that",
        "sure lets do that",
        "sure let s do that",
        "that would help",
        "it would help",
        "yeah it would help",
        "yes it would help",
        "that would be useful",
        "it would be useful",
    }
    if normalized in exact_affirmatives:
        return True
    return normalized_contains_any(
        normalized,
        {
            "would help",
            "would be useful",
            "that helps",
            "that would work",
            "that works",
            "worth checking",
            "worth a check",
        },
    )


def is_think_about_it_reply(normalized: str) -> bool:
    if not normalized:
        return False
    return normalized_contains_any(
        normalized,
        {
            "think about it",
            "think on it",
            "need to think",
            "have to think",
            "i have to think",
            "i need to think",
            "i need more time",
            "need more time",
            "not ready to accept",
            "not ready for a quick call",
            "didn t really accept",
            "didnt really accept",
            "did not really accept",
            "didn t accept",
            "didnt accept",
            "did not accept",
            "haven t accepted",
            "havent accepted",
            "have not accepted",
        },
    )


def is_pain_confirmation_reply(normalized: str) -> bool:
    if not normalized or is_ambiguous_negative_reply(normalized):
        return False
    if normalized_contains_any(
        normalized,
        {
            "no missed",
            "not missed",
            "not getting missed",
            "nothing gets missed",
            "no issue",
            "no issues",
            "not an issue",
            "not a problem",
            "do not miss",
            "dont miss",
            "don t miss",
        },
    ):
        return False
    return normalized_contains_any(
        normalized,
        {
            "missed callback",
            "missed callbacks",
            "callback gets missed",
            "callbacks get missed",
            "manual tracking issue",
            "manual tracking issues",
            "tracking issue",
            "tracking issues",
            "they can",
            "it can",
            "they do",
            "it does",
            "that happens",
            "happens",
            "often",
            "a lot",
            "should not",
            "shouldn t",
            "shouldnt",
            "costs time",
            "slips",
            "slipping",
            "missing",
            "gets missed",
            "get missed",
            "getting missed",
            "miss it",
            "missed it",
            "falls through",
        },
    )


def should_offer_appointment_close(normalized: str, turns: list[dict]) -> tuple[bool, str | None]:
    if has_callback_scheduling_request_signal(normalized) or has_callback_time_signal(normalized):
        return False, None
    if not (is_affirmative_next_step_reply(normalized) or is_pain_confirmation_reply(normalized)):
        return False, None
    if not has_recent_review_next_step_question(turns):
        return False, None
    gap = appointment_gap_from_turns(turns) or selected_sales_gap_from_transcript(normalized)
    if not gap:
        return False, None
    previous_question_type = question_type_from_response(previous_agent_question(turns) or "")
    if previous_question_type == "permission_check":
        return False, None
    return True, gap


def pending_appointment_gap_from_turns(turns: list[dict]) -> str | None:
    for turn in reversed(turns[-3:]):
        continuity = turn.get("continuity") or {}
        if str(continuity.get("reason") or "") == "appointment_time_requested":
            gap = continuity.get("selected_gap")
            if gap:
                return str(gap)
    return None


def appointment_time_request_count(turns: list[dict]) -> int:
    return sum(
        1
        for turn in turns
        if str((turn.get("continuity") or {}).get("reason") or "") == "appointment_time_requested"
    )


def appointment_lead_close_response(language: str, gap: str | None, campaign: dict | None = None) -> str:
    if is_generic_campaign_config(campaign):
        context = generic_campaign_context(campaign)
        definition = ((campaign or {}).get("diagnostic_gaps") or {}).get(gap or "") or {}
        gap_label = str(definition.get("review_focus") or definition.get("label") or "that area").replace("_", " ")
        if language.startswith("de"):
            return (
                f"Der naechste Schritt waere eine kurze {context['target']}. "
                f"{context['owner']} kann {gap_label} mit den Details pruefen; welche Zeit passt?"
            )
        return (
            f"That sounds like the area to review, so the next step would be a short {context['target']}. "
            f"{context['owner_sentence']} can review {gap_label} against the details; what time works?"
        )
    if language.startswith("de"):
        return "Dann ist der naechste Schritt eine kurze Workflow-Pruefung mit jemandem von Northstar. Welche Zeit passt fuer einen kurzen Anruf?"
    gap_labels = {
        "callbacks": "missed callback reminders",
        "reminders": "missed reminders",
        "routing": "lead assignment",
        "handoffs": "missed demo leads",
        "duplicates": "duplicate lead handling",
        "visibility": "manager visibility",
    }
    gap_label = gap_labels.get(gap or "", "that follow-up gap")
    return (
        "That is exactly what RouteSignal is meant to help with: demo leads getting assigned, reminded, and followed up. "
        "The next step is a short workflow review with someone from Northstar. "
        f"They would check {gap_label} against your actual follow-up flow. "
        "What time works for a quick call?"
    )


def pain_review_usefulness_response(language: str, gap: str | None) -> str:
    if language.startswith("de"):
        return "Dann ist das die konkrete Luecke. Eine kurze Workflow-Pruefung mit Northstar wuerde genau diesen Ablauf gegen Ihren echten Prozess pruefen. Waere diese kurze Pruefung fuer die Luecke sinnvoll?"
    gap_labels = {
        "callbacks": "missed callback reminders",
        "reminders": "missed reminders",
        "routing": "lead assignment",
        "handoffs": "missed demo leads",
        "duplicates": "duplicate lead handling",
        "visibility": "manager visibility",
    }
    gap_label = gap_labels.get(gap or "", "that follow-up gap")
    return (
        "That sounds like the gap. RouteSignal is meant to help demo leads get assigned, reminded, and followed up. "
        f"A short workflow review with someone from Northstar would check {gap_label} against your actual follow-up flow. "
        "Would a short workflow review be useful for this gap?"
    )


def appointment_time_followup_response(language: str, gap: str | None, prior_requests: int = 0) -> str:
    if language.startswith("de"):
        if prior_requests >= 2:
            return "Ich kann die kurze Workflow-Pruefung mit jemandem von Northstar einrichten, brauche aber eine Zeit. Welche Zeit passt fuer den kurzen Anruf?"
        return "Ja. Der naechste Schritt bleibt eine kurze Workflow-Pruefung mit jemandem von Northstar. Welche Zeit passt fuer diesen kurzen Anruf?"
    gap_labels = {
        "callbacks": "missed callback reminders",
        "reminders": "missed reminders",
        "routing": "lead assignment",
        "handoffs": "missed demo leads",
        "duplicates": "duplicate lead handling",
        "visibility": "manager visibility",
    }
    gap_label = gap_labels.get(gap or "", "that follow-up gap")
    gap_clause = f" on {gap_label}" if gap else ""
    if prior_requests >= 2:
        return (
            f"I can set up that short workflow review{gap_clause} with someone from Northstar, "
            "but I need a time. What time works for the quick call?"
        )
    return (
        f"Yes. Someone from Northstar would check {gap_label} against your follow-up flow "
        "in a short workflow review. What time works for a quick call?"
    )


def appointment_time_clarification_response(language: str, gap: str | None) -> str:
    if language.startswith("de"):
        return "Naechste Woche kann funktionieren. Welcher Tag und welche Uhrzeit passen fuer die kurze Workflow-Pruefung?"
    gap_labels = {
        "callbacks": "missed callback reminders",
        "reminders": "missed reminders",
        "routing": "lead assignment",
        "handoffs": "missed demo leads",
        "duplicates": "duplicate lead handling",
        "visibility": "manager visibility",
    }
    gap_clause = f" on {gap_labels.get(gap or '', 'that follow-up gap')}" if gap else ""
    return f"Next week can work for the short workflow review{gap_clause}. Which day and time should I put down?"


def has_vague_appointment_time_signal(normalized: str) -> bool:
    if not normalized:
        return False
    vague_time = normalized_contains_any(
        normalized,
        {
            "sometime",
            "some time",
            "next week",
            "later this week",
            "this week",
            "whenever",
            "any time",
            "anytime",
            "maybe next week",
        },
    )
    if not vague_time:
        return False
    return not has_callback_time_signal(normalized)


def is_already_stated_problem_reply(normalized: str) -> bool:
    if not normalized:
        return False
    return normalized_contains_any(
        normalized,
        {
            "already told you",
            "i told you",
            "i already told you",
            "i said",
            "like i said",
            "that is what i said",
            "that s what i said",
        },
    ) and normalized_contains_any(
        normalized,
        {
            "problem",
            "lead",
            "leads",
            "manual",
            "tracking",
            "callback",
            "reminder",
            "missed",
            "missing",
        },
    )


def already_stated_problem_response(language: str, gap: str | None) -> str:
    if language.startswith("de"):
        return "Stimmt, Sie haben das Problem schon genannt. Ich sollte es nicht wiederholen. Welche Zeit passt fuer eine kurze Workflow-Pruefung mit Northstar?"
    gap_labels = {
        "callbacks": "callback reminders",
        "reminders": "manual reminders",
        "routing": "assigning the next follow-up",
        "handoffs": "demo leads getting missed",
        "duplicates": "duplicate lead handling",
        "visibility": "seeing which leads still need follow-up",
    }
    gap_label = gap_labels.get(gap or "", "demo leads slipping")
    return (
        f"You already told me the problem: {gap_label}. I should not ask you to repeat it. "
        "The useful next step is a short workflow review with someone from Northstar. "
        "What time works for a quick call?"
    )


def appointment_value_clarification_response(language: str, gap: str | None) -> str:
    if language.startswith("de"):
        return "Sinnvoll ist es nur, wenn diese Luecke wirklich Nachfassung verlangsamt. Jemand von Northstar wuerde das in einer kurzen Workflow-Pruefung gegen Ihren Ablauf pruefen. Welche Zeit passt fuer den kurzen Anruf?"
    gap_labels = {
        "callbacks": "missed callback reminders",
        "reminders": "missed reminders",
        "routing": "lead assignment",
        "handoffs": "missed demo leads",
        "duplicates": "duplicate lead handling",
        "visibility": "manager visibility",
    }
    gap_label = gap_labels.get(gap or "", "that follow-up gap")
    return (
        f"It would help only if {gap_label} are really slowing follow-up. "
        "Someone from Northstar would check that in a short workflow review against your actual flow. "
        "If that is worth testing, what time works for a quick call?"
    )


def has_appointment_time_confirmation_signal(normalized: str, session_state: dict | None = None) -> bool:
    if not has_callback_time_signal(normalized):
        return False
    turns = list((session_state or {}).get("turns") or [])
    for turn in reversed(turns[-3:]):
        continuity = turn.get("continuity") or {}
        if str(continuity.get("reason") or "") == "appointment_time_requested":
            return True
    return False


def gap_progression_text(language: str, gap: str, step: int, seen: set[str] | None = None) -> str:
    seen = seen or set()
    if language.startswith("de"):
        return seller_guided_next_step_text(language, gap)
    variants = {
        "callbacks": [
            seller_guided_next_step_text(language, "callbacks"),
            "For callbacks, the issue is speed to lead: each demo request has an owner and reminder before it waits. Would a short workflow review help check missed reminders?",
            "Since missed callbacks are the gap, the useful next step is a short workflow review with someone from Northstar. Would a short workflow review be useful for this gap?",
            "The useful next step is checking who owns the lead, when the next callback is due, and whether the reply happened. Would a short workflow review help you judge fit?",
        ],
        "handoffs": [
            seller_guided_next_step_text(language, "handoffs"),
            "For handoffs, the value is handoff review: owner, next callback, and manager visibility stay together. I would keep the short workflow review to handoff misses. Would a short workflow review be useful for that gap?",
            "If owner, next callback, or manager visibility slips, a short workflow review has a reason. Which part breaks most often?",
        ],
        "routing": [
            seller_guided_next_step_text(language, "routing"),
            "For routing, the value is clear ownership before follow-up waits. I would keep the review to owner assignment. Would a short workflow review be useful for that gap?",
        ],
        "reminders": [
            seller_guided_next_step_text(language, "reminders"),
            "For reminders, the value is fewer manual chases after inbound demos. I would keep the review to missed reminder count. Would a short workflow review be useful for that gap?",
        ],
    }
    options = variants.get(gap) or [seller_guided_next_step_text(language, gap), workflow_review_next_step_response(language)]
    for offset in range(len(options)):
        candidate = options[(step + offset) % len(options)]
        if candidate not in seen:
            return candidate
    return options[step % len(options)] + " The next useful check is whether that gap is worth verified review."


def proactive_guidance_text(language: str, focus: str, step: int, campaign: dict | None = None) -> str:
    generic = generic_campaign_focus_text(language, focus, campaign)
    if generic:
        return generic
    german = language.startswith("de")
    if focus == "qualification":
        return modular_qualification_guidance_text(language, step, campaign)
    variants = {
        "price": [
            (
                "Value matters only if missed callbacks cost time. Which gap is costing you more today: routing, reminders, or handoffs?"
                if not german
                else "Der Wert ist nicht der Preis selbst. Growth lohnt sich nur, wenn verpasste Rueckrufe Zeit kosten: Routing, Erinnerungen und Uebergabepruefung reduzieren Nacharbeit."
            ),
            (
                "Starter is enough for basic routing. Which part needs more control today: reminders, duplicate checks, or handoff review?"
                if not german
                else "Starter reicht fuer einfaches Routing. Growth ist sinnvoll, wenn Erinnerungen und Uebergabepruefung verlorene Nachverfolgung verhindern."
            ),
            (
                "If callbacks or handoffs are slipping, Growth has a workflow reason. Which one happens more often?"
                if not german
                else "Die einfache Pruefung ist: gehen Rueckrufe oder Uebergaben heute verloren? Wenn ja, hat Growth einen echten Workflow-Grund."
            ),
        ],
        "fit": [
            (
                "If leads or callbacks are clean today, stop here. If they slip, RouteSignal gives the team one workflow for routing and follow-up."
                if not german
                else "Wenn Leads und Rueckrufe heute sauber laufen, stoppen wir hier. Wenn sie liegen bleiben, klaert RouteSignal Routing und Nachverfolgung in einem Ablauf."
            ),
            (
                "The practical point is consistency: demo leads get assigned, reminded, and followed up instead of being chased by hand."
                if not german
                else "Der Nutzen ist Konsistenz: Besitzerzuordnung, Erinnerungen und Uebergabestatus machen verpasste Nachverfolgung sichtbar."
            ),
            (
                "The fit question is practical: does the team lose leads because nobody owns the next step quickly enough?"
                if not german
                else "Die Passungsfrage ist praktisch: verliert das Team Leads, weil die naechste Aktion nicht schnell genug zugeordnet wird?"
            ),
        ],
        "details": [
            (
                "The practical workflow is capture the demo lead, assign the next person, remind them, and check whether the reply happened. That is the part worth checking before integration details."
                if not german
                else "Der praktische Ablauf ist Erfassen, Routen, Erinnern und Uebergaben pruefen. Das sollte vor Integrationsdetails geklaert werden."
            ),
            (
                "RouteSignal is strongest when handoffs get messy: it keeps the lead, next action, and owner status in one place."
                if not german
                else "RouteSignal ist am staerksten, wenn Uebergaben unklar werden: Lead, naechste Aktion und Besitzerstatus bleiben an einem Ort."
            ),
            (
                "Feature-wise, the core is routing, reminders, duplicate checks, Slack alerts, and handoff review."
                if not german
                else "Bei den Funktionen geht es um Routing, Erinnerungen, Dublettenpruefung, Slack-Hinweise und Uebergabepruefung."
            ),
        ],
        "effort": [
            (
                "The product only earns attention if missed follow-up costs time. If it does, a short workflow review can show whether Growth helps."
                if not german
                else "Das Produkt verdient nur Aufmerksamkeit, wenn verpasste Nachverfolgung Zeit kostet. Dann kann eine kurze Workflow-Pruefung Growth bewerten."
            ),
            (
                "The useful next step is not a long demo. It is checking whether lost callbacks or handoffs happen often enough to matter."
                if not german
                else "Der sinnvolle naechste Schritt ist keine lange Demo. Es geht darum, ob verlorene Rueckrufe oder Uebergaben oft genug passieren."
            ),
            (
                "If the time loss is real, the product gives structure to follow-up. If it is not real, I would not push it."
                if not german
                else "Wenn der Zeitverlust real ist, strukturiert das Produkt die Nachverfolgung. Wenn nicht, wuerde ich nicht draengen."
            ),
        ],
        "terms": [
            (
                "The safe sales path is written terms first: scope, contract length, and exit path. Then the price is easier to judge."
                if not german
                else "Der sichere Verkaufsweg sind zuerst schriftliche Bedingungen: Umfang, Laufzeit und Ausstieg. Dann ist der Preis besser bewertbar."
            )
        ],
        "timing": [
            (
                "If now is early, keep it simple: send the workflow summary and revisit only if missed follow-up is costing time."
                if not german
                else "Wenn es jetzt zu frueh ist, bleibt es einfach: Workflow-Zusammenfassung senden und nur bei echtem Nachverfolgungsproblem spaeter pruefen."
            ),
            (
                "No decision needs to happen now. The useful move is a later callback if routing or reminders are already a problem."
                if not german
                else "Jetzt muss nichts entschieden werden. Sinnvoll ist ein spaeterer Rueckruf, wenn Routing oder Erinnerungen schon ein Problem sind."
            ),
            (
                "If the team is busy, I would keep this to a short written summary and revisit when follow-up gaps are measurable."
                if not german
                else "Wenn das Team gerade ausgelastet ist, bleibt es bei einer kurzen Zusammenfassung und spaeterer Pruefung messbarer Luecken."
            ),
        ],
    }
    options = variants.get(focus) or [continuity_text(language, focus, persisted=True)]
    return options[min(step, len(options) - 1)]


def duplicate_response_repair(
    transcript: str,
    session_state: dict | None,
    language: str,
    generated_response: str,
    campaign: dict | None = None,
) -> dict:
    turns = list((session_state or {}).get("turns") or [])
    response = generated_response.strip()
    if not response or response not in previous_responses(turns):
        return {"applied": False, "reason": "no_duplicate_response_detected"}
    normalized = normalize_text(transcript)
    if is_generic_campaign_config(campaign) and (
        is_tentative_permission_reply(normalized) or is_uncertain_qualification_reply(normalized)
    ):
        return {
            "applied": True,
            "reason": "generic_uncertainty_duplicate_repaired",
            "dialogue_focus": "qualification",
            "candidate_response": uncertain_qualification_response(language, campaign),
        }
    if callback_semantic_from_transcript(normalized, session_state) == CALLBACK_SCHEDULING_REQUEST:
        return {
            "applied": True,
            "reason": "callback_request_time_needed",
            "dialogue_focus": "timing",
            "callback_semantic": CALLBACK_SCHEDULING_REQUEST,
            "candidate_response": callback_request_time_response_for_transcript(language, normalized),
        }
    focus = focus_from_transcript(normalized) or dialogue_focus_from_turns(turns)
    if focus:
        return {
            "applied": True,
            "reason": f"duplicate_response_prevented_with_{focus}_progression",
            "dialogue_focus": focus,
            "candidate_response": unique_progressive_focus_text(
                language,
                focus,
                normalized,
                focus_turn_count(turns, focus),
                previous_responses(turns),
                campaign,
            ),
        }
    text = (
        "I already answered that at a high level. Give me one concrete follow-up and I will answer that directly."
        if not language.startswith("de")
        else "Das habe ich auf hoher Ebene bereits beantwortet. Nennen Sie eine konkrete Folgefrage, dann antworte ich direkt darauf."
    )
    return {
        "applied": True,
        "reason": "duplicate_response_prevented_without_clear_focus",
        "candidate_response": text,
    }


def is_previous_question_clarification_request(normalized: str) -> bool:
    if not normalized:
        return False
    return normalized_contains_any(
        normalized,
        {
            "did not understand",
            "didnt understand",
            "didn t understand",
            "do not understand",
            "dont understand",
            "don t understand",
            "did not get",
            "didnt get",
            "didn t get",
            "did not catch",
            "didnt catch",
            "didn t catch",
            "what do you mean",
            "what did you mean",
            "what were you asking",
            "what are you asking",
            "what was the question",
            "what question",
            "asked before",
            "before that",
            "can you explain your question",
            "explain your question",
            "repeat the question",
            "say that again",
            "say it again",
            "clarify that",
            "clarify your question",
            "who is harder",
            "what is harder",
            "which is harder",
            "which one is harder",
            "which part is harder",
            "who harder",
            "what harder",
            "harder who",
            "harder what",
        },
    )


def is_tentative_permission_reply(normalized: str) -> bool:
    return normalized in {
        "maybe",
        "maybe yes",
        "maybe sure",
        "i guess",
        "i guess so",
        "possibly",
        "perhaps",
        "not sure",
        "i am not sure",
        "i m not sure",
        "im not sure",
        "not familiar",
        "not really familiar",
        "not familiar to me",
        "they are not familiar to me",
        "they re not familiar to me",
        "they re not really familiar to me",
        "theyre not familiar to me",
        "theyre not really familiar to me",
    }


def is_uncertain_qualification_reply(normalized: str) -> bool:
    return normalized in {
        "i do not know",
        "i don t know",
        "i dont know",
        "i don t really know",
        "i dont really know",
        "i do not really know",
        "no idea",
        "i have no idea",
        "not sure",
        "i am not sure",
        "i m not sure",
        "im not sure",
    }


def plain_qualification_term_clarification_text(language: str, normalized: str) -> str | None:
    if language.startswith("de"):
        return None
    if not (
        is_previous_question_clarification_request(normalized)
        or normalized_contains_any(normalized, {"what is", "what are", "meaning of", "mean by", "means by"})
    ):
        return None
    if normalized_contains_any(normalized, {"shared inbox", "shared inbox lead", "shared inbox leads"}):
        return (
            "A shared inbox means one place where several people see the same lead emails or demo requests. "
            "The risk is simple: two people assume someone else will reply. Is that close to how your team handles new requests?"
        )
    if normalized_contains_any(normalized, {"owner", "ownership", "own the next", "owns the next"}):
        return (
            "By that, I mean the person responsible for the next reply. "
            "The check is whether a new demo request always has one clear person following up."
        )
    if normalized_contains_any(normalized, {"handoff", "handoffs"}):
        return (
            "A handoff is when a request moves from one person or team to another. "
            "The problem is when the next reply gets lost during that move."
        )
    if normalized_contains_any(normalized, {"callback", "callbacks"}):
        return callback_workflow_clarification_response(language)
    return None


def generic_account_support_request(normalized: str) -> bool:
    return normalized_contains_any(
        normalized,
        {
            "password",
            "reset password",
            "account access",
            "help with my account",
            "help with my password",
            "support ticket",
            "handle my claim",
            "help with my claim",
            "claim status",
            "change my plan",
            "change the plan",
            "check my warranty",
            "warranty status",
            "help with my order",
            "where is my order",
            "order status",
            "cancel my account",
            "cancel account",
            "cancel my subscription",
            "cancel subscription",
        },
    )


def generic_account_support_boundary_text(language: str, campaign: dict | None) -> str:
    if language.startswith("de"):
        return "Dabei kann ich in diesem Anruf nicht helfen. Bitte nutzen Sie den zustaendigen Support; ich kann hier stoppen."
    context = generic_campaign_context(campaign)
    vertical = str((campaign or {}).get("vertical_id") or "")
    if not is_generic_campaign_config(campaign):
        return "I cannot help with password or account support on this call. I can keep this to the workflow review topic, or stop here."
    if vertical == "insurance":
        return "I cannot handle claim support on this call. Please use the authorized support path; I can keep this to the review topic, or stop here."
    if vertical == "telecom":
        return "I cannot change account plans on this call. Please use the authorized support path; I can keep this to the review topic, or stop here."
    if vertical == "automotive_service":
        return "I cannot check warranty support on this call. Please use the authorized support path; I can keep this to the review topic, or stop here."
    if vertical == "membership_or_subscription":
        return "I cannot cancel or change an account on this call. Please use authorized account support; I can stop here."
    if vertical == "retail_or_ecommerce_support_sales":
        return "I cannot handle order support on this call. Please use the support team for order details; I can stop here."
    return (
        "I cannot help with account support on this call. "
        f"If useful, {context['owner_phrase']} can follow up separately, or I can stop here."
    )


def tentative_qualification_response(language: str, campaign: dict | None = None) -> str:
    if is_generic_campaign_config(campaign):
        context = generic_campaign_context(campaign)
        if language.startswith("de"):
            return (
                f"Kein Problem. Wenn {context['gaps']} nicht klar sind, "
                "kann ich eine einfache Frage stellen oder hier stoppen."
            )
        return "No problem. Should I ask one simpler yes-or-no question, or stop here?"
    if language.startswith("de"):
        return "Kein Problem. Ich erklaere es kurz: Es geht darum, ob eine Demo-Anfrage schnell eine zustaendige Person und eine naechste Antwort bekommt."
    return (
        "No problem. I mean inbound leads where someone asks for a demo or more information. "
        "The simple check is whether one person is clearly responsible for the next reply. Does that ever get fuzzy?"
    )


def uncertain_qualification_response(language: str, campaign: dict | None = None) -> str:
    if is_generic_campaign_config(campaign):
        context = generic_campaign_context(campaign)
        if language.startswith("de"):
            return "Kein Problem. Wenn Sie nicht sicher sind, kann ich es klarer eingrenzen oder hier stoppen."
        return "No problem. Should I simplify the question, or stop here?"
    if language.startswith("de"):
        return "Kein Problem. Starten wir einfacher: Wenn jemand eine Demo anfragt, wer stellt sicher, dass die naechste Antwort passiert?"
    return "No problem. Start with one simple case: when someone asks for a demo, who makes sure they get the next reply?"


def previous_agent_question(turns: list[dict]) -> str | None:
    for turn in reversed(turns):
        response = str((turn.get("summary") or {}).get("final_response") or "").strip()
        if "?" in response:
            return response
    return None


def clarify_previous_question_text(
    language: str,
    focus: str,
    previous_question: str | None,
    campaign: dict | None = None,
) -> str:
    del previous_question
    generic = generic_campaign_focus_text(language, focus, campaign)
    if generic:
        return generic
    if language.startswith("de"):
        if focus == "price":
            return "Ich meinte: Der Preis zaehlt nur bei einer echten Ablauf-Luecke. Welche Luecke kostet Zeit: Rueckrufe, Routing oder Uebergaben?"
        return "Ich fragte nach verpassten Rueckrufen, unklaren Besitzern oder Uebergaben im Demo-Ablauf. Welcher Teil rutscht zuerst durch?"
    if focus == "price":
        return "I meant price should connect to a real workflow gap. In plain terms, are missed callbacks, routing delays, or handoffs frequent enough to justify Growth?"
    if focus == "fit":
        return "I meant fit depends on a real follow-up gap. In plain terms, which part slips today: inbound leads, callbacks, or handoffs?"
    if focus == "details":
        return "I meant the workflow part, not a generic feature list. In plain terms, which part matters most: routing, reminders, handoff review, or visibility?"
    if focus == "timing":
        return "I meant timing only matters if follow-up gaps are already costing time. In plain terms, should I keep this to a callback later?"
    if focus == "effort":
        return "I meant effort is worth it only if missed follow-up costs time. In plain terms, which gap wastes time: callbacks, routing, or handoffs?"
    return "I meant: an inbound demo request needs one clear owner for the next reply. Can owner, callback, or handoff steps sit waiting?"


def is_ambiguous_negative_reply(normalized: str) -> bool:
    if not normalized:
        return False
    return normalized in {
        "no",
        "nope",
        "nah",
        "not really",
        "i do not think so",
        "i dont think so",
        "don t think so",
        "i m not sure",
        "im not sure",
    }


def ambiguous_negative_clarification_text(
    language: str,
    focus: str,
    previous_question: str | None,
    campaign: dict | None = None,
) -> str:
    del focus, previous_question
    if is_generic_campaign_config(campaign):
        context = generic_campaign_context(campaign)
        if language.startswith("de"):
            return f"Kein Problem. Meinen Sie, jetzt passt es nicht, oder sind {context['gaps']} kein Thema?"
        return f"No problem. Do you mean now is not a good time, or that {context['gaps']} are not an issue?"
    if language.startswith("de"):
        return "Kein Problem. Meinen Sie, jetzt passt es nicht, oder sind verpasste Rueckrufe und Uebergaben kein Thema?"
    return "No problem. Do you mean now is not a good time, or that missed callbacks and handoffs are not an issue?"


def current_focus_followup_response(
    normalized: str,
    resolved_focus: str | None,
    language: str,
    turns: list[dict] | None = None,
    campaign: dict | None = None,
) -> dict | None:
    if not resolved_focus:
        return None
    turns = list(turns or [])
    prior_question = previous_agent_question(turns)
    if prior_question and is_all_clear_or_no_pain_reply(normalized):
        return {
            "applied": True,
            "reason": "clear_no_pain_acknowledged",
            "dialogue_focus": resolved_focus,
            "candidate_response": clear_no_pain_response(language, campaign),
        }
    if resolved_focus == "qualification":
        term_clarification = plain_qualification_term_clarification_text(language, normalized)
        if term_clarification:
            return {
                "applied": True,
                "reason": "plain_qualification_term_clarified",
                "dialogue_focus": "qualification",
                "candidate_response": term_clarification,
            }
        if is_tentative_permission_reply(normalized):
            return {
                "applied": True,
                "reason": "plain_qualification_context_after_tentative_reply",
                "dialogue_focus": "qualification",
                "candidate_response": tentative_qualification_response(language, campaign),
            }
        if is_uncertain_qualification_reply(normalized):
            return {
                "applied": True,
                "reason": "plain_qualification_recovered_after_uncertainty",
                "dialogue_focus": "qualification",
                "candidate_response": uncertain_qualification_response(language, campaign),
            }
    if prior_question and is_previous_question_clarification_request(normalized):
        return {
            "applied": True,
            "reason": "previous_question_clarified",
            "dialogue_focus": resolved_focus,
            "candidate_response": clarify_previous_question_text(language, resolved_focus, prior_question, campaign),
        }
    if prior_question and is_ambiguous_negative_reply(normalized):
        return {
            "applied": True,
            "reason": "ambiguous_negative_clarified",
            "dialogue_focus": resolved_focus,
            "candidate_response": ambiguous_negative_clarification_text(language, resolved_focus, prior_question, campaign),
        }
    call_context_recovery = call_context_recovery_response(normalized, resolved_focus, language, campaign)
    if call_context_recovery:
        return call_context_recovery
    selected_gap = selected_sales_gap_from_transcript(normalized)
    if selected_gap and resolved_focus in {"price", "fit", "details", "effort", "qualification"}:
        if is_pain_confirmation_reply(normalized):
            return {
                "applied": True,
                "reason": "appointment_time_requested",
                "dialogue_focus": "timing",
                "selected_gap": selected_gap,
                "candidate_response": appointment_lead_close_response(language, selected_gap),
            }
        return {
            "applied": True,
            "reason": f"seller_gap_selected_for_{resolved_focus}",
            "dialogue_focus": resolved_focus,
            "selected_gap": selected_gap,
            "candidate_response": gap_progression_text(
                language,
                selected_gap,
                gap_turn_count(turns, selected_gap),
                previous_responses(turns),
            ),
        }
    if is_low_information_acknowledgement(normalized):
        return {
            "applied": True,
            "reason": f"proactive_{resolved_focus}_guidance_after_acknowledgement",
            "dialogue_focus": resolved_focus,
            "candidate_response": proactive_guidance_text(
                language,
                resolved_focus,
                max(0, focus_turn_count(turns, resolved_focus) - 1),
                campaign,
            ),
        }
    continuation_signals = {
        "do that",
        "lets do that",
        "let s do that",
        "all right",
        "okay",
        "ok",
        "yes",
        "sure",
        "sounds good",
        "go ahead",
        "explain",
        "explain that",
        "explain to me",
        "tell me",
        "what does",
        "what is",
        "what s",
        "what would",
        "what else",
        "what else should i know",
        "how does",
        "include",
        "includes",
        "workflow include",
        "workflow includes",
        "workflow",
        "tell me more",
        "more information",
        "more info",
        "anything else",
        "recommend",
        "what do you recommend",
        "what should i choose",
        "why does that matter",
        "why would that matter",
        "how would it help",
        "how does that help",
    }
    if not normalized_contains_any(normalized, continuation_signals):
        return None
    if isinstance(campaign, dict):
        campaign_options = campaign.get("focus_progression_options")
        if isinstance(campaign_options, dict):
            raw_options = campaign_options.get(resolved_focus) or campaign_options.get("default") or []
            if isinstance(raw_options, str):
                raw_options = [raw_options]
            if isinstance(raw_options, list):
                options = [str(item) for item in raw_options if str(item or "").strip()]
                if options:
                    return {
                        "applied": True,
                        "reason": f"campaign_{resolved_focus}_focus_followup",
                        "dialogue_focus": resolved_focus,
                        "candidate_response": options[0],
                    }
    progression = same_focus_progression_response(normalized, resolved_focus, language, turns, campaign)
    if progression:
        return progression
    return {
        "applied": True,
        "reason": f"resolved_{resolved_focus}_focus_followup",
        "dialogue_focus": resolved_focus,
        "candidate_response": focus_followup_text(language, resolved_focus, normalized, campaign),
    }


def focus_from_transcript(normalized: str) -> str | None:
    price_deferred = normalized_contains_any(
        normalized,
        {
            "price later",
            "price later on",
            "talk about the price later",
            "talk about price later",
        },
    )
    if normalized in {"price", "the price", "cost", "costs", "money", "monthly price", "preis", "kosten"}:
        return "price"
    if normalized in {"terms", "contract terms", "conditions", "bedingungen", "vertragsbedingungen"}:
        return "terms"
    if normalized in {"effort", "worth it", "worth the effort", "time", "aufwand", "lohnt sich", "zeit"}:
        return "effort"
    if normalized in {"fit", "relevance", "relevant", "if it fits", "passung", "passt"}:
        return "fit"
    if normalized in {"timing", "later", "not now", "time", "zeitpunkt", "spaeter"}:
        return "timing"
    if normalized in {"details", "product details", "exact details", "plan details", "details first", "features", "feature", "produktdetails"}:
        return "details"
    if normalized_contains_any(
        normalized,
        {
            "worth my time",
            "worth the time",
            "worth my effort",
            "worth the effort",
            "reviewing options is worth",
            "viewing options is worth",
            "whether reviewing",
            "whether a viewing",
            "if this is worth",
            "if it is worth",
        },
    ):
        return "effort"
    if normalized_contains_any(
        normalized,
        {
            "start with the price",
            "start with price",
            "about price",
            "about the price",
            "talk about the price",
            "talk about price",
            "the price is the problem",
            "price is the problem",
            "main concern is price",
            "price first",
            "cost first",
            "monthly price",
            "too expensive",
            "expensive",
            "budget",
            "price concern",
        },
    ) and not price_deferred:
        return "price"
    if normalized_contains_any(
        normalized,
        {
            "contract terms",
            "the terms",
            "terms first",
            "conditions first",
            "main concern is terms",
        },
    ):
        return "terms"
    if normalized_contains_any(
        normalized,
        {
            "talk about the fit",
            "talk about fit",
            "the fit",
            "fit is good",
            "if the fit is good",
            "whether it fits",
            "if it fits",
            "fit our workflow",
            "fits our workflow",
            "fit my situation",
            "relevant for my situation",
            "relevant for the situation",
            "relevant for us",
            "my situation",
            "the situation",
            "relevant for us",
            "relevant to us",
        },
    ):
        return "fit"
    if normalized_contains_any(
        normalized,
        {
            "not now",
            "call me later",
            "callback later",
            "timing first",
            "timing is my concern",
            "concern is timing",
            "talk about timing",
            "about timing",
            "bad timing",
            "need time",
            "still need time",
        },
    ):
        return "timing"
    if normalized_contains_any(
        normalized,
        {
            "what does your product",
            "what does the product",
            "what do you do",
            "what does it do",
            "what is your product",
            "product actually do",
            "exact product details",
            "product details",
            "plan details",
            "features",
            "feature",
            "talk about the features",
            "talk about features",
            "product features",
            "what is included",
            "workflow includes",
            "workflow include",
            "what does the workflow",
            "what does workflow",
            "details first",
        },
    ):
        return "details"
    return None


def response_hash(text: str) -> str:
    if not text:
        return ""
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()[:16]


def response_subject(text: str) -> str:
    normalized = normalize_text(text)
    if not normalized:
        return "empty"
    if normalized_contains_any(normalized, {"do you have a minute", "worth a quick check"}):
        return "opening_permission"
    if normalized_contains_any(normalized, {"starter", "growth"}):
        if normalized_contains_any(normalized, {"29 month", "59 month", "$29", "$59"}):
            return "price_plan_summary"
        if normalized_contains_any(normalized, {"reminders", "handoff review", "basic routing"}):
            return "plan_boundary"
    if normalized_contains_any(normalized, {"callback reminders", "missed callbacks", "callback gap", "callback visibility"}):
        return "callback_workflow"
    if normalized_contains_any(normalized, {"handoff review", "handoff status", "handoffs"}):
        return "handoff_workflow"
    if normalized_contains_any(normalized, {"owner routing", "owner assignment", "priority routing", "basic routing"}):
        return "routing_workflow"
    if normalized_contains_any(normalized, {"workflow review", "written summary", "short summary", "verified review"}):
        return "safe_next_step"
    if normalized_contains_any(normalized, {"which gap", "which part", "where does", "which one", "what time"}):
        return "diagnostic_question"
    if normalized_contains_any(normalized, {"fit depends", "practical fit", "real workflow gap"}):
        return "fit_boundary"
    if normalized_contains_any(normalized, {"security", "soc 2", "integration", "specialist"}):
        return "verified_review_boundary"
    return f"general:{response_hash(normalized)}"


def response_signature(text: str) -> str:
    return f"{response_subject(text)}:{response_hash(text)}"


def previous_response_signatures(turns: list[dict], candidate_response: str | None = None) -> list[str]:
    signatures = [response_signature(response) for response in previous_response_list(turns)]
    if candidate_response:
        signatures.append(response_signature(candidate_response))
    return [signature for signature in signatures if signature]


def previous_response_subjects(turns: list[dict], candidate_response: str | None = None) -> list[str]:
    subjects = [response_subject(response) for response in previous_response_list(turns)]
    if candidate_response:
        subjects.append(response_subject(candidate_response))
    return [subject for subject in subjects if subject and subject != "empty"]


def last_selected_gap_from_turns(turns: list[dict]) -> str | None:
    for turn in reversed(turns):
        continuity = turn.get("continuity") or {}
        memory = turn.get("conversation_memory") or {}
        turn_transcript = normalize_text(str(turn.get("transcript") or ""))
        pragmatic_move = turn.get("dialogue_pragmatics") or (turn.get("dialogue_manager") or {}).get("pragmatic_move") or {}
        pragmatic_move_id = str(pragmatic_move.get("move_id") or "")
        transcript_can_select_gap = pragmatic_move_id not in {
            "call_purpose_question",
            "previous_question_clarification",
            "term_or_context_unfamiliarity",
            "term_meaning_question",
            "relevance_challenge",
            "agent_should_lead",
            "crm_replacement_question",
        }
        for value in [
            memory.get("selected_gap") if isinstance(memory, dict) else None,
            continuity.get("selected_gap"),
            continuity.get("dialogue_focus") if str(continuity.get("dialogue_focus") or "") in {"callbacks", "handoffs", "routing", "reminders", "duplicates", "visibility"} else None,
            None
            if is_starter_growth_plan_boundary_question(turn_transcript) or not transcript_can_select_gap
            else selected_sales_gap_from_transcript(turn_transcript),
        ]:
            if value:
                return str(value)
    return None


def question_type_from_response(response: str) -> str:
    normalized = normalize_text(response)
    if "?" not in response:
        return "none"
    if normalized_contains_any(normalized, {"person from northstar", "someone from northstar", "quick call", "what time works"}):
        return "appointment_time"
    if normalized_contains_any(normalized, {"what time", "when should", "callback time", "note for the callback"}):
        return "callback_time"
    if normalized_contains_any(normalized, {"which part slips", "which part needs"}):
        return "qualification_gap_diagnostic"
    if normalized_contains_any(normalized, {"which of those creates", "which of those"}):
        return "call_purpose_gap_diagnostic"
    if normalized_contains_any(normalized, {"which gap should i keep", "should i keep this focused", "should i keep the review"}):
        return "focus_scope_question"
    if normalized_contains_any(normalized, {"which gap costs", "which one creates", "which one happens", "which handoff breaks"}):
        return "comparative_gap_diagnostic"
    if normalized_contains_any(normalized, {"where does follow up break", "where does follow-up break", "where does that break"}):
        return "workflow_breakpoint_question"
    if normalized_contains_any(normalized, {"which gap", "which part", "which one", "where does", "where is", "where do"}):
        return "gap_diagnostic"
    if normalized_contains_any(normalized, {"should i stop", "should i end", "stop here"}):
        return "permission_to_stop"
    if normalized_contains_any(normalized, {"do you have a minute", "is now a bad time", "quick question"}):
        return "permission_check"
    if normalized_contains_any(normalized, {"do you mean", "are you saying"}):
        return "clarification"
    if normalized_contains_any(normalized, {"should the review test", "focus only on that gap", "test missed reminder", "test handoff"}):
        return "gap_scope_check"
    if normalized_contains_any(normalized, {"worth reviewing", "worth verified review", "worth a review"}):
        return "value_review_check"
    if normalized_contains_any(normalized, {"short summary", "would that help you judge", "written summary"}):
        return "summary_next_step"
    if normalized_contains_any(normalized, {"would a short", "would that be useful for this gap", "workflow review", "short workflow"}):
        return "workflow_review_next_step"
    if response_reopens_focus_menu(response):
        return "generic_focus_menu"
    return "sales_progression_question"


def response_question_counts(turns: list[dict], candidate_response: str | None = None) -> dict[str, int]:
    counts: dict[str, int] = {}
    responses = [str((turn.get("summary") or {}).get("final_response") or "") for turn in turns]
    if candidate_response:
        responses.append(candidate_response)
    for response in responses:
        question_type = question_type_from_response(response)
        counts[question_type] = counts.get(question_type, 0) + 1
    return counts


def answered_topics_from_turns(turns: list[dict], normalized: str, active_topic: str | None, selected_gap: str | None) -> list[str]:
    topics: set[str] = set()
    for turn in turns:
        summary = turn.get("summary") or {}
        continuity = turn.get("continuity") or {}
        for value in [summary.get("sales_difficulty"), continuity.get("dialogue_focus")]:
            if value:
                text = str(value)
                if text in {"price", "fit", "details", "timing", "effort", "terms", "qualification"}:
                    topics.add(text)
        turn_transcript = normalize_text(str(turn.get("transcript") or ""))
        gap = None if is_starter_growth_plan_boundary_question(turn_transcript) else selected_sales_gap_from_transcript(turn_transcript)
        if gap:
            topics.add(gap)
        if is_starter_growth_plan_boundary_question(turn_transcript) or str(continuity.get("reason") or "") == "plan_boundary":
            topics.add("plan_boundary")
    current_gap = None if is_starter_growth_plan_boundary_question(normalized) else selected_sales_gap_from_transcript(normalized)
    for value in [active_topic, selected_gap, current_gap]:
        if value:
            topics.add(str(value))
    if is_starter_growth_plan_boundary_question(normalized):
        topics.add("plan_boundary")
    return sorted(topics)


def rejected_topics_from_transcript(normalized: str, active_topic: str | None, selected_gap: str | None) -> list[str]:
    if not is_ambiguous_negative_reply(normalized):
        return []
    return sorted({value for value in [active_topic, selected_gap] if value})


def last_customer_intent_from_transcript(normalized: str, callback_semantic: str | None, active_topic: str | None) -> str:
    if callback_semantic:
        return callback_semantic
    if is_starter_growth_plan_boundary_question(normalized):
        return "plan_boundary_question"
    if is_affirmative_next_step_reply(normalized):
        return "affirm_next_step"
    if is_low_information_acknowledgement(normalized):
        return "low_information_acknowledgement"
    if is_previous_question_clarification_request(normalized):
        return "clarify_previous_question"
    if is_ambiguous_negative_reply(normalized):
        return "ambiguous_negative"
    gap = selected_sales_gap_from_transcript(normalized)
    if gap:
        return f"selected_gap:{gap}"
    if active_topic:
        return f"topic:{active_topic}"
    if is_opening_greeting(normalized):
        return "opening_greeting"
    return "unclassified"


def sales_progression_step(active_topic: str | None, selected_gap: str | None, continuity: dict | None) -> str:
    reason = str((continuity or {}).get("reason") or "")
    if reason in {"agent_opening_started", "opening_greeting_answered"}:
        return "opening"
    if reason in {"appointment_time_requested", "appointment_value_clarified", "appointment_time_confirmed", "callback_time_confirmed"}:
        return "safe_next_step"
    if selected_gap:
        return "value_mapping"
    if active_topic == "qualification":
        return "qualification"
    if active_topic in {"price", "fit", "details", "effort", "terms"}:
        return "objection_or_answer"
    if active_topic == "timing":
        return "safe_next_step"
    return "qualification"


def build_conversation_memory(
    session_state: dict | None,
    transcript: str,
    candidate_response: str | None = None,
    continuity: dict | None = None,
) -> dict:
    turns = list((session_state or {}).get("turns") or [])
    normalized = normalize_text(transcript)
    active_topic = (
        str((continuity or {}).get("dialogue_focus") or "")
        or focus_from_transcript(normalized)
        or dialogue_focus_from_turns(turns)
        or "qualification"
    )
    continuity_reason = str((continuity or {}).get("reason") or "")
    transcript_can_select_gap = continuity_reason not in {
        "plain_qualification_term_clarified",
        "pragmatic_term_explained",
    }
    if is_starter_growth_plan_boundary_question(normalized):
        selected_gap = last_selected_gap_from_turns(turns)
    else:
        selected_gap = (
            (selected_sales_gap_from_transcript(normalized) if transcript_can_select_gap else None)
            or str((continuity or {}).get("selected_gap") or "")
            or last_selected_gap_from_turns(turns)
        )
        selected_gap = selected_gap or None
    callback_semantic = callback_semantic_from_transcript(normalized, session_state)
    if callback_semantic == CALLBACK_WORKFLOW_GAP and selected_gap in {None, "reminders"}:
        selected_gap = "callbacks"
    prior_question = previous_agent_question(turns)
    current_question_type = question_type_from_response(candidate_response or "")
    last_active_question_type = current_question_type if current_question_type != "none" else question_type_from_response(prior_question or "")
    prior_hashes = [response_hash(response) for response in previous_response_list(turns)]
    if candidate_response:
        prior_hashes.append(response_hash(candidate_response))
    response_signatures = previous_response_signatures(turns, candidate_response)
    response_subjects = previous_response_subjects(turns, candidate_response)
    return {
        "schema_version": 1,
        "active_stage": sales_progression_step(active_topic, selected_gap, continuity),
        "active_topic": active_topic,
        "selected_gap": selected_gap,
        "callback_semantic": callback_semantic,
        "last_agent_question_type": current_question_type,
        "last_active_agent_question_type": last_active_question_type,
        "last_agent_question_hash": response_hash(prior_question or ""),
        "asked_question_type_counts": response_question_counts(turns, candidate_response),
        "answered_topics": answered_topics_from_turns(turns, normalized, active_topic, selected_gap),
        "rejected_topics": rejected_topics_from_transcript(normalized, active_topic, selected_gap),
        "last_response_hashes": prior_hashes[-12:],
        "last_response_signatures": response_signatures[-12:],
        "recent_response_subjects": response_subjects[-12:],
        "candidate_response_subject": response_subject(candidate_response or ""),
        "candidate_response_signature": response_signature(candidate_response or ""),
        "last_customer_intent": last_customer_intent_from_transcript(normalized, callback_semantic, active_topic),
        "last_sales_progression_step": sales_progression_step(active_topic, selected_gap, continuity),
        "appointment_close_ready": bool((continuity or {}).get("reason") in {"appointment_time_requested", "appointment_value_clarified"}),
        "appointment_close_gap": selected_gap if (continuity or {}).get("reason") in {"appointment_time_requested", "appointment_value_clarified"} else None,
        "stored_audio_data": False,
        "stores_secrets": False,
    }


def response_starts_with_customer_phrase(transcript: str, response: str) -> bool:
    customer = normalize_text(transcript)
    spoken = normalize_text(response)
    if not customer or not spoken:
        return False
    words = customer.split()
    if len(words) >= 4 and spoken.startswith(" ".join(words[: min(7, len(words))])):
        return True
    return len(words) >= 5 and customer in spoken


def response_echo_repair(
    transcript: str,
    language: str,
    response: str,
    memory: dict,
    turns: list[dict],
    campaign: dict | None = None,
) -> str:
    normalized = normalize_text(transcript)
    callback_semantic = memory.get("callback_semantic")
    selected_gap = str(memory.get("selected_gap") or "")
    active_topic = str(memory.get("active_topic") or "") or dialogue_focus_from_turns(turns) or "qualification"
    openai_repair = public_openai_dialogue.duplicate_repair_response(
        transcript=transcript,
        memory=memory,
        turns=turns,
        candidate_response=response,
        campaign=campaign,
    )
    if openai_repair:
        return openai_repair
    if callback_semantic == CALLBACK_WORKFLOW_GAP:
        if is_generic_campaign_config(campaign):
            return generic_campaign_review_question(language, campaign)
        if is_callback_workflow_question(normalized):
            return callback_workflow_clarification_response(language)
        return gap_progression_text(
            language,
            "callbacks",
            gap_turn_count(turns, "callbacks"),
            previous_responses(turns) | {response},
        )
    if is_topic_confusion(normalized):
        return topic_confusion_response(language, campaign)
    if is_buyer_expects_agent_to_lead(normalized):
        return seller_agenda_recovered_response(language, campaign)
    if selected_gap:
        if is_generic_campaign_config(campaign):
            generic = generic_campaign_focus_text(language, active_topic, campaign, normalized=normalized)
            return generic or generic_campaign_next_step_text(language, campaign)
        return gap_progression_text(
            language,
            selected_gap,
            gap_turn_count(turns, selected_gap),
            previous_responses(turns) | {response},
        )
    if active_topic:
        return unique_progressive_focus_text(
            language,
            active_topic,
            normalized,
            focus_turn_count(turns, active_topic),
            previous_responses(turns) | {response},
            campaign,
        )
    return workflow_review_next_step_response(language, campaign)


def repeated_question_repair(
    language: str,
    transcript: str,
    memory: dict,
    turns: list[dict],
    response: str,
    campaign: dict | None = None,
) -> str:
    normalized = normalize_text(transcript)
    active_topic = str(memory.get("active_topic") or "") or dialogue_focus_from_turns(turns) or "qualification"
    selected_gap = str(memory.get("selected_gap") or "")
    openai_repair = public_openai_dialogue.duplicate_repair_response(
        transcript=transcript,
        memory=memory,
        turns=turns,
        candidate_response=response,
        campaign=campaign,
    )
    if openai_repair:
        return openai_repair
    if selected_gap and active_topic in {"qualification", "price", "fit", "details", "effort"}:
        if is_generic_campaign_config(campaign):
            generic = generic_campaign_focus_text(language, active_topic, campaign, normalized=normalized)
            return generic or generic_campaign_next_step_text(language, campaign)
        return gap_progression_text(
            language,
            selected_gap,
            gap_turn_count(turns, selected_gap),
            previous_responses(turns) | {response},
        )
    return unique_progressive_focus_text(
        language,
        active_topic,
        normalized,
        focus_turn_count(turns, active_topic),
        previous_responses(turns) | {response},
        campaign,
    )


def pre_speech_conversation_stability_guard(
    transcript: str,
    session_state: dict | None,
    language: str,
    candidate_response: str,
    conversation_memory: dict | None = None,
    campaign: dict | None = None,
) -> dict:
    turns = list((session_state or {}).get("turns") or [])
    response = candidate_response.strip()
    memory = conversation_memory or build_conversation_memory(session_state, transcript, response, None)
    normalized = normalize_text(transcript)
    violations: list[str] = []
    repaired_response: str | None = None

    if is_generic_campaign_config(campaign) and generic_account_support_request(normalized):
        return {
            "applied": True,
            "reason": "generic_account_support_boundary",
            "violations": ["account_support_request"],
            "dialogue_focus": memory.get("active_topic") or "qualification",
            "selected_gap": memory.get("selected_gap"),
            "candidate_response": generic_account_support_boundary_text(language, campaign),
        }

    if response in previous_responses(turns):
        violations.append("duplicate_final_response")
        if memory.get("callback_semantic") == CALLBACK_SCHEDULING_REQUEST:
            repaired_response = callback_request_time_response_for_transcript(language, normalized)
        else:
            repaired_response = repeated_question_repair(language, transcript, memory, turns, response, campaign)

    if not is_agent_open_turn(normalized) and response_reopens_focus_menu(response) and (memory.get("selected_gap") or memory.get("active_topic")):
        violations.append("generic_menu_reopened_after_focus")
        repaired_response = repeated_question_repair(language, transcript, memory, turns, response, campaign)

    if memory.get("callback_semantic") == CALLBACK_WORKFLOW_GAP and (
        "what time" in response.lower() or "note for the callback" in response.lower() or "callback time" in response.lower()
    ) and not (
        "workflow review" in response.lower() and ("northstar" in response.lower() or "quick call" in response.lower())
    ):
        violations.append("workflow_callback_treated_as_scheduling")
        repaired_response = response_echo_repair(transcript, language, response, memory, turns, campaign)

    question_type = question_type_from_response(response)
    question_counts = dict(memory.get("asked_question_type_counts") or {})
    if question_type in {"generic_focus_menu", "callback_time"} and question_counts.get(question_type, 0) > 3:
        violations.append(f"repeated_{question_type}")
        repaired_response = repeated_question_repair(language, transcript, memory, turns, response, campaign)

    if response_starts_with_customer_phrase(transcript, response):
        violations.append("leading_customer_echo")
        repaired_response = response_echo_repair(transcript, language, response, memory, turns, campaign)

    if is_new_trial_request_clarification(normalized) and not normalized_contains_any(
        normalize_text(response),
        {
            "inbound demo or trial inquiries",
            "inbound demo or trial requests",
            "trial inquiries",
            "trial requests",
        },
    ):
        violations.append("failed_to_explain_previous_question")
        repaired_response = new_trial_request_clarification_response(language)

    if is_previous_question_clarification_request(normalized) and not normalized_contains_any(
        normalize_text(response),
        {
            "i meant",
            "i was asking",
            "in plain terms",
            "callbacks here mean",
            "route signal is for",
            "routesignal",
            "shared inbox means",
            "by that i mean",
            "a handoff is",
            "i should have explained",
            "growth is",
        },
    ):
        violations.append("failed_to_explain_previous_question")
        repaired_response = clarify_previous_question_text(
            language,
            str(memory.get("active_topic") or "qualification"),
            previous_agent_question(turns),
            campaign,
        )

    if not violations:
        return {
            "applied": False,
            "reason": "conversation_stability_passed",
            "violations": [],
            "dialogue_focus": memory.get("active_topic"),
            "selected_gap": memory.get("selected_gap"),
        }

    repaired_response = repaired_response or workflow_review_next_step_response(language, campaign)
    if repaired_response == response and response in previous_responses(turns):
        repaired_response = unique_progressive_focus_text(
            language,
            str(memory.get("active_topic") or "qualification"),
            normalized,
            focus_turn_count(turns, str(memory.get("active_topic") or "qualification")) + 1,
            previous_responses(turns) | {response},
            campaign,
        )
    return {
        "applied": True,
        "reason": "conversation_stability_repaired",
        "violations": violations,
        "dialogue_focus": memory.get("active_topic"),
        "selected_gap": memory.get("selected_gap"),
        "candidate_response": repaired_response,
    }


def anti_loop_response(
    transcript: str,
    session_state: dict | None,
    language: str,
    generated_response: str,
    campaign: dict | None = None,
) -> dict:
    turns = list((session_state or {}).get("turns") or [])
    if not response_reopens_focus_menu(generated_response) or focus_menu_count(turns) == 0:
        return {"applied": False, "reason": "no_menu_loop_detected"}

    normalized = normalize_text(transcript)
    resolved_focus = dialogue_focus_from_turns(turns)
    selected_focus = focus_from_transcript(normalized)
    focus = selected_focus or resolved_focus
    if focus:
        return {
            "applied": True,
            "reason": f"menu_loop_prevented_with_{focus}_focus",
            "dialogue_focus": focus,
            "candidate_response": focus_followup_text(language, focus, normalized, campaign),
        }

    text = (
        "I only caught part of that. Please repeat the question in one sentence."
        if not language.startswith("de")
        else "Ich habe nur einen Teil verstanden. Bitte wiederholen Sie die Frage in einem Satz."
    )
    return {
        "applied": True,
        "reason": "menu_loop_prevented_without_clear_focus",
        "candidate_response": text,
    }


def continuity_response(
    transcript: str,
    session_state: dict | None,
    campaign: dict,
    dialogue_reasoning: dict | None = None,
) -> dict:
    language = str(campaign.get("language") or "en")
    normalized = normalize_text(transcript)
    turns = list((session_state or {}).get("turns") or [])
    previous = turns[-1] if turns else {}
    previous_summary = previous.get("summary") or {}
    previous_response = str(previous_summary.get("final_response") or "")

    resolved_focus = dialogue_focus_from_turns(turns)
    selected_focus = focus_from_transcript(normalized)
    callback_semantic = callback_semantic_from_transcript(normalized, session_state)
    if is_agent_open_turn(normalized):
        return {
            "applied": True,
            "reason": "agent_opening_started",
            "dialogue_focus": "qualification",
            "candidate_response": sales_opening_response(language, campaign),
        }
    early_call_context_recovery = call_context_recovery_response(normalized, resolved_focus, language, campaign)
    if early_call_context_recovery and str(early_call_context_recovery.get("reason") or "") in {
        "call_purpose_explained",
    }:
        return early_call_context_recovery
    if looks_like_asr_fragment(normalized, selected_focus):
        return {
            "applied": True,
            "reason": "asr_fragment_repair",
            "dialogue_focus": resolved_focus,
            "candidate_response": asr_fragment_response(language),
        }
    if is_buyer_stop_request(normalized):
        return {
            "applied": True,
            "reason": "buyer_requested_stop",
            "dialogue_focus": resolved_focus or "qualification",
            "candidate_response": buyer_stop_response(language),
        }
    if question_type_from_response(previous_response) == "callback_time" and is_callback_stop_reply(normalized):
        return {
            "applied": True,
            "reason": "buyer_requested_stop",
            "dialogue_focus": "timing",
            "candidate_response": buyer_stop_response(language),
        }
    if question_type_from_response(previous_response) == "permission_check" and is_permission_time_refusal_reply(normalized):
        return {
            "applied": True,
            "reason": "callback_request_time_needed",
            "dialogue_focus": "timing",
            "callback_semantic": CALLBACK_SCHEDULING_REQUEST,
            "candidate_response": callback_request_time_response_for_transcript(language, normalized),
        }
    if is_opening_greeting(normalized) and (
        not turns
        or not resolved_focus
        or str(previous_summary.get("call_control") or "") in {"end-call", "hang-up", "schedule-and-end"}
    ):
        return {
            "applied": True,
            "reason": "opening_greeting_answered",
            "dialogue_focus": "qualification",
            "candidate_response": opening_greeting_response(language, campaign),
        }
    if is_human_review_scope_question(normalized):
        return {
            "applied": True,
            "reason": "human_review_scope_explained",
            "dialogue_focus": resolved_focus or "details",
            "candidate_response": human_review_scope_response(language, campaign),
        }
    structured_route = structured_reasoning_continuity_response(
        normalized,
        language,
        campaign,
        turns,
        resolved_focus,
        dialogue_reasoning,
    )
    if structured_route:
        return structured_route
    if is_starter_growth_plan_boundary_question(normalized) and not is_generic_campaign_config(campaign):
        return {
            "applied": True,
            "reason": "plan_boundary",
            "dialogue_focus": "price",
            "candidate_response": starter_growth_plan_boundary_response(language, turns),
        }
    if is_direct_price_question(normalized):
        return {
            "applied": True,
            "reason": "explicit_price_question_answered",
            "dialogue_focus": "price",
            "candidate_response": generic_campaign_price_text(language, campaign)
            if is_generic_campaign_config(campaign)
            else live_demo_price_answer(language),
        }
    if has_appointment_time_confirmation_signal(normalized, session_state):
        return {
            "applied": True,
            "reason": "appointment_time_confirmed",
            "dialogue_focus": "timing",
            "candidate_response": appointment_time_confirmed_response(language),
        }
    if callback_semantic == CALLBACK_TIME_CONFIRMATION:
        return {
            "applied": True,
            "reason": "callback_time_confirmed",
            "dialogue_focus": "timing",
            "candidate_response": callback_time_confirmed_response(language, campaign),
        }
    pending_appointment_gap = pending_appointment_gap_from_turns(turns)
    if pending_appointment_gap and has_vague_appointment_time_signal(normalized):
        return {
            "applied": True,
            "reason": "appointment_time_clarification_needed",
            "dialogue_focus": "timing",
            "selected_gap": pending_appointment_gap,
            "candidate_response": appointment_time_clarification_response(language, pending_appointment_gap),
        }
    if pending_appointment_gap and (is_affirmative_next_step_reply(normalized) or is_pain_confirmation_reply(normalized)):
        return {
            "applied": True,
            "reason": "appointment_time_requested",
            "dialogue_focus": "timing",
            "selected_gap": pending_appointment_gap,
            "candidate_response": appointment_time_followup_response(
                language,
                pending_appointment_gap,
                appointment_time_request_count(turns),
            ),
        }
    if is_already_stated_problem_reply(normalized):
        stated_gap = pending_appointment_gap or last_selected_gap_from_turns(turns) or selected_sales_gap_from_transcript(normalized) or "handoffs"
        return {
            "applied": True,
            "reason": "appointment_time_requested",
            "dialogue_focus": "timing",
            "selected_gap": stated_gap,
            "candidate_response": already_stated_problem_response(language, stated_gap),
        }
    if pending_appointment_gap and is_value_relevance_question(normalized):
        return {
            "applied": True,
            "reason": "appointment_value_clarified",
            "dialogue_focus": "timing",
            "selected_gap": pending_appointment_gap,
            "candidate_response": appointment_value_clarification_response(language, pending_appointment_gap),
        }
    if is_callback_workflow_question(normalized):
        if is_generic_campaign_config(campaign):
            return {
                "applied": True,
                "reason": "generic_campaign_callback_question_repaired",
                "dialogue_focus": resolved_focus or "qualification",
                "candidate_response": generic_campaign_review_question(language, campaign),
            }
        return {
            "applied": True,
            "reason": "callback_workflow_clarified",
            "dialogue_focus": resolved_focus or "details",
            "selected_gap": "callbacks",
            "callback_semantic": CALLBACK_WORKFLOW_GAP,
            "candidate_response": callback_workflow_clarification_response(language),
        }
    if is_new_trial_request_clarification(normalized):
        if is_generic_campaign_config(campaign):
            return {
                "applied": True,
                "reason": "generic_campaign_trial_request_repaired",
                "dialogue_focus": resolved_focus or "qualification",
                "candidate_response": generic_campaign_review_question(language, campaign),
            }
        return {
            "applied": True,
            "reason": "new_trial_request_clarified",
            "dialogue_focus": resolved_focus or "qualification",
            "candidate_response": new_trial_request_clarification_response(language),
        }
    if is_value_relevance_question(normalized):
        return {
            "applied": True,
            "reason": "value_relevance_explained",
            "dialogue_focus": resolved_focus or "qualification",
            "candidate_response": value_relevance_response(language, campaign),
        }
    if is_buyer_no_question_repair(normalized):
        return {
            "applied": True,
            "reason": "buyer_no_question_recovered",
            "dialogue_focus": resolved_focus or "qualification",
            "candidate_response": buyer_no_question_response(language, campaign),
        }
    should_close, appointment_gap = should_offer_appointment_close(normalized, turns)
    if should_close:
        return {
            "applied": True,
            "reason": "appointment_time_requested",
            "dialogue_focus": "timing",
            "selected_gap": appointment_gap,
            "candidate_response": appointment_lead_close_response(language, appointment_gap),
        }
    if callback_semantic == CALLBACK_WORKFLOW_GAP:
        if is_generic_campaign_config(campaign):
            primary_issue = _generic_primary_issue_phrase(campaign)
            return {
                "applied": True,
                "reason": "generic_campaign_callback_mismatch_boundary",
                "dialogue_focus": resolved_focus or "qualification",
                "callback_semantic": CALLBACK_WORKFLOW_GAP,
                "candidate_response": (
                    f"I hear you. Callbacks sound like the issue on your mind, "
                    f"but this call is about {primary_issue}. Should I stop here?"
                ),
            }
        gap_focus = resolved_focus or "qualification"
        return {
            "applied": True,
            "reason": f"seller_gap_selected_for_{gap_focus}" if resolved_focus else "callback_workflow_gap_selected",
            "dialogue_focus": gap_focus,
            "selected_gap": "callbacks",
            "callback_semantic": CALLBACK_WORKFLOW_GAP,
            "candidate_response": gap_progression_text(
                language,
                "callbacks",
                gap_turn_count(turns, "callbacks"),
                previous_responses(turns),
            ),
        }
    if is_next_step_question(normalized):
        selected_gap = last_selected_gap_from_turns(turns)
        if selected_gap:
            return {
                "applied": True,
                "reason": f"selected_{selected_gap}_next_step_explained",
                "dialogue_focus": resolved_focus or "qualification",
                "selected_gap": selected_gap,
                "candidate_response": gap_progression_text(
                    language,
                    selected_gap,
                    gap_turn_count(turns, selected_gap),
                    previous_responses(turns),
                ),
            }
    call_context_recovery = call_context_recovery_response(normalized, resolved_focus, language, campaign)
    if call_context_recovery:
        return call_context_recovery
    if callback_semantic == CALLBACK_SCHEDULING_REQUEST:
        return {
            "applied": True,
            "reason": "callback_request_time_needed",
            "dialogue_focus": "timing",
            "callback_semantic": CALLBACK_SCHEDULING_REQUEST,
            "candidate_response": callback_request_time_response_for_transcript(language, normalized),
        }
    if has_caller_identity_question(normalized):
        return {
            "applied": True,
            "reason": "caller_identity_recalled",
            "dialogue_focus": resolved_focus or "qualification",
            "candidate_response": caller_identity_recall_response(language, campaign),
        }
    campaign_depth = english_live_demo_campaign_response(normalized, campaign)
    if campaign_depth:
        return campaign_depth
    if selected_focus and resolved_focus and selected_focus != resolved_focus:
        return {
            "applied": True,
            "reason": f"focus_shift_to_{selected_focus}_from_{resolved_focus}",
            "dialogue_focus": selected_focus,
            "candidate_response": continuity_text(language, selected_focus, campaign=campaign),
        }
    current_focus_followup = current_focus_followup_response(normalized, resolved_focus, language, turns, campaign)
    if current_focus_followup:
        return current_focus_followup
    if resolved_focus == "price" and normalized_contains_any(
        normalized,
        {"price", "cost", "too expensive", "monthly price", "budget", "money", "preis", "kosten", "zu teuer"},
    ):
        return {
            "applied": True,
            "reason": "resolved_price_focus_persisted",
            "dialogue_focus": "price",
            "candidate_response": continuity_text(language, "price", persisted=True, campaign=campaign),
        }
    if resolved_focus == "fit" and normalized_contains_any(
        normalized,
        {"fit", "relevant", "situation", "workflow", "problem", "passung", "passt"},
    ):
        return {
            "applied": True,
            "reason": "resolved_fit_focus_persisted",
            "dialogue_focus": "fit",
            "candidate_response": continuity_text(language, "fit", persisted=True, campaign=campaign),
        }
    if resolved_focus == "timing" and normalized_contains_any(
        normalized,
        {"timing", "later", "not now", "callback", "time", "zeitpunkt", "spaeter"},
    ):
        return {
            "applied": True,
            "reason": "resolved_timing_focus_persisted",
            "dialogue_focus": "timing",
            "candidate_response": continuity_text(language, "timing", persisted=True, campaign=campaign),
        }
    if resolved_focus == "effort" and normalized_contains_any(
        normalized,
        {"worth", "worth my time", "worth the effort", "reviewing options", "viewing options", "effort", "time"},
    ):
        return {
            "applied": True,
            "reason": "resolved_effort_focus_persisted",
            "dialogue_focus": "effort",
            "candidate_response": continuity_text(language, "effort", persisted=True, campaign=campaign),
        }
    if resolved_focus == "terms" and normalized_contains_any(
        normalized,
        {"terms", "contract terms", "conditions", "bedingungen", "vertragsbedingungen"},
    ):
        return {
            "applied": True,
            "reason": "resolved_terms_focus_persisted",
            "dialogue_focus": "terms",
            "candidate_response": continuity_text(language, "terms", persisted=True, campaign=campaign),
        }
    if resolved_focus == "details" and normalized_contains_any(
        normalized,
        {"details", "product details", "plan details", "included", "exact product"},
    ):
        return {
            "applied": True,
            "reason": "resolved_details_focus_persisted",
            "dialogue_focus": "details",
            "candidate_response": continuity_text(language, "details", persisted=True, campaign=campaign),
        }

    if selected_focus and response_asked_price_choice(previous_response) and selected_focus in {"price", "terms", "effort"}:
        return {
            "applied": True,
            "reason": f"short_answer_selected_{selected_focus}_after_price_prompt",
            "dialogue_focus": selected_focus,
            "candidate_response": continuity_text(language, selected_focus, campaign=campaign),
        }
    if selected_focus and response_asked_main_focus_choice(previous_response):
        return {
            "applied": True,
            "reason": f"short_answer_selected_{selected_focus}_after_main_focus_prompt",
            "dialogue_focus": selected_focus,
            "candidate_response": continuity_text(language, selected_focus, campaign=campaign),
        }
    if normalized in {"yes", "yeah", "yep", "sure", "ok", "okay"} and response_asked_main_focus_choice(previous_response):
        text = (
            "I need one focus to make this useful: price, fit, timing, or exact product details."
            if not language.startswith("de")
            else "Ich brauche einen Fokus, damit es hilfreich ist: Preis, Passung, Zeitpunkt oder genaue Produktdetails."
        )
        return {
            "applied": True,
            "reason": "affirmative_after_main_focus_prompt_needs_specific_focus",
            "candidate_response": text,
        }
    if previous_summary.get("sales_difficulty") == "autonomy-check" and normalized_contains_any(
        normalized,
        {"need time", "still need time", "not now", "later", "callback", "do not rush", "dont rush"},
    ):
        return {
            "applied": True,
            "reason": "autonomy_followup_kept_low_pressure",
            "dialogue_focus": "timing",
            "candidate_response": continuity_text(language, "timing", campaign=campaign),
        }
    if previous_summary.get("sales_difficulty") == "existing-provider-gap" and normalized_contains_any(
        normalized,
        {"routing", "follow up", "followup", "callback", "does not cover", "misses", "gap"},
    ):
        text = (
            "Then that is the gap to check: whether routing, callbacks, or follow-up work are still slipping through. I can keep this to a written comparison."
            if not language.startswith("de")
            else "Dann ist genau diese Luecke der Punkt: ob Routing, Rueckrufe oder Nachverfolgung noch liegen bleiben. Ich kann das auf einen schriftlichen Vergleich begrenzen."
        )
        return {
            "applied": True,
            "reason": "provider_gap_followup_answered",
            "dialogue_focus": "provider_gap",
            "candidate_response": text,
        }

    if selected_focus and not resolved_focus:
        return {
            "applied": True,
            "reason": f"initial_{selected_focus}_focus_selected" if not turns else f"explicit_{selected_focus}_focus_selected",
            "dialogue_focus": selected_focus,
            "candidate_response": continuity_text(language, selected_focus, campaign=campaign),
        }

    return {"applied": False, "reason": "no_session_continuity_match"}
