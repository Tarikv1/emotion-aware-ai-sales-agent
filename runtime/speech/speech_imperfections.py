#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from typing import Any

from runtime.speech.speech_interaction import is_unsafe_claim_context, suppresses_interaction_markers
from runtime.speech.speech_naturalness import ELIGIBLE_SEGMENT_TYPES, PROTECTED_SEGMENT_TYPES, normalize_language, protection_reason


SPEECH_IMPERFECTIONS_ID = "VOICE-028-controlled-delivery-imperfections-layer"

DEFAULT_PROFILE = {
    "enabled": False,
    "style": "professional-human",
    "max_imperfections_per_response": 1,
    "min_chars_for_imperfection": 60,
    "allow_clarifying_rephrases": True,
    "allow_breath_pauses": True,
    "allow_soft_restarts": True,
    "protected_segment_types": sorted(PROTECTED_SEGMENT_TYPES),
}

CLARIFYING_REPHRASES = {
    "en": ["Actually,", "I mean,", "More simply,"],
    "de": ["Also,", "Genauer gesagt,", "Anders gesagt,"],
}

SOFT_RESTARTS = {
    "en": ["Let me put it this way,"],
    "de": ["Ich sage es so,"],
}

LANGUAGE_SPECIFIC_IMPERFECTIONS = {
    "en": ("actually", "i mean", "more simply", "let me put it this way"),
    "de": ("also", "genauer gesagt", "anders gesagt", "ich sage es so"),
}

EVALUATION_RUBRIC = {
    "believability": "Does the small imperfection make the delivery feel less machine-perfect?",
    "professionalism": "Does the agent remain clear, competent, and sales-appropriate?",
    "trust": "Does the imperfection avoid sounding evasive, uncertain, or manipulative?",
    "placement": "Does the imperfection occur at a sentence or thought boundary?",
    "protected_text_safety": "Do campaign questions, disclosures, and compliance lines stay exact?",
}


def stable_index(seed: str, length: int) -> int:
    if length <= 0:
        return 0
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % length


def stable_range(seed: str, minimum: int, maximum: int) -> int:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    fraction = int(digest[:8], 16) / 0xFFFFFFFF
    return int(round(minimum + ((maximum - minimum) * fraction)))


def speech_imperfections_profile_from_campaign(campaign: dict[str, Any]) -> dict[str, Any]:
    profile = deepcopy(DEFAULT_PROFILE)
    profile.update(campaign.get("speech_imperfections", {}))
    try:
        profile["max_imperfections_per_response"] = max(0, int(profile.get("max_imperfections_per_response", 0)))
    except (TypeError, ValueError):
        profile["max_imperfections_per_response"] = DEFAULT_PROFILE["max_imperfections_per_response"]
    try:
        profile["min_chars_for_imperfection"] = max(0, int(profile.get("min_chars_for_imperfection", 0)))
    except (TypeError, ValueError):
        profile["min_chars_for_imperfection"] = DEFAULT_PROFILE["min_chars_for_imperfection"]
    return profile


def segment_is_eligible(segment: dict[str, Any], campaign: dict[str, Any], profile: dict[str, Any]) -> bool:
    if protection_reason(segment, campaign, profile) is not None:
        return False
    if segment.get("allow_speech_imperfections") is False:
        return False
    if segment.get("allow_speech_imperfections") is True:
        return True
    return segment.get("segment_type") in ELIGIBLE_SEGMENT_TYPES


def lower_first_alpha(text: str) -> str:
    for index, char in enumerate(text):
        if char.isalpha():
            return text[:index] + char.lower() + text[index + 1 :]
    return text


def split_first_sentence(text: str) -> tuple[str, str] | None:
    match = re.search(r"([.!?])\s+", text)
    if not match:
        return None
    first = text[: match.end()].strip()
    rest = text[match.end() :].strip()
    if not first or not rest:
        return None
    return first, rest


def phrase_pool(language: str, profile: dict[str, Any]) -> list[tuple[str, str]]:
    normalized = normalize_language(language)
    pool: list[tuple[str, str]] = []
    if profile.get("allow_clarifying_rephrases", True):
        pool.extend(("clarifying_rephrase", phrase) for phrase in CLARIFYING_REPHRASES[normalized])
    if profile.get("allow_soft_restarts", True):
        pool.extend(("soft_restart", phrase) for phrase in SOFT_RESTARTS[normalized])
    return pool


def build_visible_imperfection(
    segment: dict[str, Any],
    text: str,
    language: str,
    profile: dict[str, Any],
    seed: str,
) -> dict[str, Any] | None:
    sentence_parts = split_first_sentence(text)
    if sentence_parts is None:
        return None
    pool = phrase_pool(language, profile)
    if not pool:
        return None
    imperfection_type, marker_text = pool[stable_index(f"{seed}:phrase", len(pool))]
    return {
        "imperfection_id": f"{segment.get('segment_id', 'segment')}:controlled_imperfection",
        "imperfection_type": imperfection_type,
        "segment_id": segment.get("segment_id"),
        "language": normalize_language(language),
        "visible": True,
        "marker_text": marker_text,
        "placement": "sentence_boundary",
        "pause_ms": stable_range(f"{seed}:pause", 110, 240),
        "safety_note": "Eligible freeform speech only; does not change protected campaign text or regulated claims.",
    }


def apply_visible_imperfection(text: str, imperfection: dict[str, Any]) -> str:
    sentence_parts = split_first_sentence(text)
    if sentence_parts is None:
        return text
    first, rest = sentence_parts
    marker_text = str(imperfection.get("marker_text", "")).strip()
    if not marker_text:
        return text
    return f"{first} {marker_text} {lower_first_alpha(rest)}"


