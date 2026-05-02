#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from typing import Any


SPEECH_NATURALNESS_ID = "VOICE-012-segment-aware-naturalness"

PROTECTED_SEGMENT_TYPES = {
    "approved_opening",
    "campaign_qualification_question",
    "company_script",
    "required_disclosure",
    "compliance_statement",
    "legal_or_medical_boundary",
    "coverage_or_claim_boundary",
    "claim_boundary",
    "do_not_call",
    "hangup",
    "appointment_confirmation",
    "sensitive_escalation",
    "human_handoff_exact_script",
}

ELIGIBLE_SEGMENT_TYPES = {
    "freeform_empathy",
    "freeform_objection_handling",
    "freeform_transition",
    "freeform_explanation",
    "freeform_clarification",
    "freeform_bridge",
}

PROTECTED_SOURCES = {
    "campaign_config",
    "company_script",
    "client_handbook",
    "required_disclosure",
    "compliance",
}

DEFAULT_PROFILE = {
    "enabled": True,
    "style": "human-professional",
    "filler_frequency": "low",
    "max_fillers_per_response": 1,
    "allow_casual_fillers": True,
    "allow_hesitation_sounds": True,
    "pause_markers_allowed": True,
    "protected_segment_types": sorted(PROTECTED_SEGMENT_TYPES),
}

FILLERS_BY_LANGUAGE = {
    "en": {
        "hesitation": ["um", "uh", "hm"],
        "casual": ["you know", "like"],
    },
    "de": {
        "hesitation": ["ähm", "äh", "hm"],
        "casual": ["also"],
    },
}


def normalize_language(language: str | None) -> str:
    if not language:
        return "en"
    lowered = language.lower()
    if lowered.startswith("de"):
        return "de"
    return "en"


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).lower()


def stable_index(seed: str, length: int) -> int:
    if length <= 0:
        return 0
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % length


def speech_profile_from_campaign(campaign: dict[str, Any]) -> dict[str, Any]:
    profile = deepcopy(DEFAULT_PROFILE)
    profile.update(campaign.get("speech_naturalness", {}))
    try:
        profile["max_fillers_per_response"] = max(0, int(profile.get("max_fillers_per_response", 0)))
    except (TypeError, ValueError):
        profile["max_fillers_per_response"] = DEFAULT_PROFILE["max_fillers_per_response"]
    return profile


def campaign_protected_texts(campaign: dict[str, Any]) -> dict[str, set[str]]:
    return {
        "approved_opening": {normalize_text(campaign.get("approved_opening", ""))},
        "campaign_qualification_question": {
            normalize_text(question) for question in campaign.get("qualification_questions", [])
        },
        "required_disclosure": {normalize_text(disclosure) for disclosure in campaign.get("required_disclosures", [])},
    }


def protection_reason(segment: dict[str, Any], campaign: dict[str, Any], profile: dict[str, Any]) -> str | None:
    segment_type = segment.get("segment_type", "")
    source = segment.get("source", "")
    normalized_text = normalize_text(segment.get("text", ""))
    protected_types = set(profile.get("protected_segment_types") or PROTECTED_SEGMENT_TYPES)

    protected_texts = campaign_protected_texts(campaign)
    for text_type, values in protected_texts.items():
        if normalized_text and normalized_text in values:
            return f"matches_{text_type}"

    if segment_type in protected_types or segment_type in PROTECTED_SEGMENT_TYPES:
        return f"protected_segment_type:{segment_type}"

    if source in PROTECTED_SOURCES:
        return f"protected_source:{source}"

    if segment.get("allow_fillers") is False:
        return "manual_no_fillers"

    return None


def segment_is_eligible(segment: dict[str, Any], campaign: dict[str, Any], profile: dict[str, Any]) -> bool:
    if protection_reason(segment, campaign, profile) is not None:
        return False
    if segment.get("allow_fillers") is True:
        return True
    return segment.get("segment_type") in ELIGIBLE_SEGMENT_TYPES


def filler_pool(language: str, profile: dict[str, Any]) -> list[str]:
    language = normalize_language(language)
    inventory = FILLERS_BY_LANGUAGE[language]
    fillers: list[str] = []
    if profile.get("allow_hesitation_sounds", True):
        fillers.extend(inventory["hesitation"])
    if profile.get("allow_casual_fillers", True):
        fillers.extend(inventory["casual"])
    return fillers


