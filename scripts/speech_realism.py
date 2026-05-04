#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from typing import Any

from speech_naturalness import (
    ELIGIBLE_SEGMENT_TYPES,
    PROTECTED_SEGMENT_TYPES,
    PROTECTED_SOURCES,
    normalize_language,
    normalize_text,
    protection_reason,
)


SPEECH_REALISM_ID = "VOICE-023-speech-realism-layer"

DEFAULT_PROFILE = {
    "enabled": True,
    "style": "professional-human",
    "filler_frequency": "low",
    "max_bundles_per_response": 2,
    "allow_thinking_fillers": True,
    "allow_empathy_acknowledgements": True,
    "min_chars_for_thinking_bundle": 72,
    "protected_segment_types": sorted(PROTECTED_SEGMENT_TYPES),
    "pause_ms_ranges": {
        "thinking": [150, 260],
        "empathy": [120, 220],
    },
    "rate_ranges": {
        "follow_through": [1.04, 1.12],
        "empathy": [0.96, 1.03],
    },
}

FILLERS_BY_LANGUAGE = {
    "en": ["um", "uh", "hm"],
    # Keep German runtime fillers provider-readable until live tests prove umlaut forms are better.
    "de": ["hm", "also"],
}

THINKING_PATTERNS = {
    "en": [
        r"\bthe important thing is\b",
        r"\bwhat I can do is\b",
        r"\bthe safest next step is\b",
        r"\bthe practical next step is\b",
    ],
    "de": [
        r"\bWichtig ist\b",
        r"\bder sichere naechste Schritt ist\b",
        r"\bder praktische naechste Schritt ist\b",
        r"\bwas ich machen kann\b",
    ],
}

SUPPRESSED_EMOTIONS = {"angry", "furious", "hostile", "upset"}
SUPPRESSED_SEGMENT_TYPES = {"hangup", "do_not_call", "claim_boundary", "coverage_or_claim_boundary"}


def stable_unit(seed: str) -> float:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def stable_index(seed: str, length: int) -> int:
    if length <= 0:
        return 0
    return int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8], 16) % length


def stable_range_int(seed: str, low: int, high: int) -> int:
    if high <= low:
        return low
    return low + round(stable_unit(seed) * (high - low))


def stable_range_float(seed: str, low: float, high: float, digits: int = 3) -> float:
    if high <= low:
        return round(low, digits)
    return round(low + stable_unit(seed) * (high - low), digits)


def speech_realism_profile_from_campaign(campaign: dict[str, Any]) -> dict[str, Any]:
    profile = deepcopy(DEFAULT_PROFILE)
    profile.update(campaign.get("speech_realism", {}))
    try:
        profile["max_bundles_per_response"] = max(0, int(profile.get("max_bundles_per_response", 0)))
    except (TypeError, ValueError):
        profile["max_bundles_per_response"] = DEFAULT_PROFILE["max_bundles_per_response"]
    try:
        profile["min_chars_for_thinking_bundle"] = max(0, int(profile.get("min_chars_for_thinking_bundle", 0)))
    except (TypeError, ValueError):
        profile["min_chars_for_thinking_bundle"] = DEFAULT_PROFILE["min_chars_for_thinking_bundle"]
    return profile


def customer_state_suppresses_realism(customer_state: dict[str, Any] | None) -> bool:
    if not customer_state:
        return False
    emotion = str(customer_state.get("emotion", "")).lower()
    return bool(customer_state.get("stop_or_refusal")) or emotion in SUPPRESSED_EMOTIONS


def segment_is_eligible(segment: dict[str, Any], campaign: dict[str, Any], profile: dict[str, Any]) -> bool:
    if protection_reason(segment, campaign, profile) is not None:
        return False
    if segment.get("allow_speech_realism") is False or segment.get("allow_fillers") is False:
        return False
    if segment.get("segment_type") in SUPPRESSED_SEGMENT_TYPES:
        return False
    if segment.get("allow_speech_realism") is True:
        return True
    return segment.get("segment_type") in ELIGIBLE_SEGMENT_TYPES


def bundle_quota(profile: dict[str, Any], eligible_segments: list[dict[str, Any]]) -> int:
    if not profile.get("enabled", True):
        return 0
    max_bundles = int(profile.get("max_bundles_per_response", 0))
    if max_bundles <= 0 or not eligible_segments:
        return 0
    total_chars = sum(len(segment.get("text", "")) for segment in eligible_segments)
    frequency = str(profile.get("filler_frequency", "low")).lower()
    if frequency in {"off", "none", "disabled"}:
        desired = 0
    elif frequency in {"very-low", "very_low", "rare"}:
        desired = 1 if total_chars >= 120 else 0
    elif frequency == "low":
        desired = 1 if total_chars >= 70 else 0
    elif frequency == "medium":
        desired = 2 if total_chars >= 160 else 1
    else:
        desired = 2
    return min(max_bundles, desired, len(eligible_segments))


