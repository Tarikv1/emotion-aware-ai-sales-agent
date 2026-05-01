#!/usr/bin/env python3
import re


VOICE_MILESTONE = "VOICE-006"
POLICY_ID = "VOICE-006-safe-interruption-policy"

LANGUAGE_PHRASE_PACKS = {
    "en": {
        "language_name": "English",
        "short_acknowledgements": [
            "ok",
            "okay",
            "yes",
            "yeah",
            "yep",
            "mhm",
            "uh huh",
            "alright",
            "i see",
            "got it",
        ],
        "short_ambiguous_interruptions": [
            "wait",
            "wait a second",
            "wait a minute",
            "huh",
            "what",
            "sorry",
            "one second",
            "hold on",
            "hang on",
        ],
        "stop_or_refusal_phrases": [
            "stop calling",
            "do not call",
            "don't call",
            "dont call",
            "do not contact me",
            "don't contact me",
            "stop",
            "no thanks",
            "not interested",
            "leave me alone",
            "remove my number",
            "take me off your list",
        ],
        "human_request_phrases": [
            "human",
            "real person",
            "person call",
            "specialist",
            "agent",
            "representative",
            "someone call me",
        ],
        "question_phrases": [
            "what",
            "why",
            "how",
            "can you",
            "could you",
            "does that",
            "what does",
            "explain",
            "mean",
            "question",
        ],
        "clarification_response": "I paused there. Was something unclear, or did you want to ask something?",
    },
    "de": {
        "language_name": "German",
        "short_acknowledgements": [
            "ja",
            "ok",
            "okay",
            "mhm",
            "verstanden",
            "alles klar",
            "gut",
            "passt",
        ],
        "short_ambiguous_interruptions": [
            "warte",
            "warten sie",
            "moment",
            "moment bitte",
            "kurz",
            "was",
            "wie bitte",
            "sorry",
            "entschuldigung",
            "haeh",
            "häh",
        ],
        "stop_or_refusal_phrases": [
            "rufen sie mich nicht mehr an",
            "rufen sie mich bitte nicht mehr an",
            "rufen sie nicht mehr an",
            "nicht mehr an",
            "kein interesse",
            "ich habe kein interesse",
            "nein danke",
            "lassen sie mich in ruhe",
            "will ich nicht",
            "stopp",
            "stoppen sie",
        ],
        "human_request_phrases": [
            "mitarbeiter",
            "mensch",
            "berater",
            "spezialist",
            "echte person",
            "person anrufen",
            "mit einem menschen",
            "jemand soll mich anrufen",
        ],
        "question_phrases": [
            "was bedeutet",
            "was heisst",
            "was heißt",
            "warum",
            "wie",
            "koennen sie",
            "können sie",
            "erklaeren",
            "erklären",
            "bedeutet",
            "frage",
        ],
        "clarification_response": "Ich habe kurz pausiert. War etwas unklar, oder wollten Sie etwas fragen?",
    },
}

GERMAN_MARKERS = [
    "rufen",
    "nicht mehr",
    "kein interesse",
    "nein danke",
    "mitarbeiter",
    "mensch",
    "berater",
    "spezialist",
    "echte person",
    "person anrufen",
    "mit einem menschen",
    "jemand soll mich anrufen",
    "was bedeutet",
    "was heisst",
    "was heißt",
    "warum",
    "wie bitte",
    "warte",
    "warten sie",
    "moment",
    "kurz",
    "entschuldigung",
    "haeh",
    "häh",
    "koennen",
    "können",
    "erklären",
    "erklaeren",
    "unklar",
    "frage",
    "verstanden",
    "alles klar",
]


def normalize(text: str) -> str:
    lowered = text.lower()
    cleaned = re.sub(r"[^a-z0-9äöüß]+", " ", lowered)
    return " ".join(cleaned.split())


def contains_any(text: str, phrases: list[str]) -> bool:
    return any(normalize(phrase) in text for phrase in phrases)


def phrase_pack(language: str) -> dict:
    return LANGUAGE_PHRASE_PACKS[language]