def build_imperfections_for_segment(
    *,
    segment: dict[str, Any],
    campaign: dict[str, Any],
    profile: dict[str, Any],
    language: str,
    seed: str,
    customer_state: dict[str, Any],
    imperfection_count: int,
) -> list[dict[str, Any]]:
    if imperfection_count >= profile["max_imperfections_per_response"]:
        return []
    if not profile.get("enabled", False):
        return []
    if suppresses_interaction_markers(customer_state):
        return []
    if is_unsafe_claim_context(customer_state, language):
        return []
    if not segment_is_eligible(segment, campaign, profile):
        return []

    text = str(segment.get("text", ""))
    if len(text) < profile.get("min_chars_for_imperfection", 0):
        return []

    visible = build_visible_imperfection(segment, text, language, profile, seed)
    if visible is not None:
        return [visible]

    if profile.get("allow_breath_pauses", True):
        return [
            {
                "imperfection_id": f"{segment.get('segment_id', 'segment')}:breath_pause",
                "imperfection_type": "breath_pause",
                "segment_id": segment.get("segment_id"),
                "language": normalize_language(language),
                "visible": False,
                "marker_text": "",
                "placement": "thought_boundary",
                "pause_ms": stable_range(f"{seed}:breath", 120, 220),
                "safety_note": "Provider-neutral breath-like pause only; visible wording stays unchanged.",
            }
        ]
    return []


def marker_has_language_mismatch(imperfection: dict[str, Any], language: str) -> bool:
    text = str(imperfection.get("marker_text", "")).lower()
    if not text:
        return False
    other_language = "de" if normalize_language(language) == "en" else "en"
    return any(fragment in text for fragment in LANGUAGE_SPECIFIC_IMPERFECTIONS[other_language])


def validate_output_segments(
    output_segments: list[dict[str, Any]],
    imperfections: list[dict[str, Any]],
    language: str,
    unsafe_context: bool,
) -> dict[str, Any]:
    protected_segment_changes = []
    protected_imperfection_violations = []
    language_mismatched_imperfections = []
    unsafe_visible_imperfections = []

    for segment in output_segments:
        if segment.get("protection_reason") and segment.get("text_before") != segment.get("text_after"):
            protected_segment_changes.append(
                {
                    "segment_id": segment.get("segment_id"),
                    "reason": segment.get("protection_reason"),
                    "text_before": segment.get("text_before"),
                    "text_after": segment.get("text_after"),
                }
            )
        if segment.get("protection_reason") and segment.get("imperfections"):
            protected_imperfection_violations.append(
                {
                    "segment_id": segment.get("segment_id"),
                    "reason": segment.get("protection_reason"),
                    "imperfections": segment.get("imperfections"),
                }
            )

    for imperfection in imperfections:
        if marker_has_language_mismatch(imperfection, language):
            language_mismatched_imperfections.append(imperfection)
        if unsafe_context and imperfection.get("visible"):
            unsafe_visible_imperfections.append(imperfection)

    passed = not (
        protected_segment_changes
        or protected_imperfection_violations
        or language_mismatched_imperfections
        or unsafe_visible_imperfections
    )
    return {
        "passed": passed,
        "protected_segment_changes": protected_segment_changes,
        "protected_imperfection_violations": protected_imperfection_violations,
        "language_mismatched_imperfections": language_mismatched_imperfections,
        "unsafe_visible_imperfections": unsafe_visible_imperfections,
    }


def apply_speech_imperfections(
    *,
    campaign: dict[str, Any],
    segments: list[dict[str, Any]],
    language: str | None = None,
    seed: str = "",
    customer_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_language = normalize_language(language or campaign.get("language"))
    profile = speech_imperfections_profile_from_campaign(campaign)
    state = customer_state or {}
    unsafe_context = is_unsafe_claim_context(state, normalized_language)

    output_segments: list[dict[str, Any]] = []
    imperfections: list[dict[str, Any]] = []

    for index, segment in enumerate(segments):
        text_before = str(segment.get("text", ""))
        reason = protection_reason(segment, campaign, profile)
        eligible = segment_is_eligible(segment, campaign, profile)
        segment_seed = f"{seed}:{segment.get('segment_id', index)}"
        segment_imperfections = build_imperfections_for_segment(
            segment=segment,
            campaign=campaign,
            profile=profile,
            language=normalized_language,
            seed=segment_seed,
            customer_state=state,
            imperfection_count=len(imperfections),
        )
        text_after = text_before
        for imperfection in segment_imperfections:
            if imperfection.get("visible"):
                text_after = apply_visible_imperfection(text_after, imperfection)
        imperfections.extend(segment_imperfections)
        output_segments.append(
            {
                "segment_id": segment.get("segment_id", f"segment-{index}"),
                "segment_type": segment.get("segment_type"),
                "source": segment.get("source"),
                "text_before": text_before,
                "text_after": text_after,
                "eligible": eligible,
                "protection_reason": reason,
                "imperfections": segment_imperfections,
            }
        )

    validation = validate_output_segments(
        output_segments=output_segments,
        imperfections=imperfections,
        language=normalized_language,
        unsafe_context=unsafe_context,
    )
    tts_text = " ".join(segment["text_after"] for segment in output_segments if segment.get("text_after")).strip()
    return {
        "speech_imperfections_id": SPEECH_IMPERFECTIONS_ID,
        "language": normalized_language,
        "profile": profile,
        "customer_state_used": state,
        "unsafe_claim_context": unsafe_context,
        "imperfections": imperfections,
        "imperfection_count": len(imperfections),
        "output_segments": output_segments,
        "tts_text": tts_text,
        "evaluation_rubric": deepcopy(EVALUATION_RUBRIC),
        "validation": validation,
        "provider_calls_made": False,
        "customer_audio_uploaded": False,
        "voice_cloning_used": False,
    }
