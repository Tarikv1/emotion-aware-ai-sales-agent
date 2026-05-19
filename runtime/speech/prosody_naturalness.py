#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from typing import Any

from runtime.speech.speech_naturalness import (
    ELIGIBLE_SEGMENT_TYPES,
    PROTECTED_SEGMENT_TYPES,
    PROTECTED_SOURCES,
    normalize_language,
    normalize_text,
    protection_reason,
)


PROSODY_NATURALNESS_ID = "VOICE-015-segment-aware-prosody"

ALLOWED_CUE_TYPES = {"pause", "rate", "emphasis", "pitch", "stretch"}

DEFAULT_PROFILE = {
    "enabled": True,
    "style": "professional-human",
    "pause_variation_enabled": True,
    "rate_variation_enabled": True,
    "emphasis_enabled": True,
    "pitch_variation_enabled": True,
    "stretch_enabled": True,
    "max_cues_per_response": 4,
    "max_stretches_per_response": 1,
    "protected_segment_types": sorted(PROTECTED_SEGMENT_TYPES),
    "pause_ms_ranges": {
        "clause": [140, 260],
        "thinking": [180, 320],
        "transition": [220, 380],
    },
    "rate_ranges": {
        "quick": [1.03, 1.08],
        "careful": [0.9, 0.96],
    },
}

DEFAULT_EMPHASIS_TARGETS = {
    "en": ["important", "practical", "realistic", "safe", "verified", "specialist"],
    "de": ["wichtig", "praktisch", "realistisch", "sicher", "unverbindlich", "Fachberater"],
}

DEFAULT_CAREFUL_RATE_TARGETS = {
    "en": [
        "do not promise",
        "cannot verify",
        "keep this realistic",
        "before we schedule anything",
        "not confirmed",
    ],
    "de": [
        "nichts verspreche",
        "unverbindlich",
        "sauber pruefen",
        "bevor wir etwas vormerken",
        "nicht bestaetigt",
    ],
}

DEFAULT_STRETCH_TARGETS = {
    "en": ["so", "well"],
    "de": ["also", "hm"],
}


def stable_unit(seed: str) -> float:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def stable_range_int(seed: str, low: int, high: int) -> int:
    if high <= low:
        return low
    return low + round(stable_unit(seed) * (high - low))


def stable_range_float(seed: str, low: float, high: float, digits: int = 3) -> float:
    if high <= low:
        return round(low, digits)
    return round(low + stable_unit(seed) * (high - low), digits)


def prosody_profile_from_campaign(campaign: dict[str, Any]) -> dict[str, Any]:
    profile = deepcopy(DEFAULT_PROFILE)
    profile.update(campaign.get("speech_prosody", {}))

    # Product default: professional-human only. Campaigns can tune intensity, not turn the agent into a casual persona.
    profile["style"] = "professional-human"

    try:
        profile["max_cues_per_response"] = max(0, int(profile.get("max_cues_per_response", 0)))
    except (TypeError, ValueError):
        profile["max_cues_per_response"] = DEFAULT_PROFILE["max_cues_per_response"]

    try:
        profile["max_stretches_per_response"] = max(0, int(profile.get("max_stretches_per_response", 0)))
    except (TypeError, ValueError):
        profile["max_stretches_per_response"] = DEFAULT_PROFILE["max_stretches_per_response"]

    return profile


def segment_is_eligible(segment: dict[str, Any], campaign: dict[str, Any], profile: dict[str, Any]) -> bool:
    if protection_reason(segment, campaign, profile) is not None:
        return False
    if segment.get("allow_prosody") is True:
        return True
    return segment.get("segment_type") in ELIGIBLE_SEGMENT_TYPES


def find_target(text: str, candidates: list[str]) -> str | None:
    normalized_text = normalize_text(text)
    for candidate in candidates:
        if normalize_text(candidate) in normalized_text:
            match = re.search(re.escape(candidate), text, re.IGNORECASE)
            if match:
                return text[match.start() : match.end()]
    return None


def target_regex(target: str) -> re.Pattern[str] | None:
    if not target:
        return None
    escaped = re.escape(target)
    prefix = r"(?<![A-Za-z0-9])" if target[0].isalnum() else ""
    suffix = r"(?![A-Za-z0-9])" if target[-1].isalnum() else ""
    return re.compile(f"{prefix}{escaped}{suffix}", re.IGNORECASE)


def safe_explicit_pause_target(text: str, target: str) -> str | None:
    pattern = target_regex(target)
    if pattern is None:
        return None
    for match in pattern.finditer(text):
        suffix = text[match.end() :]
        if not suffix.strip():
            return text[match.start() : match.end()]
        punctuation = re.match(r"\s*([,.;:!?])", suffix)
        if punctuation:
            return text[match.start() : match.end() + punctuation.end()]
    return None