def phrases_for(category: str) -> list[str]:
    phrases = []
    for pack in LANGUAGE_PHRASE_PACKS.values():
        phrases.extend(pack[category])
    return phrases


def exact_phrases_for(category: str) -> set[str]:
    return {normalize(phrase) for phrase in phrases_for(category)}


def detect_language(normalized: str, language_hint: str | None = None) -> str:
    if language_hint in LANGUAGE_PHRASE_PACKS:
        return language_hint
    if contains_any(normalized, GERMAN_MARKERS):
        return "de"
    return "en"


def token_overlap_ratio(transcript: str, agent_response: str) -> float:
    transcript_tokens = set(normalize(transcript).split())
    response_tokens = set(normalize(agent_response).split())
    if not transcript_tokens or not response_tokens:
        return 0.0
    return len(transcript_tokens & response_tokens) / len(transcript_tokens)


def looks_like_echo(transcript: str, agent_response: str) -> bool:
    normalized_transcript = normalize(transcript)
    normalized_response = normalize(agent_response)
    if not normalized_transcript or not normalized_response:
        return False
    if len(normalized_transcript.split()) >= 4 and normalized_transcript in normalized_response:
        return True
    return token_overlap_ratio(transcript, agent_response) >= 0.72


def base_decision(
    *,
    audio_detected: bool,
    speech_detected: bool,
    customer_speech_detected: bool,
    interruption_type: str,
    interruption_confirmed: bool,
    agent_speech_action: str,
    send_to_agent_core: bool,
    clarification_response: str | None,
    rationale: str,
    detected_language: str,
) -> dict:
    return {
        "voice_milestone": VOICE_MILESTONE,
        "policy_id": POLICY_ID,
        "detected_language": detected_language,
        "audio_detected": audio_detected,
        "speech_detected": speech_detected,
        "customer_speech_detected": customer_speech_detected,
        "interruption_type": interruption_type,
        "interruption_confirmed": interruption_confirmed,
        "agent_speech_action": agent_speech_action,
        "send_to_agent_core": send_to_agent_core,
        "clarification_response": clarification_response,
        "rationale": rationale,
    }


def interruption_policy_metadata() -> dict:
    return {
        "voice_milestone": VOICE_MILESTONE,
        "policy_id": POLICY_ID,
        "principle": "Raw audio alone does not cancel agent speech; only likely customer interruption can pause or cancel.",
        "interruption_types": [
            "no_active_agent_speech",
            "noise_or_no_transcript",
            "likely_echo",
            "short_acknowledgement",
            "short_ambiguous_interruption",
            "clear_customer_question",
            "stop_or_refusal",
            "human_request",
            "meaningful_customer_interruption",
        ],
        "safe_actions": [
            "continue-speaking",
            "pause-and-ask-clarification",
            "cancel-agent-speech-and-process-turn",
        ],
        "supported_languages": list(LANGUAGE_PHRASE_PACKS.keys()),
        "language_phrase_pack_summary": {
            language: {
                "language_name": pack["language_name"],
                "short_acknowledgements": len(pack["short_acknowledgements"]),
                "short_ambiguous_interruptions": len(pack["short_ambiguous_interruptions"]),
                "stop_or_refusal_phrases": len(pack["stop_or_refusal_phrases"]),
                "human_request_phrases": len(pack["human_request_phrases"]),
                "question_phrases": len(pack["question_phrases"]),
            }
            for language, pack in LANGUAGE_PHRASE_PACKS.items()
        },
    }


