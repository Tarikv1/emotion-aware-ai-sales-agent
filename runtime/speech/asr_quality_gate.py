from __future__ import annotations

import re

ASR_LOW_CONFIDENCE_THRESHOLD = 0.45


def normalize_transcript(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def asr_fragment_response(language: str) -> str:
    if language.startswith("de"):
        return "Ich habe nur einen Teil verstanden. Bitte wiederholen Sie die Frage in einem Satz."
    return "I only caught part of that. Please repeat the question in one sentence."


def asr_low_confidence_response(language: str) -> str:
    if language.startswith("de"):
        return "Ich bin mir bei der Spracherkennung nicht sicher. Bitte wiederholen Sie die Frage kurz."
    return "I am not confident I caught that correctly. Please repeat the question briefly."


def looks_like_asr_fragment(normalized: str, selected_focus: str | None) -> bool:
    if selected_focus:
        return False
    words = normalized.split()
    if not words:
        return True
    fragment_endings = {"a", "an", "the", "about", "of", "to", "for", "with", "and", "or", "but"}
    return len(words) <= 8 and words[-1] in fragment_endings


def evaluate_asr_quality(transcript: str, asr_confidence: float | None) -> dict:
    normalized = normalize_transcript(transcript)
    if not normalized:
        return {
            "accepted": False,
            "reason": "empty_transcript",
            "low_confidence_threshold": ASR_LOW_CONFIDENCE_THRESHOLD,
            "confidence": asr_confidence,
        }
    if asr_confidence is not None and asr_confidence < ASR_LOW_CONFIDENCE_THRESHOLD:
        return {
            "accepted": False,
            "reason": "low_confidence",
            "low_confidence_threshold": ASR_LOW_CONFIDENCE_THRESHOLD,
            "confidence": asr_confidence,
        }
    return {
        "accepted": True,
        "reason": "accepted",
        "low_confidence_threshold": ASR_LOW_CONFIDENCE_THRESHOLD,
        "confidence": asr_confidence,
    }


def repair_response_for_quality_gate(language: str, quality_gate: dict) -> dict:
    if quality_gate["reason"] == "low_confidence":
        return {
            "applied": True,
            "reason": "asr_low_confidence_repair",
            "candidate_response": asr_low_confidence_response(language),
        }
    return {
        "applied": True,
        "reason": "asr_empty_transcript_repair",
        "candidate_response": asr_fragment_response(language),
    }