def select_filler(language: str, seed: str, inserted_count: int) -> str:
    language = normalize_language(language)
    pool = FILLERS_BY_LANGUAGE[language]
    return pool[stable_index(f"{seed}:filler:{inserted_count}", len(pool))]


def insert_filler_after_pattern(text: str, pattern: str, filler: str) -> str | None:
    match = re.search(pattern, text, re.IGNORECASE)
    if match is None:
        return None
    prefix = text[: match.end()].rstrip()
    suffix = text[match.end() :].lstrip()
    if suffix.startswith(","):
        suffix = suffix[1:].lstrip()
    return f"{prefix}, {filler}, {suffix}"


def insert_fallback_filler(text: str, filler: str) -> str:
    sentence_boundary = re.search(r"([.!?])\s+", text)
    if sentence_boundary is not None and sentence_boundary.end() < len(text):
        prefix = text[: sentence_boundary.end()].strip()
        suffix = text[sentence_boundary.end() :].lstrip()
        sentence_filler = filler[:1].upper() + filler[1:] if filler else filler
        return f"{prefix} {sentence_filler}, {suffix}"

    words = text.split()
    if len(words) < 10:
        return text
    insert_at = min(max(6, len(words) // 3), 11)
    before = words[:insert_at]
    after = words[insert_at:]
    if before and not before[-1].endswith((",", ";", ":")):
        before[-1] = f"{before[-1]},"
    return " ".join(before + [f"{filler},"] + after)


def insert_thinking_filler(text: str, filler: str, language: str) -> tuple[str, str]:
    for pattern in THINKING_PATTERNS[normalize_language(language)]:
        candidate = insert_filler_after_pattern(text, pattern, filler)
        if candidate and candidate != text:
            return candidate, "after_thinking_phrase"
    candidate = insert_fallback_filler(text, filler)
    return candidate, "fallback_mid_utterance" if candidate != text else "not_inserted"


def build_thinking_bundle(
    segment: dict[str, Any],
    language: str,
    seed: str,
    inserted_count: int,
    profile: dict[str, Any],
) -> dict[str, Any]:
    filler = select_filler(language, seed, inserted_count)
    pause_low, pause_high = profile.get("pause_ms_ranges", {}).get("thinking", [150, 260])
    rate_low, rate_high = profile.get("rate_ranges", {}).get("follow_through", [1.04, 1.12])
    return {
        "bundle_id": f"{segment.get('segment_id')}:thinking:{inserted_count + 1}",
        "bundle_type": "thinking_filler",
        "segment_id": segment.get("segment_id"),
        "segment_type": segment.get("segment_type"),
        "filler": filler,
        "position": "mid_utterance",
        "pause_ms": stable_range_int(f"{seed}:pause:{inserted_count}", int(pause_low), int(pause_high)),
        "pitch_intent": "slight-rise",
        "rate_after": stable_range_float(f"{seed}:rate:{inserted_count}", float(rate_low), float(rate_high)),
        "delivery_intent": "thinking-then-confident-follow-through",
        "safety_note": "Eligible freeform speech only; protected campaign and compliance text remains exact.",
    }


def contains_language_mismatched_filler(text: str, language: str) -> bool:
    normalized = f" {normalize_text(text)} "
    if normalize_language(language) == "de":
        return any(fragment in normalized for fragment in [" uh ", " you know ", " like "])
    return any(fragment in normalized for fragment in [" aehm ", " aeh "])


def validate_output_segments(
    input_segments: list[dict[str, Any]],
    output_segments: list[dict[str, Any]],
    bundles: list[dict[str, Any]],
    campaign: dict[str, Any],
    profile: dict[str, Any],
    language: str,
) -> dict[str, Any]:
    protected_segment_changes = []
    bundle_in_protected_segments = []
    language_mismatch_segments = []
    unsafe_pause_bundles = []
    unsafe_rate_bundles = []
    protected_ids = {
        segment.get("segment_id")
        for segment in input_segments
        if protection_reason(segment, campaign, profile) is not None
    }

    for index, (input_segment, output_segment) in enumerate(zip(input_segments, output_segments)):
        reason = protection_reason(input_segment, campaign, profile)
        if reason and input_segment.get("text", "") != output_segment["text_after"]:
            protected_segment_changes.append(index)
        if reason and output_segment["bundles"]:
            bundle_in_protected_segments.append(index)
        if output_segment["bundles"] and contains_language_mismatched_filler(output_segment["text_after"], language):
            language_mismatch_segments.append(index)

    for bundle in bundles:
        if bundle.get("segment_id") in protected_ids or bundle.get("segment_type") in PROTECTED_SEGMENT_TYPES:
            bundle_in_protected_segments.append(bundle.get("segment_id"))
        if not 90 <= int(bundle.get("pause_ms", 0)) <= 320:
            unsafe_pause_bundles.append(bundle)
        if not 0.94 <= float(bundle.get("rate_after", 1.0)) <= 1.14:
            unsafe_rate_bundles.append(bundle)

    passed = not any(
        [
            protected_segment_changes,
            bundle_in_protected_segments,
            language_mismatch_segments,
            unsafe_pause_bundles,
            unsafe_rate_bundles,
        ]
    )
    return {
        "validator": "VOICE-023 segment protection, language, and bounded speech-realism check",
        "passed": passed,
        "protected_segment_changes": protected_segment_changes,
        "bundle_in_protected_segments": bundle_in_protected_segments,
        "language_mismatch_segments": language_mismatch_segments,
        "unsafe_pause_bundles": unsafe_pause_bundles,
        "unsafe_rate_bundles": unsafe_rate_bundles,
        "notes": (
            "Speech-realism bundles stayed bounded and outside protected segments."
            if passed
            else "Speech-realism validation found protected-segment, language, or bound issues."
        ),
    }


def apply_speech_realism(
    campaign: dict[str, Any],
    segments: list[dict[str, Any]],
    language: str | None = None,
    seed: str = "",
    customer_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    language = normalize_language(language or campaign.get("language"))
    profile = speech_realism_profile_from_campaign(campaign)
    suppress_all = customer_state_suppresses_realism(customer_state)
    annotated_segments = []
    eligible_segments = []

    for index, segment in enumerate(segments):
        segment_copy = deepcopy(segment)
        reason = protection_reason(segment_copy, campaign, profile)
        eligible = (
            not suppress_all
            and reason is None
            and segment_is_eligible(segment_copy, campaign, profile)
            and len(segment_copy.get("text", "").strip()) >= int(profile.get("min_chars_for_thinking_bundle", 0))
        )
        segment_copy["_index"] = index
        segment_copy["_protected_reason"] = reason
        segment_copy["_eligible_for_speech_realism"] = eligible
        annotated_segments.append(segment_copy)
        if eligible:
            eligible_segments.append(segment_copy)

    quota = bundle_quota(profile, eligible_segments)
    inserted_count = 0
    output_segments = []
    speech_bundles = []

    for segment in annotated_segments:
        text_before = segment.get("text", "")
        text_after = text_before
        segment_bundles: list[dict[str, Any]] = []

        if (
            inserted_count < quota
            and segment["_eligible_for_speech_realism"]
            and profile.get("allow_thinking_fillers", True)
        ):
            segment_seed = f"{seed}:{segment['_index']}:{segment.get('segment_id')}:{text_before}"
            bundle = build_thinking_bundle(segment, language, segment_seed, inserted_count, profile)
            candidate, insertion_strategy = insert_thinking_filler(text_before, bundle["filler"], language)
            if candidate != text_before:
                bundle["insertion_strategy"] = insertion_strategy
                text_after = candidate
                segment_bundles.append(bundle)
                speech_bundles.append(bundle)
                inserted_count += 1

        output_segments.append(
            {
                "segment_index": segment["_index"],
                "segment_id": segment.get("segment_id"),
                "segment_type": segment.get("segment_type"),
                "source": segment.get("source"),
                "eligible_for_speech_realism": segment["_eligible_for_speech_realism"],
                "protected_reason": segment["_protected_reason"],
                "text_before": text_before,
                "text_after": text_after,
                "bundles": segment_bundles,
            }
        )

    validation = validate_output_segments(segments, output_segments, speech_bundles, campaign, profile, language)
    tts_text = " ".join(segment["text_after"].strip() for segment in output_segments if segment["text_after"].strip())
    return {
        "speech_realism_id": SPEECH_REALISM_ID,
        "language": language,
        "profile": profile,
        "segment_count": len(segments),
        "eligible_segment_count": len(eligible_segments),
        "protected_segment_count": len(segments) - len(eligible_segments),
        "bundle_quota": quota,
        "bundle_count": len(speech_bundles),
        "speech_bundles": speech_bundles,
        "customer_state_suppressed": suppress_all,
        "input_segments": deepcopy(segments),
        "output_segments": output_segments,
        "tts_text": tts_text,
        "validation": validation,
        "provider_calls_made": False,
        "requires_api_key": False,
        "customer_audio_uploaded": False,
        "voice_cloning_used": False,
        "generated_audio_created": False,
        "runtime_boundary": {
            "position": "after spoken text normalization and before prosody/provider rendering",
            "changes_allowed": "bounded filler words and delivery metadata for eligible freeform TTS text only",
            "changes_forbidden": [
                "changing final_response",
                "changing campaign questions",
                "changing disclosures or compliance statements",
                "changing call-control lines",
                "adding claims, promises, or pressure",
            ],
        },
    }
