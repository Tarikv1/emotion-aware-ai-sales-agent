#!/usr/bin/env python3
from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from speech_naturalness import (
    ELIGIBLE_SEGMENT_TYPES,
    PROTECTED_SEGMENT_TYPES,
    PROTECTED_SOURCES,
    normalize_language,
    protection_reason,
)


SPOKEN_TEXT_NORMALIZATION_ID = "VOICE-022-spoken-text-normalization"

DEFAULT_PROFILE = {
    "enabled": True,
    "style": "professional-spoken",
    "english_contractions": True,
    "german_spoken_forms": True,
    "max_rewrites_per_response": 4,
    "protected_segment_types": sorted(PROTECTED_SEGMENT_TYPES),
}

ENGLISH_RULES = [
    {"rule_id": "en-i-will", "pattern": r"\bI will\b", "replacement": "i'll"},
    {"rule_id": "en-i-am", "pattern": r"\bI am\b", "replacement": "i'm"},
    {"rule_id": "en-i-have", "pattern": r"\bI have\b", "replacement": "i've"},
    {"rule_id": "en-i-would", "pattern": r"\bI would\b", "replacement": "i'd"},
    {"rule_id": "en-you-are", "pattern": r"\byou are\b", "replacement": "you're"},
    {"rule_id": "en-that-is", "pattern": r"\bthat is\b", "replacement": "that's"},
    {"rule_id": "en-it-is", "pattern": r"\bit is\b", "replacement": "it's"},
    {"rule_id": "en-there-is", "pattern": r"\bthere is\b", "replacement": "there's"},
    {"rule_id": "en-we-are", "pattern": r"\bwe are\b", "replacement": "we're"},
    {"rule_id": "en-we-will", "pattern": r"\bwe will\b", "replacement": "we'll"},
    {"rule_id": "en-let-us", "pattern": r"\blet us\b", "replacement": "let's"},
    {"rule_id": "en-do-not", "pattern": r"\bdo not\b", "replacement": "don't"},
    {"rule_id": "en-does-not", "pattern": r"\bdoes not\b", "replacement": "doesn't"},
    {"rule_id": "en-cannot", "pattern": r"\bcannot\b", "replacement": "can't"},
    {"rule_id": "en-could-not", "pattern": r"\bcould not\b", "replacement": "couldn't"},
    {"rule_id": "en-should-not", "pattern": r"\bshould not\b", "replacement": "shouldn't"},
    {"rule_id": "en-would-not", "pattern": r"\bwould not\b", "replacement": "wouldn't"},
]

GERMAN_RULES = [
    {"rule_id": "de-ich-habe", "pattern": r"\bich habe\b", "replacement": "ich hab"},
    {"rule_id": "de-wenn-es", "pattern": r"\bwenn es\b", "replacement": "wenn's"},
    {"rule_id": "de-gibt-es", "pattern": r"\bgibt es\b", "replacement": "gibt's"},
    {"rule_id": "de-geht-es", "pattern": r"\bgeht es\b", "replacement": "geht's"},
    {"rule_id": "de-macht-es", "pattern": r"\bmacht es\b", "replacement": "macht's"},
]


def spoken_profile_from_campaign(campaign: dict[str, Any]) -> dict[str, Any]:
    profile = deepcopy(DEFAULT_PROFILE)
    profile.update(campaign.get("spoken_text_normalization", {}))
    try:
        profile["max_rewrites_per_response"] = max(0, int(profile.get("max_rewrites_per_response", 0)))
    except (TypeError, ValueError):
        profile["max_rewrites_per_response"] = DEFAULT_PROFILE["max_rewrites_per_response"]
    return profile


def segment_is_eligible(segment: dict[str, Any], campaign: dict[str, Any], profile: dict[str, Any]) -> bool:
    if protection_reason(segment, campaign, profile) is not None:
        return False
    if segment.get("allow_spoken_text_normalization") is False:
        return False
    if segment.get("allow_spoken_text_normalization") is True:
        return True
    if segment.get("allow_prosody") is True or segment.get("allow_fillers") is True:
        return True
    return segment.get("segment_type") in ELIGIBLE_SEGMENT_TYPES


def rules_for_language(language: str, profile: dict[str, Any]) -> list[dict[str, str]]:
    language = normalize_language(language)
    if language == "de":
        return GERMAN_RULES if profile.get("german_spoken_forms", True) else []
    return ENGLISH_RULES if profile.get("english_contractions", True) else []


def preserve_initial_case(replacement: str, source: str) -> str:
    if not source:
        return replacement
    if source.isupper():
        return replacement.upper()
    if source[0].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def apply_rule_once(text: str, rule: dict[str, str]) -> tuple[str, dict[str, str] | None]:
    pattern = re.compile(rule["pattern"], re.IGNORECASE)
    match = pattern.search(text)
    if match is None:
        return text, None
    before = match.group(0)
    after = preserve_initial_case(rule["replacement"], before)
    changed = text[: match.start()] + after + text[match.end() :]
    return changed, {
        "rule_id": rule["rule_id"],
        "before": before,
        "after": after,
    }