def first_phrase(text: str, max_words: int = 5) -> str:
    stripped = text.strip()
    if not stripped:
        return ""
    sentence = re.split(r"(?<=[.!?])\s+", stripped, maxsplit=1)[0]
    words = sentence.split()
    return " ".join(words[:max_words])


def replace_first_case_insensitive(text: str, target: str, replacement: str) -> str:
    if not target:
        return text
    return re.sub(re.escape(target), replacement, text, count=1, flags=re.IGNORECASE)


def add_emphasis_debug(text: str, target: str) -> str:
    return replace_first_case_insensitive(text, target, f"**{target}**")


def add_stretch_debug(text: str, target: str, variant: str) -> str:
    return replace_first_case_insensitive(text, target, variant)


def pause_after_target(text: str, segment: dict[str, Any]) -> str | None:
    explicit = segment.get("pause_after")
    if explicit:
        safe_target = safe_explicit_pause_target(text, str(explicit))
        if safe_target:
            return safe_target

    sentence_match = re.search(r"^(.{12,90}?[.!?])\s+", text)
    if sentence_match:
        return sentence_match.group(1)

    comma_match = re.search(r"^(.{12,90}?,)\s+", text)
    if comma_match:
        return comma_match.group(1)

    return None


def pause_cue(
    segment: dict[str, Any],
    text: str,
    seed: str,
    language: str,
    index: int,
    profile: dict[str, Any],
) -> dict[str, Any] | None:
    if not profile.get("pause_variation_enabled", True):
        return None
    after = pause_after_target(text, segment)
    if not after:
        return None
    mode = segment.get("pause_mode") or ("thinking" if segment.get("segment_type") == "freeform_objection_handling" else "transition")
    low, high = profile.get("pause_ms_ranges", DEFAULT_PROFILE["pause_ms_ranges"]).get(
        mode,
        DEFAULT_PROFILE["pause_ms_ranges"]["clause"],
    )
    return {
        "type": "pause",
        "segment_index": index,
        "segment_id": segment.get("segment_id"),
        "segment_type": segment.get("segment_type"),
        "after": after,
        "mode": mode,
        "duration_ms": stable_range_int(f"{seed}:pause:{index}:{after}:{language}", int(low), int(high)),
        "provider_hint": "Render as a bounded pause or break; do not add visible words.",
    }


def rate_cue(
    segment: dict[str, Any],
    text: str,
    seed: str,
    language: str,
    index: int,
    profile: dict[str, Any],
) -> dict[str, Any] | None:
    if not profile.get("rate_variation_enabled", True):
        return None
    language = normalize_language(language)
    target = segment.get("rate_target") or find_target(text, DEFAULT_CAREFUL_RATE_TARGETS[language])
    if not target:
        return None
    mode = segment.get("rate_mode") or "careful"
    low, high = profile.get("rate_ranges", DEFAULT_PROFILE["rate_ranges"]).get(
        mode,
        DEFAULT_PROFILE["rate_ranges"]["careful"],
    )
    return {
        "type": "rate",
        "segment_index": index,
        "segment_id": segment.get("segment_id"),
        "segment_type": segment.get("segment_type"),
        "target": target,
        "mode": mode,
        "ratio": stable_range_float(f"{seed}:rate:{index}:{target}:{language}", float(low), float(high)),
        "provider_hint": "Render with a small speed change only; keep wording unchanged.",
    }


def emphasis_cue(
    segment: dict[str, Any],
    text: str,
    seed: str,
    language: str,
    index: int,
    profile: dict[str, Any],
) -> dict[str, Any] | None:
    if not profile.get("emphasis_enabled", True):
        return None
    language = normalize_language(language)
    candidates = segment.get("emphasis_targets") or DEFAULT_EMPHASIS_TARGETS[language]
    target = find_target(text, list(candidates))
    if not target:
        return None
    return {
        "type": "emphasis",
        "segment_index": index,
        "segment_id": segment.get("segment_id"),
        "segment_type": segment.get("segment_type"),
        "target": target,
        "strength": segment.get("emphasis_strength") or "medium",
        "provider_hint": "Debug view may use Markdown bold; provider adapters must not blindly send Markdown unless supported.",
    }