def select_filler(language: str, profile: dict[str, Any], seed: str, inserted_count: int) -> str | None:
    language = normalize_language(language)
    pool = filler_pool(language, profile)
    if not pool:
        return None
    style = str(profile.get("style", "")).lower()
    if inserted_count > 0 and profile.get("allow_casual_fillers", True) and "casual" in style:
        casual_pool = FILLERS_BY_LANGUAGE[language]["casual"]
        if casual_pool:
            return casual_pool[stable_index(f"{seed}:casual:{inserted_count}", len(casual_pool))]
    return pool[stable_index(f"{seed}:filler:{inserted_count}", len(pool))]


def filler_quota(profile: dict[str, Any], eligible_segments: list[dict[str, Any]]) -> int:
    if not profile.get("enabled", True):
        return 0
    max_fillers = int(profile.get("max_fillers_per_response", 0))
    if max_fillers <= 0 or not eligible_segments:
        return 0

    total_chars = sum(len(segment.get("text", "")) for segment in eligible_segments)
    frequency = str(profile.get("filler_frequency", "low")).lower()
    if frequency in {"off", "none", "disabled"}:
        desired = 0
    elif frequency in {"very-low", "very_low", "rare"}:
        desired = 1 if total_chars >= 160 else 0
    elif frequency == "low":
        desired = 1 if total_chars >= 70 else 0
    elif frequency == "medium":
        desired = 2 if total_chars >= 180 else 1
    elif frequency == "high":
        desired = 3 if total_chars >= 260 else 2
    else:
        desired = 1 if total_chars >= 70 else 0

    return min(max_fillers, desired, len(eligible_segments))


def contextual_filler(filler: str, suffix: str, language: str) -> str:
    suffix_start = normalize_text(suffix)
    casual_complement_fillers = {"like", "you know", "also", "hm"}
    if filler in casual_complement_fillers and (
        suffix_start.startswith("that ") or suffix_start.startswith("dass ")
    ):
        return "um" if normalize_language(language) == "en" else "ähm"
    return filler


def insert_after_pattern(text: str, pattern: str, filler: str, language: str) -> tuple[str, str] | None:
    match = re.search(pattern, text, re.IGNORECASE)
    if match is None:
        return None
    prefix = text[: match.end()].rstrip()
    suffix = text[match.end() :].lstrip()
    if suffix.startswith(","):
        suffix = suffix[1:].lstrip()
    filler = contextual_filler(filler, suffix, language)
    return f"{prefix}, {filler}, {suffix}", filler


