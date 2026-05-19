from __future__ import annotations

import hashlib
import re

from runtime.speech.asr_quality_gate import asr_fragment_response, looks_like_asr_fragment, normalize_transcript

AGENT_OPEN_TRANSCRIPT = "__agent_open__"
CALLBACK_WORKFLOW_GAP = "callback_workflow_gap"
CALLBACK_SCHEDULING_REQUEST = "callback_scheduling_request"
CALLBACK_TIME_CONFIRMATION = "callback_time_confirmation"


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


def nested_campaign_value(campaign: dict | None, section: str, key: str, fallback: str) -> str:
    data = (campaign or {}).get(section) or {}
    value = str(data.get(key) or "").strip() if isinstance(data, dict) else ""
    return value or fallback


def sales_opening_response(language: str, campaign: dict | None = None) -> str:
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
            "Sind Sie fuer Demo-Nachverfolgung zustaendig? Wir helfen bei verpassten Rueckrufen und Uebergaben. "
            "Lohnt sich dazu ein kurzer Check?"
        )
    return (
        f"Hi, this is {representative} calling from {client_name}, {product_relationship}. "
        f"Do you have a minute? I am looking for {buyer_role}. We help stop missed callbacks and messy handoffs. "
        "Is that worth a quick check?"
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


def callback_time_confirmed_response(language: str) -> str:
    if language.startswith("de"):
        return "Bestaetigt. Ich notiere den Rueckruf so. Auf Wiederhoeren."
    return "Confirmed. I will record that callback time for the specialist. Goodbye."


def callback_workflow_clarification_response(language: str) -> str:
    if language.startswith("de"):
        return "Mit Rueckrufen meine ich Nachfass-Erinnerungen nach Demo-Anfragen, nicht diesen Anruf. RouteSignal haelt Besitzer und naechsten Schritt sichtbar. Passieren verpasste Nachfassaktionen oft genug?"
    return (
        "Callbacks here mean follow-up reminders after an inbound demo request, not scheduling this call. "
        "RouteSignal keeps owner and next step visible. Are missed follow-ups happening often enough to check?"
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


def has_callback_scheduling_request_signal(normalized: str) -> bool:
    return has_callback_request_signal(normalized)


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
            "what s this about",
            "what are you calling about",
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
    return normalized_contains_any(normalized, {"what is the next step", "what s the next step", "what next", "next step"})


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
    return normalized_contains_any(
        normalized,
        {
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
    return normalized in {"i do not know", "i dont know", "i don t know", "not sure", "i m not sure", "im not sure"}


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
        },
    )


def buyer_stop_response(language: str) -> str:
    if language.startswith("de"):
        return "Verstanden. Ich stoppe hier und notiere, dass Sie dazu nicht weiter angerufen werden moechten. Auf Wiederhoeren."
    return "Understood. I will stop here and mark that you do not want another call about this. Goodbye."


def new_trial_request_clarification_response(language: str) -> str:
    if language.startswith("de"):
        return "Mit neuen Testanfragen meine ich eingehende Demo- oder Testanfragen, die einen Besitzer und eine Nachfassung brauchen. Passiert dort etwas wie ein verpasster Rueckruf?"
    return "I meant inbound demo or trial inquiries that need an owner and a follow-up step. Does that handoff ever get missed?"


def buyer_no_question_response(language: str) -> str:
    if language.startswith("de"):
        return "Stimmt, Sie haben keine Frage gestellt. Ich rufe wegen einer Sache an: gehen Demo-Nachfassaktionen bei Besitzer, Rueckruf oder Uebergabe verloren?"
    return "Fair, you did not ask a question. I called to check one thing: do inbound demo follow-ups lose the owner, callback reminder, or handoff status?"


def value_relevance_response(language: str) -> str:
    if language.startswith("de"):
        return "Es zaehlt nur, wenn diese Luecke heute Zeit kostet: verpasste Rueckrufe, unklare Besitzer oder verlorene Uebergaben. Was kostet heute wirklich Zeit?"
    return "In plain terms, it matters only if that gap costs time today: missed callbacks, unclear owners, or lost handoffs. Which one costs time today?"


def time_constrained_agenda_response(language: str) -> str:
    if language.startswith("de"):
        return "Ich halte es bei einer Frage: gehen Demo-Nachfassaktionen bei Besitzer, Rueckruf-Erinnerung oder Uebergabe verloren?"
    return "I will keep it to one question: are inbound demo follow-ups missing owners, callback reminders, or handoffs?"


def seller_agenda_recovered_response(language: str) -> str:
    if language.startswith("de"):
        return "Fair. Ich pruefe einen Ablauf: verlieren Demo-Nachfassaktionen Besitzer, Rueckruf-Erinnerungen oder Uebergabestatus?"
    return "Fair. I called to check one workflow: do inbound demo follow-ups lose owners, callback reminders, or handoff status?"


def call_purpose_response(language: str) -> str:
    if language.startswith("de"):
        return "Ich rufe wegen Demo-Nachfassaktionen an: Besitzer, Rueckruf-Erinnerung und Uebergabestatus. Soll ich eine dieser Luecken pruefen?"
    return "I am calling about inbound demo follow-up: owners, callback reminders, and handoff status. Which of those creates the most missed follow-up?"


def workflow_review_next_step_response(language: str) -> str:
    if language.startswith("de"):
        return "Der naechste Schritt ist eine kurze Pruefung: Besitzer, Rueckruf-Erinnerung oder Uebergabe. Welche Luecke soll ich pruefen?"
    return "The quick check is one workflow gap: owner, callback reminder, or handoff status. Which one should I check?"


def written_summary_response(language: str) -> str:
    if language.startswith("de"):
        return "Ich kann eine kurze Workflow-Zusammenfassung schicken: Besitzer, Rueckruf-Erinnerung und Uebergabestatus. Soll sie sich auf Rueckruf-Erinnerungen konzentrieren?"
    return "I can send a short workflow summary: owner routing, callback reminders, and handoff status. Should it focus on the callback gap you mentioned?"


def workflow_review_scope_response(language: str) -> str:
    if language.startswith("de"):
        return "Kurz heisst eine Workflow-Luecke, keine volle Demo: Besitzer, Rueckruf-Erinnerung oder Uebergabe. Welche soll ich pruefen?"
    return "Short means one workflow gap, not a full demo: owner, callback reminder, or handoff status. Which one should I check?"


def time_waste_repair_response(language: str) -> str:
    if language.startswith("de"):
        return "Fair. Ich kann hier stoppen. Die kurze Pruefung ist, ob Demo-Nachfassaktionen Besitzer oder Rueckruf-Erinnerungen verlieren. Soll ich beenden?"
    return "Fair. I can stop here. The quick check is whether demo follow-ups lose owners or callback reminders. Should I end the call?"


def uncertain_gap_response(language: str) -> str:
    if language.startswith("de"):
        return "Kein Problem. Die kurze Pruefung ist einfacher: fehlt Demo-Nachfassaktionen manchmal Besitzer, Rueckruf-Erinnerung oder Uebergabe?"
    return "No problem. The quick check is simpler: do demo follow-ups ever miss an owner, callback reminder, or handoff?"


def topic_confusion_response(language: str) -> str:
    if language.startswith("de"):
        return "Ich war nicht klar. RouteSignal betrifft Demo-Nachfassaktionen: Besitzer, Rueckruf-Erinnerung und Uebergabestatus. Soll ich stoppen?"
    return "I am not being clear. RouteSignal is for demo follow-up: owner, callback reminder, and handoff status. Should I keep it to callback reminders, or stop here?"


def frustrated_confusion_response(language: str) -> str:
    if language.startswith("de"):
        return "Fair, ich habe den Faden verloren. Die kurze Pruefung ist Demo-Nachfassung: Besitzer, Rueckruf-Erinnerung oder Uebergabe. Soll ich stoppen?"
    return "Fair, I lost the thread. The quick check is demo follow-up owners, callback reminders, or handoffs. Should I stop?"


def call_context_recovery_response(normalized: str, resolved_focus: str | None, language: str) -> dict | None:
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
            return {
                "applied": True,
                "reason": reason,
                "dialogue_focus": focus,
                "candidate_response": response_builder(language),
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

    if normalized_contains_any(normalized, {"soc 2", "soc2", "security", "secure", "compliance"}):
        return candidate(
            "campaign_depth_security_boundary_answered",
            "security",
            "I cannot claim that here. Use verified security material before any serious rollout discussion.",
        )
    if normalized_contains_any(normalized, {"salesforce", "hubspot", "integrate", "integration", "connect with", "crm"}):
        return candidate(
            "campaign_depth_integration_boundary_answered",
            "details",
            "The fictional profile supports owner lookup, but exact setup and permissions need verified review before I claim fit.",
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
            "That breaks when ownership changes. RouteSignal keeps the lead, callback, reminder, and handoff status in one workflow. Where does it break first today?",
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
                or "RouteSignal CRM routes leads, captures follow-up tasks, and shows handoff status."
            )
            + " Where does follow-up break first today: routing, reminders, or handoff review?",
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
    return response_asked_main_focus_choice(response) or response_asked_price_choice(response)


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


def continuity_text(language: str, focus: str, *, persisted: bool = False) -> str:
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
            return "The effort test is simple: does missed follow-up cost more time than this review? If not, stop here."
        return "The effort test is simple: does missed follow-up cost more time than this review? If not, stop here."
    if focus == "fit":
        if german:
            if persisted:
                return "Dann bleiben wir bei der Passung. Entscheidend ist, ob Rueckruf- oder Nachverfolgungsarbeit in Ihrem aktuellen Ablauf wirklich offen bleibt."
            return "Verstanden. Dann geht es zuerst um Passung: ob das Problem in Ihrer Situation wirklich existiert, bevor wir ueber einen naechsten Schritt sprechen."
        if persisted:
            return "Fit depends on a real workflow gap: missed leads, callbacks, or handoffs. If that is not happening, stop here."
        return "Fit depends on a real workflow gap: missed leads, callbacks, or handoffs. If that is not happening, stop here."
    if focus == "timing":
        if german:
            if persisted:
                return "Dann bleibt der Zeitpunkt der Engpass. Ich wuerde es bei einer schriftlichen Zusammenfassung oder einem spaeteren Rueckruf belassen."
            return "Verstanden. Dann steht der Zeitpunkt im Vordergrund. Heute muss nichts entschieden werden; hoechstens eine kurze schriftliche Zusammenfassung oder ein spaeterer Rueckruf."
        if persisted:
            return "If timing is the blocker, use a written summary or later callback. No decision now."
        return "If timing is the blocker, use a written summary or later callback. No decision now."
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
    return "I can answer that directly if you name the point: workflow, price, security, or callback timing."


def focus_followup_text(language: str, focus: str, normalized: str) -> str:
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
            return "Check effort only: is missed follow-up costing enough time to justify a review? If not, stop here."
    if focus == "details":
        if asks_for_explanation:
            if german:
                return "Bei den Details geht es hier um Lead-Routing und Nachverfolgung. Was genau integriert wird, sollte ein Spezialist pruefen."
            return "The workflow scope is lead routing, follow-up, and handoff review. Exact integrations need verified checks."
        if agrees_to_continue:
            if german:
                return "Gut, dann bleiben wir bei den Details: was der Workflow abdeckt, was offen bleibt und was ein Spezialist pruefen sollte."
            return "Check scope only: what the workflow covers, what remains open, and what needs verified review."
    if focus == "fit":
        if asks_for_explanation:
            if german:
                return "Bei der Passung geht es darum, ob Lead-Routing oder Nachverfolgung in Ihrem aktuellen Ablauf wirklich ein Problem ist."
            return "Fit depends on a real workflow gap: missed leads, callbacks, or handoffs. If that is not happening, stop here."
        if agrees_to_continue:
            if german:
                return "Gut, dann bleiben wir bei der Passung und pruefen nur, ob das Problem in Ihrem Ablauf wirklich existiert."
            return "Check fit only: are leads, callbacks, or handoffs getting missed today? If not, stop here."
    if focus == "timing":
        if asks_for_explanation or agrees_to_continue:
            return continuity_text(language, "timing", persisted=True)
    if focus == "qualification":
        if is_value_relevance_question(normalized):
            return value_relevance_response(language)
        if asks_for_explanation:
            if german:
                return "Einfach gesagt: RouteSignal ist nur relevant, wenn Demo-Nachfassung rutscht: verpasste Rueckrufe, unklare Besitzer oder Uebergabestatus. Was davon passiert wirklich?"
            return "In plain terms, RouteSignal is only relevant if demo follow-up is slipping: missed callbacks, unclear owners, or handoff status. Which of those actually happens?"
        if agrees_to_continue:
            return modular_qualification_guidance_text(language, 1)
    return continuity_text(language, focus, persisted=True)


def same_focus_progression_response(normalized: str, resolved_focus: str | None, language: str, turns: list[dict]) -> dict | None:
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
        return {
            "applied": True,
            "reason": f"resolved_{resolved_focus}_focus_progressed",
            "dialogue_focus": resolved_focus,
            "candidate_response": proactive_guidance_text(
                language,
                resolved_focus,
                max(0, focus_turn_count(turns, resolved_focus) - 1),
            ),
        }
    return None


def modular_qualification_guidance_text(language: str, step: int) -> str:
    if language.startswith("de"):
        options = [
            "Die kurze Pruefung ist verpasste Nachverfolgung: Routing, Rueckrufe oder Uebergaben. Welche Luecke kostet heute die meiste Zeit?",
            "Wenn diese Luecken real sind, gibt RouteSignal Besitzer, Erinnerung und Uebergabe einen Ablauf. Welcher Teil rutscht am haeufigsten durch?",
            "Der Verkaufsgrund ist einfach: weniger verpasste Rueckrufe und klarere Besitzer. Waere eine kurze Workflow-Pruefung sinnvoll?",
        ]
        return options[step % len(options)]
    contexts = [
        ("Inbound demo requests", ("owner", "callback", "handoff status"), "Which part slips first for your team?"),
        ("Shared inbox leads", ("owner routing", "callback reminders", "manager visibility"), "Where does that break today?"),
        ("Spreadsheet follow-up", ("routing delay", "handoff review", "missed callbacks"), "Which one creates the most delay?"),
        ("Slack alerts and CRM notes", ("owner lookup", "follow-up status", "handoff review"), "Would a short workflow review test one gap?"),
        ("New trial requests", ("priority routing", "duplicate checks", "callback visibility"), "Which gap should I keep this focused on?"),
        ("Manager review", ("routing", "reminders", "handoff visibility"), "Are missed callbacks frequent enough to justify a workflow review?"),
    ]
    subject, signals, question = contexts[step % len(contexts)]
    return f"{subject} need {signals[0]}, {signals[1]}, and {signals[2]}. {question}"


def progressive_focus_text(language: str, focus: str, normalized: str, step: int) -> str:
    german = language.startswith("de")
    if focus == "qualification":
        return modular_qualification_guidance_text(language, step)
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
                "Fit depends on a real workflow gap: missed leads, callbacks, or handoffs. If that is not happening, stop here."
                if not german
                else "Bei der Passung geht es darum, ob Lead-Routing oder Nachverfolgung in Ihrem aktuellen Ablauf wirklich ein Problem ist."
            ),
            (
                "The practical fit check is whether inbound leads, callbacks, or handoffs get missed today."
                if not german
                else "Die naechste Passungsfrage ist praktisch: Bleiben heute Leads, Rueckrufe oder Uebergaben liegen?"
            ),
            (
                "If that problem is real, a verified workflow review may be useful. If not, stop here."
                if not german
                else "Wenn dieses Problem real ist, kann ein Spezialist die Passung pruefen; wenn nicht, gibt es keinen Grund weiterzumachen."
            ),
            (
                "The yes-or-no is whether missed handoffs justify even a short workflow review."
                if not german
                else "Die praktische Ja-Nein-Frage ist, ob verpasste Uebergaben oft genug passieren, um eine kurze Spezialistenpruefung zu rechtfertigen."
            ),
            (
                "If fit stays unclear after that, stop at a written summary."
                if not german
                else "Wenn die Passung danach noch unklar ist, wuerde ich bei einer schriftlichen Zusammenfassung stoppen, statt live weiterzudraengen."
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
                "The effort test is simple: does missed follow-up cost more time than this review? If not, stop here."
                if not german
                else "Die Aufwandfrage ist konkret: Lohnt sich die Durchsicht nur, wenn Rueckrufe oder Nachverfolgung heute Zeit kosten?"
            ),
            (
                "If the review takes more time than the problem costs, stop here."
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
                "If timing is the blocker, use a written summary or later callback. No decision now."
                if not german
                else "Dann bleibt der Zeitpunkt der Engpass. Ich wuerde es bei schriftlicher Zusammenfassung oder spaeterem Rueckruf belassen."
            ),
            (
                "If now is not the right time, use a later callback or written summary."
                if not german
                else "Wenn jetzt nicht der richtige Zeitpunkt ist, bleibt nur ein spaeterer Rueckruf oder eine schriftliche Zusammenfassung."
            ),
            (
                "A useful timing test is whether missed follow-up is already costing time. If not, wait."
                if not german
                else "Die sinnvolle Zeitfrage ist, ob verpasste Nachverfolgung heute schon Zeit kostet. Wenn nicht, warten."
            ),
        ],
    }
    options = variants.get(focus) or [continuity_text(language, focus, persisted=True)]
    return options[min(step, len(options) - 1)]