def pitch_cue(
    segment: dict[str, Any],
    text: str,
    seed: str,
    language: str,
    index: int,
    profile: dict[str, Any],
) -> dict[str, Any] | None:
    if not profile.get("pitch_variation_enabled", True):
        return None
    direction = segment.get("pitch_direction")
    if not direction:
        if segment.get("segment_type") == "freeform_empathy":
            direction = "warm-soft"
        elif "?" in text:
            direction = "slight-rise"
        else:
            direction = "steady-low"
    if direction not in {"warm-soft", "slight-rise", "steady-low"}:
        direction = "warm-soft"
    target = segment.get("pitch_target") or first_phrase(text)
    semitone_by_direction = {
        "warm-soft": -0.25,
        "slight-rise": 0.45,
        "steady-low": -0.45,
    }
    jitter = stable_range_float(f"{seed}:pitch:{index}:{target}:{language}", -0.1, 0.1)
    return {
        "type": "pitch",
        "segment_index": index,
        "segment_id": segment.get("segment_id"),
        "segment_type": segment.get("segment_type"),
        "target": target,
        "direction": direction,
        "relative_pitch_semitones": round(semitone_by_direction[direction] + jitter, 3),
        "provider_hint": "Render as a subtle contour change, not theatrical acting.",
    }


def stretch_cue(
    segment: dict[str, Any],
    text: str,
    seed: str,
    language: str,
    index: int,
    profile: dict[str, Any],
) -> dict[str, Any] | None:
    if not profile.get("stretch_enabled", True):
        return None
    language = normalize_language(language)
    if segment.get("allow_stretch") is not True and not segment.get("stretch_targets"):
        return None
    candidates = segment.get("stretch_targets") or DEFAULT_STRETCH_TARGETS[language]
    target = find_target(text, list(candidates))
    if not target:
        return None
    hold_ms = stable_range_int(f"{seed}:stretch:{index}:{target}:{language}", 120, 280)
    variant = f"{target}..."
    return {
        "type": "stretch",
        "segment_index": index,
        "segment_id": segment.get("segment_id"),
        "segment_type": segment.get("segment_type"),
        "target": target,
        "variant": variant,
        "hold_ms": hold_ms,
        "provider_hint": "Render as a small thinking hold; do not over-stretch letters.",
    }


def propose_segment_cues(
    segment: dict[str, Any],
    text: str,
    seed: str,
    language: str,
    index: int,
    profile: dict[str, Any],
) -> list[dict[str, Any]]:
    proposed = [
        pitch_cue(segment, text, seed, language, index, profile),
        pause_cue(segment, text, seed, language, index, profile),
        rate_cue(segment, text, seed, language, index, profile),
        emphasis_cue(segment, text, seed, language, index, profile),
        stretch_cue(segment, text, seed, language, index, profile),
    ]
    return [cue for cue in proposed if cue is not None]


def apply_debug_cues(text: str, cues: list[dict[str, Any]]) -> str:
    debug_text = text
    for cue in cues:
        if cue["type"] == "emphasis":
            debug_text = add_emphasis_debug(debug_text, cue["target"])
        elif cue["type"] == "stretch":
            debug_text = add_stretch_debug(debug_text, cue["target"], cue["variant"])
    return debug_text


def cue_counts(cues: list[dict[str, Any]]) -> dict[str, int]:
    counts = {cue_type: 0 for cue_type in sorted(ALLOWED_CUE_TYPES)}
    for cue in cues:
        counts[cue["type"]] = counts.get(cue["type"], 0) + 1
    return counts


