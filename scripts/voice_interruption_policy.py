#!/usr/bin/env python3
import re


VOICE_MILESTONE = "VOICE-006"
POLICY_ID = "VOICE-006-safe-interruption-policy"

SHORT_ACKNOWLEDGEMENTS = {
    "ok",
    "okay",
    "yes",
    "yeah",
    "yep",
    "mhm",
    "uh huh",
    "alright",
    "i see",
    "verstanden",
    "ja",
}

SHORT_AMBIGUOUS_INTERRUPTION = {
    "wait",
    "huh",
    "what",
    "sorry",
    "one second",
    "hold on",
    "moment",
    "kurz",
    "was",
    "wie bitte",
}

STOP_OR_REFUSAL_PHRASES = [
    "stop calling",
    "do not call",
    "don't call",
    "stop",
    "no thanks",
    "not interested",
    "leave me alone",
    "rufen sie mich nicht",
    "nicht mehr an",
]

HUMAN_REQUEST_PHRASES = [
    "human",
    "real person",
    "person call",
    "specialist",
    "agent",
    "mitarbeiter",
    "mensch",
    "person anrufen",
]

QUESTION_PHRASES = [
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
    "frage",
]


def normalize(text: str) -> str:
    lowered = text.lower()
    cleaned = re.sub(r"[^a-z0-9äöüß]+", " ", lowered)
    return " ".join(cleaned.split())


def contains_any(text: str, phrases: list[str]) -> bool:
    return any(phrase in text for phrase in phrases)


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
) -> dict:
    return {
        "voice_milestone": VOICE_MILESTONE,
        "policy_id": POLICY_ID,
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
    }


def classify_interruption_candidate(
    transcript: str,
    agent_response: str,
    audio_event_type: str = "speech-final",
    agent_is_speaking: bool = True,
) -> dict:
    normalized = normalize(transcript)
    audio_detected = audio_event_type not in {"none", "no-audio"}

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
        )

    if contains_any(normalized, STOP_OR_REFUSAL_PHRASES):
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
        )

    if contains_any(normalized, HUMAN_REQUEST_PHRASES):
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
        )

    if normalized in SHORT_ACKNOWLEDGEMENTS:
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
        )

    if normalized in SHORT_AMBIGUOUS_INTERRUPTION or len(normalized) <= 8:
        return base_decision(
            audio_detected=True,
            speech_detected=True,
            customer_speech_detected=True,
            interruption_type="short_ambiguous_interruption",
            interruption_confirmed=True,
            agent_speech_action="pause-and-ask-clarification",
            send_to_agent_core=False,
            clarification_response="I paused there. Was something unclear, or did you want to ask something?",
            rationale="Short meaningful interruption should pause and clarify rather than assume intent.",
        )

    if "?" in transcript or contains_any(normalized, QUESTION_PHRASES):
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
    )