def exhausted_progression_options(language: str, focus: str) -> list[str]:
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
            "Timing is already the blocker. The safe next step is either a later callback you choose or a short written summary.",
            "No decision now. If you want to continue later, give me a callback time; otherwise I can stop here.",
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


def unique_progressive_focus_text(language: str, focus: str, normalized: str, step: int, seen: set[str]) -> str:
    for offset in range(8):
        candidate = progressive_focus_text(language, focus, normalized, step + offset)
        if candidate not in seen:
            return candidate
    for candidate in exhausted_progression_options(language, focus):
        if candidate not in seen:
            return candidate
    fallback = progressive_focus_text(language, focus, normalized, step)
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
    if normalized_contains_any(normalized, {"handoff", "handoffs", "handoff review", "ownership", "owner changes"}):
        return "handoffs"
    if normalized_contains_any(normalized, {"callback", "callbacks", "call backs", "missed calls", "missed callbacks"}):
        return "callbacks"
    if normalized_contains_any(normalized, {"reminder", "reminders", "follow up", "follow-up", "followup"}):
        return "reminders"
    if normalized_contains_any(normalized, {"routing", "route", "assignment", "owner assignment"}):
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
        "handoffs": "handoff review is the value point: owner, next callback, and status stop getting lost",
        "callbacks": "callback reminders are the value point: fewer inbound demo requests wait without a next step",
        "reminders": "reminders are the value point: the team chases fewer follow-ups by hand",
        "routing": "priority routing is the value point: each inbound request gets a clear owner faster",
        "duplicates": "duplicate checks are the value point: lead ownership stays cleaner before follow-up",
        "visibility": "manager visibility is the value point: handoff status and missed follow-up are easier to inspect",
    }
    claim = gap_claims.get(gap, "that workflow gap is the value point")
    return (
        f"Then {claim}. Would a short workflow review focus only on that gap?"
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


def gap_progression_text(language: str, gap: str, step: int, seen: set[str] | None = None) -> str:
    seen = seen or set()
    if language.startswith("de"):
        return seller_guided_next_step_text(language, gap)
    variants = {
        "callbacks": [
            seller_guided_next_step_text(language, "callbacks"),
            "For callbacks, the business case is speed to lead: owner and reminder are visible before a demo request waits. Should I keep the review to missed reminders only?",
            "If callback reminders are clean today, stop here. If they slip, Growth is worth reviewing. Which gap should the next step test first?",
            "The useful next step is a short summary of owner, next callback, and handoff status. Would a short written summary help you judge fit?",
        ],
        "handoffs": [
            seller_guided_next_step_text(language, "handoffs"),
            "For handoffs, the value is handoff review: owner, next callback, and manager visibility stay together. Should I keep the short workflow review to handoff misses only?",
            "If handoffs are clean today, stop here. If owner, next callback, or manager visibility slips, a short workflow review has a reason. Which part breaks most often?",
        ],
        "routing": [
            seller_guided_next_step_text(language, "routing"),
            "For routing, the value is clear ownership before follow-up waits. Should I keep the review to owner assignment only?",
        ],
        "reminders": [
            seller_guided_next_step_text(language, "reminders"),
            "For reminders, the value is fewer manual chases after inbound demos. Should I keep the review to missed reminder count only?",
        ],
    }
    options = variants.get(gap) or [seller_guided_next_step_text(language, gap), workflow_review_next_step_response(language)]
    for offset in range(len(options)):
        candidate = options[(step + offset) % len(options)]
        if candidate not in seen:
            return candidate
    return options[step % len(options)] + " The next useful check is whether that gap is worth verified review."


def proactive_guidance_text(language: str, focus: str, step: int) -> str:
    german = language.startswith("de")
    if focus == "qualification":
        return modular_qualification_guidance_text(language, step)
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
                "The selling point is consistency: owner lookup, reminders, and handoff status make missed follow-up easier to see and fix."
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
                "The practical workflow is capture, route, remind, and review handoff status. That is the part worth checking before integration details."
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


def duplicate_response_repair(transcript: str, session_state: dict | None, language: str, generated_response: str) -> dict:
    turns = list((session_state or {}).get("turns") or [])
    response = generated_response.strip()
    if not response or response not in previous_responses(turns):
        return {"applied": False, "reason": "no_duplicate_response_detected"}
    normalized = normalize_text(transcript)
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
        },
    )


