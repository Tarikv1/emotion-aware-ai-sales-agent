"""Backend-neutral prosody control contract for future audio adapters.

This module defines allowed values only. It does not shape live spoken text,
call TTS providers, or inject backend-specific inline tags.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


PROSODY_OBJECT_FIELDS = (
    "voice_intent",
    "buyer_emotion",
    "sales_move",
    "pace",
    "warmth",
    "confidence",
    "energy",
    "pause_policy",
    "emphasis_terms",
    "avoid",
    "backend_hints",
)

STANDARD_VALUES = {
    "pace": ("slow", "medium_slow", "medium", "medium_fast"),
    "warmth": ("neutral", "warm", "very_warm"),
    "confidence": ("soft", "calm", "confident", "assertive"),
    "energy": ("low", "medium", "high"),
    "pause_policy": (
        "none",
        "short_after_opening_clause",
        "short_before_recommendation",
        "short_after_objection_ack",
    ),
    "voice_intent": (
        "clarify_without_pressure",
        "reassure_confused_buyer",
        "handle_price_objection",
        "recommend_with_confidence",
        "close_low_pressure",
        "respect_boundary",
        "terminal_close",
    ),
    "buyer_emotion": (
        "neutral",
        "confused",
        "skeptical",
        "impatient",
        "price_sensitive",
        "interested",
        "frustrated",
    ),
}


@dataclass(frozen=True)
class ProsodyControl:
    voice_intent: str
    buyer_emotion: str
    sales_move: str
    pace: str
    warmth: str
    confidence: str
    energy: str
    pause_policy: str
    emphasis_terms: list[str] = field(default_factory=list)
    avoid: list[str] = field(default_factory=list)
    backend_hints: dict[str, Any] = field(default_factory=dict)


def empty_prosody_control() -> dict[str, Any]:
    return {
        "voice_intent": "",
        "buyer_emotion": "",
        "sales_move": "",
        "pace": "",
        "warmth": "",
        "confidence": "",
        "energy": "",
        "pause_policy": "",
        "emphasis_terms": [],
        "avoid": [],
        "backend_hints": {},
    }
