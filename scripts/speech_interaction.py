#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from typing import Any

from speech_naturalness import ELIGIBLE_SEGMENT_TYPES, PROTECTED_SEGMENT_TYPES, normalize_language, protection_reason


SPEECH_INTERACTION_ID = "VOICE-026-interaction-prosody-layer"

DEFAULT_PROFILE = {
    "enabled": True,
    "style": "professional-human",
    "max_markers_per_response": 2,
    "allow_backchannels": True,
    "allow_latency_acknowledgement": True,
    "allow_sales_pace_variation": True,
    "protected_segment_types": sorted(PROTECTED_SEGMENT_TYPES),
}

LATENCY_ACKNOWLEDGEMENTS = {
    "en": ["Let me check that.", "I can check that."],
    "de": ["Das pruefe ich kurz.", "Ich schaue kurz nach."],
}

NEUTRAL_BACKCHANNELS = {
    "en": ["I understand.", "That makes sense."],
    "de": ["Ich verstehe.", "Das verstehe ich."],
}

AGREEMENT_MARKERS = {
    "en": ("yes", "exactly", "that's right", "right"),
    "de": ("ja", "genau", "richtig"),
}

LANGUAGE_SPECIFIC_MARKERS = {
    "en": ("let me", "i can check", "i understand", "that makes sense"),
    "de": ("das pruefe", "ich schaue", "ich verstehe", "das verstehe"),
}

SUPPRESSED_EMOTIONS = {"angry", "hostile", "abusive"}

UNSAFE_CLAIM_TERMS = {
    "en": ("guaranteed", "guarantee", "save me money", "payout", "covered for sure"),
    "de": ("garantiert", "garantie", "auszahlung", "sicher abgedeckt", "spart mir geld"),
}

EVALUATION_RUBRIC = {
    "naturalness": "Does the response sound like a live professional rather than a fixed script?",
    "trust": "Does the response avoid false agreement, pressure, and over-familiarity?",
    "confidence": "Does the agent sound clear and capable without sounding theatrical?",
    "warmth": "Does the agent acknowledge the customer without becoming casual or manipulative?",
    "pace": "Does the response include bounded pace variation instead of a flat constant rate?",
    "interruption_safety": "Does the agent avoid talking over stop/refusal signals or protected handoff moments?",
    "sales_usefulness": "Does the prosody support forward motion toward the campaign goal?",
    "protected_text_safety": "Do campaign questions, disclosures, and compliance lines stay exact?",
}


def stable_index(seed: str, length: int) -> int:
    if length <= 0:
        return 0
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % length


def stable_range(seed: str, minimum: float, maximum: float, digits: int = 3) -> float:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    fraction = int(digest[:8], 16) / 0xFFFFFFFF
    return round(minimum + ((maximum - minimum) * fraction), digits)


def speech_interaction_profile_from_campaign(campaign: dict[str, Any]) -> dict[str, Any]:
    profile = deepcopy(DEFAULT_PROFILE)
    profile.update(campaign.get("speech_interaction", {}))
    try:
        profile["max_markers_per_response"] = max(0, int(profile.get("max_markers_per_response", 0)))
    except (TypeError, ValueError):
        profile["max_markers_per_response"] = DEFAULT_PROFILE["max_markers_per_response"]
    return profile


def normalize_state(customer_state: dict[str, Any] | None) -> dict[str, Any]:
    return customer_state or {}


def is_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "1", "y"}
    return bool(value)


def suppresses_interaction_markers(customer_state: dict[str, Any]) -> bool:
    emotion = str(customer_state.get("emotion", "")).lower()
    if emotion in SUPPRESSED_EMOTIONS:
        return True
    for key in ("stop_intent", "do_not_call", "human_handoff_requested", "customer_interrupted_with_stop"):
        if is_truthy(customer_state.get(key)):
            return True
    phrase = " ".join(str(customer_state.get(key, "")) for key in ("customer_phrase", "utterance", "transcript"))
    normalized = phrase.lower()
    return any(stop_word in normalized for stop_word in ("stop calling", "do not call", "hang up", "auflegen"))


def is_unsafe_claim_context(customer_state: dict[str, Any], language: str) -> bool:
    for key in ("unsafe_claim_present", "claim_safety_risk", "contains_unsafe_claim", "forbidden_claim_risk"):
        if is_truthy(customer_state.get(key)):
            return True
    text = " ".join(str(customer_state.get(key, "")) for key in ("customer_claim", "customer_phrase", "utterance"))
    lowered = text.lower()
    terms = UNSAFE_CLAIM_TERMS.get(normalize_language(language), ())
    return any(term in lowered for term in terms)


def needs_latency_acknowledgement(customer_state: dict[str, Any]) -> bool:
    if is_truthy(customer_state.get("requires_lookup")):
        return True
    try:
        return int(customer_state.get("processing_expected_ms", 0)) >= 1200
    except (TypeError, ValueError):
        return False