def previous_agent_question(turns: list[dict]) -> str | None:
    for turn in reversed(turns):
        response = str((turn.get("summary") or {}).get("final_response") or "").strip()
        if "?" in response:
            return response
    return None


def clarify_previous_question_text(language: str, focus: str, previous_question: str | None) -> str:
    del previous_question
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
    return "I was asking whether missed callbacks, messy handoffs, or unclear owners happen in your inbound demo flow. In plain terms, which part needs a clearer owner or callback?"


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


def ambiguous_negative_clarification_text(language: str, focus: str, previous_question: str | None) -> str:
    del focus, previous_question
    if language.startswith("de"):
        return "Kein Problem. Meinen Sie, jetzt passt es nicht, oder sind verpasste Rueckrufe und Uebergaben kein Thema?"
    return "No problem. Do you mean now is not a good time, or that missed callbacks and handoffs are not an issue?"


def current_focus_followup_response(
    normalized: str,
    resolved_focus: str | None,
    language: str,
    turns: list[dict] | None = None,
) -> dict | None:
    if not resolved_focus:
        return None
    turns = list(turns or [])
    prior_question = previous_agent_question(turns)
    if prior_question and is_previous_question_clarification_request(normalized):
        return {
            "applied": True,
            "reason": "previous_question_clarified",
            "dialogue_focus": resolved_focus,
            "candidate_response": clarify_previous_question_text(language, resolved_focus, prior_question),
        }
    if prior_question and is_ambiguous_negative_reply(normalized):
        return {
            "applied": True,
            "reason": "ambiguous_negative_clarified",
            "dialogue_focus": resolved_focus,
            "candidate_response": ambiguous_negative_clarification_text(language, resolved_focus, prior_question),
        }
    call_context_recovery = call_context_recovery_response(normalized, resolved_focus, language)
    if call_context_recovery:
        return call_context_recovery
    selected_gap = selected_sales_gap_from_transcript(normalized)
    if selected_gap and resolved_focus in {"price", "fit", "details", "effort", "qualification"}:
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
    progression = same_focus_progression_response(normalized, resolved_focus, language, turns)
    if progression:
        return progression
    return {
        "applied": True,
        "reason": f"resolved_{resolved_focus}_focus_followup",
        "dialogue_focus": resolved_focus,
        "candidate_response": focus_followup_text(language, resolved_focus, normalized),
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
        for value in [
            memory.get("selected_gap") if isinstance(memory, dict) else None,
            continuity.get("selected_gap"),
            continuity.get("dialogue_focus") if str(continuity.get("dialogue_focus") or "") in {"callbacks", "handoffs", "routing", "reminders", "duplicates", "visibility"} else None,
            None if is_starter_growth_plan_boundary_question(turn_transcript) else selected_sales_gap_from_transcript(turn_transcript),
        ]:
            if value:
                return str(value)
    return None


def question_type_from_response(response: str) -> str:
    normalized = normalize_text(response)
    if "?" not in response:
        return "none"
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
    if normalized_contains_any(normalized, {"would a short", "workflow review", "short workflow"}):
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
    if selected_gap:
        return "value_mapping"
    if active_topic == "qualification":
        return "qualification"
    if active_topic in {"price", "fit", "details", "effort", "terms"}:
        return "objection_or_answer"
    if active_topic == "timing":
        return "safe_next_step"
    if reason == "callback_time_confirmed":
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
    if is_starter_growth_plan_boundary_question(normalized):
        selected_gap = last_selected_gap_from_turns(turns)
    else:
        selected_gap = selected_sales_gap_from_transcript(normalized) or last_selected_gap_from_turns(turns)
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
) -> str:
    normalized = normalize_text(transcript)
    callback_semantic = memory.get("callback_semantic")
    selected_gap = str(memory.get("selected_gap") or "")
    active_topic = str(memory.get("active_topic") or "") or dialogue_focus_from_turns(turns) or "qualification"
    if callback_semantic == CALLBACK_WORKFLOW_GAP:
        if is_callback_workflow_question(normalized):
            return callback_workflow_clarification_response(language)
        return gap_progression_text(
            language,
            "callbacks",
            gap_turn_count(turns, "callbacks"),
            previous_responses(turns) | {response},
        )
    if is_topic_confusion(normalized):
        return topic_confusion_response(language)
    if is_buyer_expects_agent_to_lead(normalized):
        return seller_agenda_recovered_response(language)
    if selected_gap:
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
        )
    return workflow_review_next_step_response(language)