def insert_fallback(text: str, filler: str) -> str:
    words = text.split()
    if len(words) < 8:
        return text
    insert_at = min(max(5, len(words) // 3), 9)
    before = words[:insert_at]
    after = words[insert_at:]
    if before and not before[-1].endswith((",", ";", ":")):
        before[-1] = f"{before[-1]},"
    return " ".join(before + [f"{filler},"] + after)


def insert_mid_utterance_filler(text: str, filler: str, language: str) -> tuple[str, str | None]:
    if len(text.strip()) < 55:
        return text, None

    language = normalize_language(language)
    patterns = (
        [
            r"\bthe important thing is\b",
            r"\bwhat I can do is\b",
            r"\bthe safest next step is\b",
            r"\bI do not\b",
            r"\bI don't\b",
            r"\bwe can\b",
        ]
        if language == "en"
        else [
            r"\bWichtig ist\b",
            r"\bder sichere naechste Schritt ist\b",
            r"\bder sichere nächste Schritt ist\b",
            r"\bich moechte\b",
            r"\bich möchte\b",
            r"\bich will\b",
            r"\bwir koennen\b",
            r"\bwir können\b",
        ]
    )

    for pattern in patterns:
        inserted = insert_after_pattern(text, pattern, filler, language)
        if inserted is not None:
            return inserted
    fallback = insert_fallback(text, filler)
    return fallback, filler if fallback != text else None


def contains_language_mismatched_filler(text: str, language: str) -> bool:
    normalized = f" {normalize_text(text)} "
    if normalize_language(language) == "de":
        english_fillers = {" um ", " uh ", " you know ", " kind of "}
        return any(filler in normalized for filler in english_fillers)
    german_fillers = {" ähm ", " äh "}
    return any(filler in normalized for filler in german_fillers)


def validate_output_segments(
    input_segments: list[dict[str, Any]],
    output_segments: list[dict[str, Any]],
    campaign: dict[str, Any],
    profile: dict[str, Any],
    language: str,
) -> dict[str, Any]:
    protected_segment_changes = []
    filler_in_protected_segments = []
    language_mismatch_segments = []

    for index, (input_segment, output_segment) in enumerate(zip(input_segments, output_segments)):
        reason = protection_reason(input_segment, campaign, profile)
        output_text = output_segment["text_after"]
        if reason and input_segment.get("text", "") != output_text:
            protected_segment_changes.append(index)
        if reason and output_segment.get("filler_inserted"):
            filler_in_protected_segments.append(index)
        if output_segment.get("filler_inserted") and contains_language_mismatched_filler(output_text, language):
            language_mismatch_segments.append(index)

    passed = not protected_segment_changes and not filler_in_protected_segments and not language_mismatch_segments
    return {
        "validator": "VOICE-012 segment protection and language check",
        "passed": passed,
        "protected_segment_changes": protected_segment_changes,
        "filler_in_protected_segments": filler_in_protected_segments,
        "language_mismatch_segments": language_mismatch_segments,
        "notes": (
            "Speech naturalness preserved protected segments and language-specific fillers."
            if passed
            else "Speech naturalness validation found protected-segment or language mismatch issues."
        ),
    }


def apply_speech_naturalness(
    campaign: dict[str, Any],
    segments: list[dict[str, Any]],
    language: str | None = None,
    seed: str = "",
) -> dict[str, Any]:
    language = normalize_language(language or campaign.get("language"))
    profile = speech_profile_from_campaign(campaign)
    pool = filler_pool(language, profile)
    annotated_segments = []
    eligible_segments = []

    for index, segment in enumerate(segments):
        segment_copy = deepcopy(segment)
        reason = protection_reason(segment_copy, campaign, profile)
        eligible = reason is None and segment_is_eligible(segment_copy, campaign, profile)
        segment_copy["_index"] = index
        segment_copy["_protected_reason"] = reason
        segment_copy["_eligible_for_fillers"] = eligible
        annotated_segments.append(segment_copy)
        if eligible:
            eligible_segments.append(segment_copy)

    quota = filler_quota(profile, eligible_segments)
    inserted_count = 0
    output_segments = []
    fillers_inserted = []

    for segment in annotated_segments:
        text_before = segment.get("text", "")
        text_after = text_before
        filler_inserted = None

        if (
            inserted_count < quota
            and segment["_eligible_for_fillers"]
            and pool
            and len(text_before.strip()) >= 55
        ):
            filler = select_filler(language, profile, f"{seed}:{segment['_index']}:{text_before}", inserted_count)
            if filler is None:
                continue
            candidate, actual_filler = insert_mid_utterance_filler(text_before, filler, language)
            if candidate != text_before:
                text_after = candidate
                filler_inserted = actual_filler or filler
                inserted_count += 1
                fillers_inserted.append(
                    {
                        "segment_index": segment["_index"],
                        "segment_id": segment.get("segment_id"),
                        "filler": filler_inserted,
                        "language": language,
                        "position": "mid-utterance",
                    }
                )

        output_segments.append(
            {
                "segment_index": segment["_index"],
                "segment_id": segment.get("segment_id"),
                "segment_type": segment.get("segment_type"),
                "source": segment.get("source"),
                "eligible_for_fillers": segment["_eligible_for_fillers"],
                "protected_reason": segment["_protected_reason"],
                "text_before": text_before,
                "text_after": text_after,
                "filler_inserted": filler_inserted,
            }
        )

    validation = validate_output_segments(segments, output_segments, campaign, profile, language)
    tts_text = " ".join(segment["text_after"].strip() for segment in output_segments if segment["text_after"].strip())
    return {
        "speech_naturalness_id": SPEECH_NATURALNESS_ID,
        "language": language,
        "profile": profile,
        "segment_count": len(segments),
        "eligible_segment_count": len(eligible_segments),
        "protected_segment_count": len(segments) - len(eligible_segments),
        "filler_pool": pool,
        "filler_quota": quota,
        "filler_count": len(fillers_inserted),
        "fillers_inserted": fillers_inserted,
        "input_segments": deepcopy(segments),
        "output_segments": output_segments,
        "tts_text": tts_text,
        "validation": validation,
        "runtime_boundary": {
            "provider_calls_made": False,
            "requires_api_key": False,
            "customer_audio_uploaded": False,
            "changes_allowed": "speech rhythm only; protected campaign, compliance, call-control, and safety text stay unchanged",
        },
    }