def validate_output_segments(
    input_segments: list[dict[str, Any]],
    output_segments: list[dict[str, Any]],
    cues: list[dict[str, Any]],
    campaign: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:
    protected_segment_changes = []
    cue_in_protected_segments = []
    unsafe_pause_cues = []
    unsafe_rate_cues = []
    unsafe_pitch_cues = []
    markdown_in_tts_text = []

    protected_ids = {
        segment.get("segment_id")
        for segment in input_segments
        if protection_reason(segment, campaign, profile) is not None
    }

    for index, (input_segment, output_segment) in enumerate(zip(input_segments, output_segments)):
        reason = protection_reason(input_segment, campaign, profile)
        if reason and input_segment.get("text", "") != output_segment["tts_text"]:
            protected_segment_changes.append(index)
        if reason and output_segment["cue_count"] > 0:
            cue_in_protected_segments.append(index)
        if "**" in output_segment["tts_text"]:
            markdown_in_tts_text.append(index)

    for cue in cues:
        if cue.get("segment_id") in protected_ids or cue.get("segment_type") in PROTECTED_SEGMENT_TYPES:
            cue_in_protected_segments.append(cue.get("segment_index"))
        if cue["type"] == "pause" and not 120 <= cue["duration_ms"] <= 420:
            unsafe_pause_cues.append(cue)
        if cue["type"] == "rate" and not 0.9 <= cue["ratio"] <= 1.08:
            unsafe_rate_cues.append(cue)
        if cue["type"] == "pitch" and cue["direction"] not in {"warm-soft", "slight-rise", "steady-low"}:
            unsafe_pitch_cues.append(cue)

    passed = not any(
        [
            protected_segment_changes,
            cue_in_protected_segments,
            unsafe_pause_cues,
            unsafe_rate_cues,
            unsafe_pitch_cues,
            markdown_in_tts_text,
        ]
    )
    return {
        "validator": "VOICE-015 segment protection and bounded prosody check",
        "passed": passed,
        "protected_segment_changes": protected_segment_changes,
        "cue_in_protected_segments": cue_in_protected_segments,
        "unsafe_pause_cues": unsafe_pause_cues,
        "unsafe_rate_cues": unsafe_rate_cues,
        "unsafe_pitch_cues": unsafe_pitch_cues,
        "markdown_in_tts_text": markdown_in_tts_text,
        "notes": (
            "Prosody cues stayed bounded and outside protected segments."
            if passed
            else "Prosody validation found protected-segment or cue-boundary issues."
        ),
    }


def apply_prosody_naturalness(
    campaign: dict[str, Any],
    segments: list[dict[str, Any]],
    language: str | None = None,
    seed: str = "",
) -> dict[str, Any]:
    language = normalize_language(language or campaign.get("language"))
    profile = prosody_profile_from_campaign(campaign)
    max_cues = int(profile.get("max_cues_per_response", 0)) if profile.get("enabled", True) else 0
    max_stretches = int(profile.get("max_stretches_per_response", 0))

    output_segments = []
    prosody_plan = []
    eligible_segment_count = 0
    protected_segment_count = 0
    stretch_count = 0

    for index, segment in enumerate(deepcopy(segments)):
        text = segment.get("text", "")
        reason = protection_reason(segment, campaign, profile)
        eligible = reason is None and segment_is_eligible(segment, campaign, profile)
        if eligible:
            eligible_segment_count += 1
        else:
            protected_segment_count += 1

        segment_cues: list[dict[str, Any]] = []
        if eligible and len(prosody_plan) < max_cues:
            for cue in propose_segment_cues(segment, text, seed, language, index, profile):
                if len(prosody_plan) >= max_cues:
                    break
                if cue["type"] == "stretch":
                    if stretch_count >= max_stretches:
                        continue
                    stretch_count += 1
                cue["cue_id"] = f"cue-{len(prosody_plan) + 1:02d}"
                segment_cues.append(cue)
                prosody_plan.append(cue)

        output_segments.append(
            {
                "segment_index": index,
                "segment_id": segment.get("segment_id"),
                "segment_type": segment.get("segment_type"),
                "source": segment.get("source"),
                "eligible_for_prosody": eligible,
                "protected_reason": reason,
                "text_before": text,
                "tts_text": text,
                "debug_text": apply_debug_cues(text, segment_cues),
                "cue_count": len(segment_cues),
                "cues": segment_cues,
            }
        )

    validation = validate_output_segments(segments, output_segments, prosody_plan, campaign, profile)
    tts_text = " ".join(segment["tts_text"].strip() for segment in output_segments if segment["tts_text"].strip())
    debug_text = " ".join(segment["debug_text"].strip() for segment in output_segments if segment["debug_text"].strip())

    return {
        "prosody_naturalness_id": PROSODY_NATURALNESS_ID,
        "language": language,
        "profile": profile,
        "randomization": {
            "seeded": True,
            "seed": seed,
            "deterministic_for_same_input": True,
            "dimensions": ["pause duration", "rate ratio", "pitch contour delta", "stretch hold"],
        },
        "segment_count": len(segments),
        "eligible_segment_count": eligible_segment_count,
        "protected_segment_count": protected_segment_count,
        "cue_count": len(prosody_plan),
        "cue_counts": cue_counts(prosody_plan),
        "protected_segment_cue_count": sum(
            1 for cue in prosody_plan if cue.get("segment_type") in PROTECTED_SEGMENT_TYPES or cue.get("source") in PROTECTED_SOURCES
        ),
        "input_segments": deepcopy(segments),
        "output_segments": output_segments,
        "prosody_plan": prosody_plan,
        "tts_text": tts_text,
        "debug_text": debug_text,
        "provider_rendering_boundary": {
            "clean_tts_text": "Plain text remains available for every provider.",
            "debug_text": "Debug text may show emphasis or stretch cues for human review.",
            "cartesia": "Future adapter may map pause/rate/pitch cues to supported SSML-style controls.",
            "elevenlabs": "Future adapter may map cues to punctuation shaping, model tags, or voice settings only after provider tests.",
            "fallback": "If a provider cannot represent a cue safely, drop the cue and speak clean text.",
        },
        "validation": validation,
        "runtime_boundary": {
            "provider_calls_made": False,
            "requires_api_key": False,
            "customer_audio_uploaded": False,
            "voice_cloning_used": False,
            "changes_allowed": "provider-neutral delivery cues only; protected campaign, compliance, call-control, and safety text stay exact",
        },
    }