def repeated_question_repair(language: str, transcript: str, memory: dict, turns: list[dict], response: str) -> str:
    normalized = normalize_text(transcript)
    active_topic = str(memory.get("active_topic") or "") or dialogue_focus_from_turns(turns) or "qualification"
    selected_gap = str(memory.get("selected_gap") or "")
    if selected_gap and active_topic in {"qualification", "price", "fit", "details", "effort"}:
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
    )


def pre_speech_conversation_stability_guard(
    transcript: str,
    session_state: dict | None,
    language: str,
    candidate_response: str,
    conversation_memory: dict | None = None,
) -> dict:
    turns = list((session_state or {}).get("turns") or [])
    response = candidate_response.strip()
    memory = conversation_memory or build_conversation_memory(session_state, transcript, response, None)
    normalized = normalize_text(transcript)
    violations: list[str] = []
    repaired_response: str | None = None

    if response in previous_responses(turns):
        violations.append("duplicate_final_response")
        if memory.get("callback_semantic") == CALLBACK_SCHEDULING_REQUEST:
            repaired_response = callback_request_time_response_for_transcript(language, normalized)
        else:
            repaired_response = repeated_question_repair(language, transcript, memory, turns, response)

    if response_reopens_focus_menu(response) and (memory.get("selected_gap") or memory.get("active_topic")):
        violations.append("generic_menu_reopened_after_focus")
        repaired_response = repeated_question_repair(language, transcript, memory, turns, response)

    if memory.get("callback_semantic") == CALLBACK_WORKFLOW_GAP and (
        "what time" in response.lower() or "note for the callback" in response.lower() or "callback time" in response.lower()
    ):
        violations.append("workflow_callback_treated_as_scheduling")
        repaired_response = response_echo_repair(transcript, language, response, memory, turns)

    question_type = question_type_from_response(response)
    question_counts = dict(memory.get("asked_question_type_counts") or {})
    if question_type in {"generic_focus_menu", "callback_time"} and question_counts.get(question_type, 0) > 3:
        violations.append(f"repeated_{question_type}")
        repaired_response = repeated_question_repair(language, transcript, memory, turns, response)

    if response_starts_with_customer_phrase(transcript, response):
        violations.append("leading_customer_echo")
        repaired_response = response_echo_repair(transcript, language, response, memory, turns)

    if is_previous_question_clarification_request(normalized) and not normalized_contains_any(
        normalize_text(response),
        {"i meant", "i was asking", "in plain terms", "callbacks here mean", "route signal is for"},
    ):
        violations.append("failed_to_explain_previous_question")
        repaired_response = clarify_previous_question_text(language, str(memory.get("active_topic") or "qualification"), previous_agent_question(turns))

    if not violations:
        return {
            "applied": False,
            "reason": "conversation_stability_passed",
            "violations": [],
            "dialogue_focus": memory.get("active_topic"),
            "selected_gap": memory.get("selected_gap"),
        }

    repaired_response = repaired_response or workflow_review_next_step_response(language)
    if repaired_response == response and response in previous_responses(turns):
        repaired_response = unique_progressive_focus_text(
            language,
            str(memory.get("active_topic") or "qualification"),
            normalized,
            focus_turn_count(turns, str(memory.get("active_topic") or "qualification")) + 1,
            previous_responses(turns) | {response},
        )
    return {
        "applied": True,
        "reason": "conversation_stability_repaired",
        "violations": violations,
        "dialogue_focus": memory.get("active_topic"),
        "selected_gap": memory.get("selected_gap"),
        "candidate_response": repaired_response,
    }