def classify_interruption_candidate(
    transcript: str,
    agent_response: str,
    audio_event_type: str = "speech-final",
    agent_is_speaking: bool = True,
    language_hint: str | None = None,
) -> dict:
    normalized = normalize(transcript)
    audio_detected = audio_event_type not in {"none", "no-audio"}
    detected_language = detect_language(normalized, language_hint)
    detected_pack = phrase_pack(detected_language)

    if not agent_is_speaking:
        return base_decision(
            audio_detected=audio_detected,
            speech_detected=bool(normalized),
            customer_speech_detected=False,
            interruption_type="no_active_agent_speech",
            interruption_confirmed=False,
            agent_speech_action="continue-speaking",
            send_to_agent_core=False,
            clarification_response=None,
            rationale="There is no active agent speech to interrupt.",
            detected_language=detected_language,
        )

    if audio_event_type in {"background-noise", "audio-only"} or not normalized:
        return base_decision(
            audio_detected=audio_detected,
            speech_detected=False,
            customer_speech_detected=False,
            interruption_type="noise_or_no_transcript",
            interruption_confirmed=False,
            agent_speech_action="continue-speaking",
            send_to_agent_core=False,
            clarification_response=None,
            rationale="Raw audio or empty transcript is not enough to cancel the agent.",
            detected_language=detected_language,
        )

    if looks_like_echo(transcript, agent_response):
        return base_decision(
            audio_detected=True,
            speech_detected=True,
            customer_speech_detected=False,
            interruption_type="likely_echo",
            interruption_confirmed=False,
            agent_speech_action="continue-speaking",
            send_to_agent_core=False,
            clarification_response=None,
            rationale="Transcript overlaps strongly with the current agent response, so it is treated as likely echo.",
            detected_language=detected_language,
        )

    if contains_any(normalized, phrases_for("stop_or_refusal_phrases")):
        return base_decision(
            audio_detected=True,
            speech_detected=True,
            customer_speech_detected=True,
            interruption_type="stop_or_refusal",
            interruption_confirmed=True,
            agent_speech_action="cancel-agent-speech-and-process-turn",
            send_to_agent_core=True,
            clarification_response=None,
            rationale="Stop or refusal language must interrupt and be handled by call-control policy.",
            detected_language=detected_language,
        )

    if contains_any(normalized, phrases_for("human_request_phrases")):
        return base_decision(
            audio_detected=True,
            speech_detected=True,
            customer_speech_detected=True,
            interruption_type="human_request",
            interruption_confirmed=True,
            agent_speech_action="cancel-agent-speech-and-process-turn",
            send_to_agent_core=True,
            clarification_response=None,
            rationale="Human request should interrupt and route through escalation policy.",
            detected_language=detected_language,
        )

    if normalized in exact_phrases_for("short_acknowledgements"):
        return base_decision(
            audio_detected=True,
            speech_detected=True,
            customer_speech_detected=True,
            interruption_type="short_acknowledgement",
            interruption_confirmed=False,
            agent_speech_action="continue-speaking",
            send_to_agent_core=False,
            clarification_response=None,
            rationale="Short acknowledgement is not enough to stop the agent.",
            detected_language=detected_language,
        )

    if normalized in exact_phrases_for("short_ambiguous_interruptions") or len(normalized) <= 8:
        return base_decision(
            audio_detected=True,
            speech_detected=True,
            customer_speech_detected=True,
            interruption_type="short_ambiguous_interruption",
            interruption_confirmed=True,
            agent_speech_action="pause-and-ask-clarification",
            send_to_agent_core=False,
            clarification_response=detected_pack["clarification_response"],
            rationale="Short meaningful interruption should pause and clarify rather than assume intent.",
            detected_language=detected_language,
        )

    if "?" in transcript or contains_any(normalized, phrases_for("question_phrases")):
        return base_decision(
            audio_detected=True,
            speech_detected=True,
            customer_speech_detected=True,
            interruption_type="clear_customer_question",
            interruption_confirmed=True,
            agent_speech_action="cancel-agent-speech-and-process-turn",
            send_to_agent_core=True,
            clarification_response=None,
            rationale="Clear question should stop current agent speech and become the next customer turn.",
            detected_language=detected_language,
        )

    return base_decision(
        audio_detected=True,
        speech_detected=True,
        customer_speech_detected=True,
        interruption_type="meaningful_customer_interruption",
        interruption_confirmed=True,
        agent_speech_action="cancel-agent-speech-and-process-turn",
        send_to_agent_core=True,
        clarification_response=None,
        rationale="Meaningful non-echo customer speech should interrupt and be processed as a new turn.",
        detected_language=detected_language,
    )