def segment_is_eligible(segment: dict[str, Any], campaign: dict[str, Any], profile: dict[str, Any]) -> bool:
    if protection_reason(segment, campaign, profile) is not None:
        return False
    if segment.get("allow_interaction_prosody") is False:
        return False
    if segment.get("allow_interaction_prosody") is True:
        return True
    return segment.get("segment_type") in ELIGIBLE_SEGMENT_TYPES


def select_phrase(pool: list[str], seed: str, marker_type: str) -> str:
    return pool[stable_index(f"{seed}:{marker_type}", len(pool))]


def prepend_sentence_marker(text: str, marker_text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return marker_text
    if stripped.lower().startswith(marker_text.lower()):
        return stripped
    return f"{marker_text} {stripped}"


def build_latency_marker(segment: dict[str, Any], language: str, seed: str) -> dict[str, Any]:
    marker_text = select_phrase(LATENCY_ACKNOWLEDGEMENTS[language], seed, "latency")
    return {
        "marker_id": f"{segment.get('segment_id', 'segment')}:latency_acknowledgement",
        "marker_type": "latency_acknowledgement",
        "segment_id": segment.get("segment_id"),
        "language": language,
        "visible": True,
        "marker_text": marker_text,
        "placement": "pre_answer",
        "pause_ms": 220,
        "pitch_intent": "warm-steady",
        "rate_multiplier": 0.98,
        "safety_note": "Latency acknowledgement is neutral and does not agree with customer claims.",
    }


def build_neutral_backchannel(segment: dict[str, Any], language: str, seed: str, unsafe_context: bool) -> dict[str, Any]:
    pool = [NEUTRAL_BACKCHANNELS[language][0]] if unsafe_context else NEUTRAL_BACKCHANNELS[language]
    marker_text = select_phrase(pool, seed, "neutral_backchannel")
    return {
        "marker_id": f"{segment.get('segment_id', 'segment')}:neutral_backchannel",
        "marker_type": "neutral_backchannel",
        "segment_id": segment.get("segment_id"),
        "language": language,
        "visible": True,
        "marker_text": marker_text,
        "placement": "pre_answer",
        "pause_ms": 180,
        "pitch_intent": "warm-slight-rise",
        "rate_multiplier": 0.99,
        "safety_note": "Neutral acknowledgement; not an agreement marker.",
    }


def build_sales_pace_marker(segment: dict[str, Any], language: str, seed: str, customer_state: dict[str, Any]) -> dict[str, Any]:
    emotion = str(customer_state.get("emotion", "")).lower()
    if emotion in {"anxious", "worried", "confused"}:
        rate_multiplier = stable_range(f"{seed}:careful-rate", 0.97, 1.02)
        pitch_intent = "warm-steady"
    else:
        rate_multiplier = stable_range(f"{seed}:sales-rate", 1.04, 1.10)
        pitch_intent = "confident-forward"
    return {
        "marker_id": f"{segment.get('segment_id', 'segment')}:sales_pace_variation",
        "marker_type": "sales_pace_variation",
        "segment_id": segment.get("segment_id"),
        "language": language,
        "visible": False,
        "marker_text": "",
        "placement": "whole_segment",
        "pause_ms": 0,
        "pitch_intent": pitch_intent,
        "rate_multiplier": rate_multiplier,
        "safety_note": "Provider-neutral pace cue; does not alter campaign wording.",
    }


def marker_has_language_mismatch(marker: dict[str, Any], language: str) -> bool:
    text = str(marker.get("marker_text", "")).lower()
    if not text:
        return False
    other_language = "de" if language == "en" else "en"
    return any(fragment in text for fragment in LANGUAGE_SPECIFIC_MARKERS[other_language])


def marker_is_unsafe_agreement(marker: dict[str, Any], language: str) -> bool:
    text = str(marker.get("marker_text", "")).lower()
    if not text:
        return False
    for phrase in AGREEMENT_MARKERS.get(language, ()):
        if re.search(rf"\b{re.escape(phrase)}\b", text):
            return True
    return False


def build_markers_for_segment(
    *,
    segment: dict[str, Any],
    campaign: dict[str, Any],
    profile: dict[str, Any],
    language: str,
    seed: str,
    customer_state: dict[str, Any],
    marker_count: int,
) -> list[dict[str, Any]]:
    if marker_count >= profile["max_markers_per_response"]:
        return []
    if not profile.get("enabled", True) or suppresses_interaction_markers(customer_state):
        return []
    if not segment_is_eligible(segment, campaign, profile):
        return []

    markers: list[dict[str, Any]] = []
    unsafe_context = is_unsafe_claim_context(customer_state, language)

    if profile.get("allow_latency_acknowledgement", True) and needs_latency_acknowledgement(customer_state):
        markers.append(build_latency_marker(segment, language, seed))
    elif profile.get("allow_backchannels", True) and (
        unsafe_context or str(customer_state.get("emotion", "")).lower() in {"skeptical", "concerned", "worried", "confused"}
    ):
        markers.append(build_neutral_backchannel(segment, language, seed, unsafe_context))

    remaining = profile["max_markers_per_response"] - marker_count - len(markers)
    if remaining > 0 and profile.get("allow_sales_pace_variation", True):
        markers.append(build_sales_pace_marker(segment, language, seed, customer_state))

    return markers[: max(0, profile["max_markers_per_response"] - marker_count)]


def apply_visible_markers(text: str, markers: list[dict[str, Any]]) -> str:
    output = text
    for marker in markers:
        if marker.get("visible") and marker.get("placement") == "pre_answer":
            output = prepend_sentence_marker(output, str(marker.get("marker_text", "")))
    return output


def validate_output_segments(
    output_segments: list[dict[str, Any]],
    markers: list[dict[str, Any]],
    language: str,
    unsafe_context: bool,
) -> dict[str, Any]:
    protected_segment_changes = []
    protected_marker_violations = []
    language_mismatched_markers = []
    unsafe_agreement_markers = []
    rate_range_violations = []
    missing_rubric_keys = sorted(set(EVALUATION_RUBRIC) - set(EVALUATION_RUBRIC))

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
        if segment.get("protection_reason") and segment.get("markers"):
            protected_marker_violations.append(
                {
                    "segment_id": segment.get("segment_id"),
                    "reason": segment.get("protection_reason"),
                    "markers": segment.get("markers"),
                }
            )

    for marker in markers:
        if marker_has_language_mismatch(marker, language):
            language_mismatched_markers.append(marker)
        rate_multiplier = marker.get("rate_multiplier")
        if rate_multiplier and not (0.94 <= float(rate_multiplier) <= 1.12):
            rate_range_violations.append(marker)
        if unsafe_context and marker_is_unsafe_agreement(marker, language):
            unsafe_agreement_markers.append(marker)

    passed = not (
        protected_segment_changes
        or protected_marker_violations
        or language_mismatched_markers
        or unsafe_agreement_markers
        or rate_range_violations
        or missing_rubric_keys
    )
    return {
        "passed": passed,
        "protected_segment_changes": protected_segment_changes,
        "protected_marker_violations": protected_marker_violations,
        "language_mismatched_markers": language_mismatched_markers,
        "unsafe_agreement_markers": unsafe_agreement_markers,
        "rate_range_violations": rate_range_violations,
        "missing_rubric_keys": missing_rubric_keys,
    }


def apply_speech_interaction(
    *,
    campaign: dict[str, Any],
    segments: list[dict[str, Any]],
    language: str | None = None,
    seed: str = "",
    customer_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_language = normalize_language(language or campaign.get("language"))
    profile = speech_interaction_profile_from_campaign(campaign)
    state = normalize_state(customer_state)
    unsafe_context = is_unsafe_claim_context(state, normalized_language)

    output_segments: list[dict[str, Any]] = []
    interaction_markers: list[dict[str, Any]] = []

    for index, segment in enumerate(segments):
        text_before = str(segment.get("text", ""))
        segment_profile = deepcopy(profile)
        reason = protection_reason(segment, campaign, segment_profile)
        eligible = segment_is_eligible(segment, campaign, segment_profile)
        segment_seed = f"{seed}:{segment.get('segment_id', index)}"
        markers = build_markers_for_segment(
            segment=segment,
            campaign=campaign,
            profile=segment_profile,
            language=normalized_language,
            seed=segment_seed,
            customer_state=state,
            marker_count=len(interaction_markers),
        )
        text_after = apply_visible_markers(text_before, markers)
        interaction_markers.extend(markers)
        output_segments.append(
            {
                "segment_id": segment.get("segment_id", f"segment-{index}"),
                "segment_type": segment.get("segment_type"),
                "source": segment.get("source"),
                "text_before": text_before,
                "text_after": text_after,
                "eligible": eligible,
                "protection_reason": reason,
                "markers": markers,
            }
        )

    validation = validate_output_segments(
        output_segments=output_segments,
        markers=interaction_markers,
        language=normalized_language,
        unsafe_context=unsafe_context,
    )
    tts_text = " ".join(segment["text_after"] for segment in output_segments if segment.get("text_after")).strip()
    return {
        "speech_interaction_id": SPEECH_INTERACTION_ID,
        "language": normalized_language,
        "profile": profile,
        "customer_state_used": state,
        "unsafe_claim_context": unsafe_context,
        "interaction_markers": interaction_markers,
        "marker_count": len(interaction_markers),
        "output_segments": output_segments,
        "tts_text": tts_text,
        "evaluation_rubric": deepcopy(EVALUATION_RUBRIC),
        "validation": validation,
        "provider_calls_made": False,
        "customer_audio_uploaded": False,
        "voice_cloning_used": False,
    }