def normalize_segment_text(
    text: str,
    rules: list[dict[str, str]],
    remaining_quota: int,
) -> tuple[str, list[dict[str, str]]]:
    text_after = text
    normalizations = []
    if remaining_quota <= 0:
        return text_after, normalizations

    for rule in rules:
        if len(normalizations) >= remaining_quota:
            break
        candidate, operation = apply_rule_once(text_after, rule)
        if operation is None:
            continue
        text_after = candidate
        normalizations.append(operation)

    return text_after, normalizations


def validate_output_segments(
    input_segments: list[dict[str, Any]],
    output_segments: list[dict[str, Any]],
    campaign: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:
    protected_segment_changes = []
    normalization_in_protected_segments = []
    source_protection_changes = []

    for index, (input_segment, output_segment) in enumerate(zip(input_segments, output_segments)):
        reason = protection_reason(input_segment, campaign, profile)
        source = input_segment.get("source")
        protected_source = source in PROTECTED_SOURCES
        if reason and input_segment.get("text", "") != output_segment["text_after"]:
            protected_segment_changes.append(index)
        if reason and output_segment.get("normalizations"):
            normalization_in_protected_segments.append(index)
        if protected_source and input_segment.get("text", "") != output_segment["text_after"]:
            source_protection_changes.append(index)

    passed = not protected_segment_changes and not normalization_in_protected_segments and not source_protection_changes
    return {
        "validator": "VOICE-022 segment protection and spoken-normalization check",
        "passed": passed,
        "protected_segment_changes": protected_segment_changes,
        "normalization_in_protected_segments": normalization_in_protected_segments,
        "source_protection_changes": source_protection_changes,
        "notes": (
            "Spoken-text normalization preserved protected segments and sources."
            if passed
            else "Spoken-text normalization changed protected text or source-owned text."
        ),
    }


def apply_spoken_text_normalization(
    campaign: dict[str, Any],
    segments: list[dict[str, Any]],
    language: str | None = None,
    seed: str = "",
) -> dict[str, Any]:
    del seed
    language = normalize_language(language or campaign.get("language"))
    profile = spoken_profile_from_campaign(campaign)
    rules = rules_for_language(language, profile)
    max_rewrites = int(profile.get("max_rewrites_per_response", 0)) if profile.get("enabled", True) else 0

    output_segments = []
    operations = []
    eligible_segment_count = 0
    protected_segment_count = 0

    for index, segment in enumerate(deepcopy(segments)):
        text_before = segment.get("text", "")
        reason = protection_reason(segment, campaign, profile)
        eligible = reason is None and segment_is_eligible(segment, campaign, profile)
        if eligible:
            eligible_segment_count += 1
        else:
            protected_segment_count += 1

        remaining_quota = max(0, max_rewrites - len(operations))
        text_after = text_before
        segment_operations: list[dict[str, Any]] = []
        if eligible and rules and remaining_quota > 0:
            text_after, segment_operations = normalize_segment_text(text_before, rules, remaining_quota)
            for operation in segment_operations:
                operations.append(
                    {
                        **operation,
                        "language": language,
                        "segment_index": index,
                        "segment_id": segment.get("segment_id"),
                        "segment_type": segment.get("segment_type"),
                    }
                )

        output_segments.append(
            {
                "segment_index": index,
                "segment_id": segment.get("segment_id"),
                "segment_type": segment.get("segment_type"),
                "source": segment.get("source"),
                "eligible_for_spoken_normalization": eligible,
                "protected_reason": reason,
                "text_before": text_before,
                "text_after": text_after,
                "normalizations": segment_operations,
            }
        )

    validation = validate_output_segments(segments, output_segments, campaign, profile)
    tts_text = " ".join(segment["text_after"].strip() for segment in output_segments if segment["text_after"].strip())
    return {
        "spoken_text_normalization_id": SPOKEN_TEXT_NORMALIZATION_ID,
        "language": language,
        "profile": profile,
        "rule_count": len(rules),
        "segment_count": len(segments),
        "eligible_segment_count": eligible_segment_count,
        "protected_segment_count": protected_segment_count,
        "normalization_count": len(operations),
        "normalizations": operations,
        "input_segments": deepcopy(segments),
        "output_segments": output_segments,
        "tts_text": tts_text,
        "validation": validation,
        "runtime_boundary": {
            "provider_calls_made": False,
            "requires_api_key": False,
            "customer_audio_uploaded": False,
            "voice_cloning_used": False,
            "changes_allowed": "safe spoken phrasing for eligible freeform TTS text only",
            "changes_forbidden": [
                "changing final_response",
                "changing protected campaign questions",
                "changing disclosures or compliance statements",
                "changing call-control lines",
                "adding claims or promises",
            ],
        },
    }