def anti_loop_response(transcript: str, session_state: dict | None, language: str, generated_response: str) -> dict:
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
            "candidate_response": focus_followup_text(language, focus, normalized),
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


def continuity_response(transcript: str, session_state: dict | None, campaign: dict) -> dict:
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
    if is_starter_growth_plan_boundary_question(normalized):
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
            "candidate_response": live_demo_price_answer(language),
        }
    if callback_semantic == CALLBACK_TIME_CONFIRMATION:
        return {
            "applied": True,
            "reason": "callback_time_confirmed",
            "dialogue_focus": "timing",
            "candidate_response": callback_time_confirmed_response(language),
        }
    if is_callback_workflow_question(normalized):
        return {
            "applied": True,
            "reason": "callback_workflow_clarified",
            "dialogue_focus": resolved_focus or "details",
            "selected_gap": "callbacks",
            "callback_semantic": CALLBACK_WORKFLOW_GAP,
            "candidate_response": callback_workflow_clarification_response(language),
        }
    if is_new_trial_request_clarification(normalized):
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
            "candidate_response": value_relevance_response(language),
        }
    if is_buyer_no_question_repair(normalized):
        return {
            "applied": True,
            "reason": "buyer_no_question_recovered",
            "dialogue_focus": resolved_focus or "qualification",
            "candidate_response": buyer_no_question_response(language),
        }
    if callback_semantic == CALLBACK_WORKFLOW_GAP:
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
    call_context_recovery = call_context_recovery_response(normalized, resolved_focus, language)
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
            "candidate_response": continuity_text(language, selected_focus),
        }
    current_focus_followup = current_focus_followup_response(normalized, resolved_focus, language, turns)
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
            "candidate_response": continuity_text(language, "price", persisted=True),
        }
    if resolved_focus == "fit" and normalized_contains_any(
        normalized,
        {"fit", "relevant", "situation", "workflow", "problem", "passung", "passt"},
    ):
        return {
            "applied": True,
            "reason": "resolved_fit_focus_persisted",
            "dialogue_focus": "fit",
            "candidate_response": continuity_text(language, "fit", persisted=True),
        }
    if resolved_focus == "timing" and normalized_contains_any(
        normalized,
        {"timing", "later", "not now", "callback", "time", "zeitpunkt", "spaeter"},
    ):
        return {
            "applied": True,
            "reason": "resolved_timing_focus_persisted",
            "dialogue_focus": "timing",
            "candidate_response": continuity_text(language, "timing", persisted=True),
        }
    if resolved_focus == "effort" and normalized_contains_any(
        normalized,
        {"worth", "worth my time", "worth the effort", "reviewing options", "viewing options", "effort", "time"},
    ):
        return {
            "applied": True,
            "reason": "resolved_effort_focus_persisted",
            "dialogue_focus": "effort",
            "candidate_response": continuity_text(language, "effort", persisted=True),
        }
    if resolved_focus == "terms" and normalized_contains_any(
        normalized,
        {"terms", "contract terms", "conditions", "bedingungen", "vertragsbedingungen"},
    ):
        return {
            "applied": True,
            "reason": "resolved_terms_focus_persisted",
            "dialogue_focus": "terms",
            "candidate_response": continuity_text(language, "terms", persisted=True),
        }
    if resolved_focus == "details" and normalized_contains_any(
        normalized,
        {"details", "product details", "plan details", "included", "exact product"},
    ):
        return {
            "applied": True,
            "reason": "resolved_details_focus_persisted",
            "dialogue_focus": "details",
            "candidate_response": continuity_text(language, "details", persisted=True),
        }

    if selected_focus and response_asked_price_choice(previous_response) and selected_focus in {"price", "terms", "effort"}:
        return {
            "applied": True,
            "reason": f"short_answer_selected_{selected_focus}_after_price_prompt",
            "dialogue_focus": selected_focus,
            "candidate_response": continuity_text(language, selected_focus),
        }
    if selected_focus and response_asked_main_focus_choice(previous_response):
        return {
            "applied": True,
            "reason": f"short_answer_selected_{selected_focus}_after_main_focus_prompt",
            "dialogue_focus": selected_focus,
            "candidate_response": continuity_text(language, selected_focus),
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
            "candidate_response": continuity_text(language, "timing"),
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
            "candidate_response": continuity_text(language, selected_focus),
        }

    return {"applied": False, "reason": "no_session_continuity_match"}
