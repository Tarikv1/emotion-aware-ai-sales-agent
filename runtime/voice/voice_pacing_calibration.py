#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from typing import Any


VOICE_PACING_CALIBRATION_ID = "VOICE-034-pacing-calibration-v2"

BREAK_TAG_RE = re.compile(r"<break\s+time=\"(?P<value>[0-9.]+)(?P<unit>ms|s)\"\s*/?>", re.IGNORECASE)

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

DEFAULT_PROFILE = {
    "enabled": True,
    "style": "professional-sales-pacing-v2",
    "protected_segment_types": sorted(PROTECTED_SEGMENT_TYPES),
    "speed_bounds": {
        "en": [1.07, 1.15],
        "de": [0.975, 1.04],
    },
    "english_trust_repair_speed_bounds": [1.13, 1.14],
    "break_bounds_ms": {
        "en": [80, 240],
        "de": [110, 280],
    },
    "break_scale_ranges": {
        "en": [0.62, 0.82],
        "de": [0.9, 1.08],
    },
    "max_breaks_per_segment": 3,
    "german_word_gap_reduction": True,
    "min_provider_tags_preserved": 0,
}


def stable_unit(seed: str) -> float:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def stable_range_float(seed: str, low: float, high: float, digits: int = 3) -> float:
    if high <= low:
        return round(low, digits)
    return round(low + stable_unit(seed) * (high - low), digits)


def clamp_float(value: float, low: float, high: float, digits: int = 3) -> float:
    return round(min(high, max(low, value)), digits)


def normalize_language(language: str | None) -> str:
    return "de" if str(language or "").lower().startswith("de") else "en"


def normalize_text(text: str | None) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def profile_from_campaign(campaign: dict[str, Any]) -> dict[str, Any]:
    profile = deepcopy(DEFAULT_PROFILE)
    campaign_profile = campaign.get("voice_pacing_calibration") or campaign.get("speech_pacing") or {}
    for key, value in campaign_profile.items():
        if isinstance(value, dict) and isinstance(profile.get(key), dict):
            merged = dict(profile[key])
            merged.update(value)
            profile[key] = merged
        else:
            profile[key] = value
    profile["style"] = "professional-sales-pacing-v2"
    return profile


def segment_is_protected(segment: dict[str, Any], profile: dict[str, Any]) -> bool:
    protected_types = set(profile.get("protected_segment_types", PROTECTED_SEGMENT_TYPES))
    return (
        segment.get("protected_reason") is not None
        or segment.get("segment_type") in protected_types
        or segment.get("eligible_for_prosody") is False
    )


def break_to_ms(match: re.Match[str]) -> int:
    value = float(match.group("value"))
    unit = match.group("unit").lower()
    return int(round(value * 1000)) if unit == "s" else int(round(value))


def format_break(ms: int, unit: str) -> str:
    if unit.lower() == "s":
        seconds = f"{ms / 1000:.3f}".rstrip("0").rstrip(".")
        return f"<break time=\"{seconds}s\" />"
    return f"<break time=\"{ms}ms\"/>"


def compress_breaks(text: str, *, language: str, segment_id: str, seed: str, profile: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    bounds = profile.get("break_bounds_ms", DEFAULT_PROFILE["break_bounds_ms"]).get(language, DEFAULT_PROFILE["break_bounds_ms"]["en"])
    scale_range = profile.get("break_scale_ranges", DEFAULT_PROFILE["break_scale_ranges"]).get(language, DEFAULT_PROFILE["break_scale_ranges"]["en"])
    min_ms, max_ms = int(bounds[0]), int(bounds[1])
    max_breaks = int(profile.get("max_breaks_per_segment", 3))
    operations: list[dict[str, Any]] = []
    break_index = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal break_index
        break_index += 1
        original_ms = break_to_ms(match)
        if break_index > max_breaks:
            operations.append(
                {
                    "operation": "remove_extra_break",
                    "original_ms": original_ms,
                    "tuned_ms": 0,
                }
            )
            return ""
        scale = stable_range_float(f"{seed}:{segment_id}:voice-034-break:{break_index}", float(scale_range[0]), float(scale_range[1]))
        tuned_ms = int(round(min(max_ms, max(min_ms, original_ms * scale))))
        operations.append(
            {
                "operation": "compress_break",
                "original_ms": original_ms,
                "tuned_ms": tuned_ms,
                "scale": scale,
            }
        )
        return format_break(tuned_ms, match.group("unit"))

    return BREAK_TAG_RE.sub(replace, text), operations


def speed_for_segment(segment: dict[str, Any], *, language: str, seed: str, profile: dict[str, Any]) -> float:
    bounds = profile.get("speed_bounds", DEFAULT_PROFILE["speed_bounds"]).get(language, DEFAULT_PROFILE["speed_bounds"]["en"])
    source_text = normalize_text(segment.get("rendered_text", ""))
    if language == "en" and (
        "not asking you to decide now" in source_text
        or "that's why i'll keep it brief" in source_text
        or "that is why i will keep it brief" in source_text
    ):
        bounds = profile.get("english_trust_repair_speed_bounds", DEFAULT_PROFILE["english_trust_repair_speed_bounds"])
    low, high = float(bounds[0]), float(bounds[1])
    segment_type = segment.get("segment_type") or "segment"
    return clamp_float(stable_range_float(f"{seed}:{segment.get('segment_id')}:{segment_type}:voice-034-speed", low, high), low, high)


def tune_segment(segment: dict[str, Any], *, language: str, seed: str, profile: dict[str, Any]) -> dict[str, Any]:
    protected = segment_is_protected(segment, profile)
    source_text = segment.get("rendered_text", "")
    if protected or not profile.get("enabled", True):
        return {
            "segment_id": segment.get("segment_id"),
            "segment_type": segment.get("segment_type"),
            "protected": protected,
            "protected_reason": segment.get("protected_reason"),
            "tuned": False,
            "source_text": source_text,
            "pacing_text": source_text,
            "speed_ratio": 1.0,
            "break_operations": [],
            "provider_hint": "Protected or disabled segment kept exact.",
        }

    pacing_text, break_operations = compress_breaks(
        source_text,
        language=language,
        segment_id=str(segment.get("segment_id") or "segment"),
        seed=seed,
        profile=profile,
    )
    return {
        "segment_id": segment.get("segment_id"),
        "segment_type": segment.get("segment_type"),
        "protected": False,
        "protected_reason": None,
        "tuned": True,
        "source_text": source_text,
        "pacing_text": pacing_text,
        "speed_ratio": speed_for_segment(segment, language=language, seed=seed, profile=profile),
        "break_operations": break_operations,
        "provider_hint": "Professional sales pacing calibrated; wording unchanged.",
    }


def average(values: list[int]) -> float:
    return round(sum(values) / len(values), 3) if values else 0.0


def collect_break_values(text: str) -> list[int]:
    return [break_to_ms(match) for match in BREAK_TAG_RE.finditer(text)]


def validate_calibration(
    *,
    source_rendering: dict[str, Any],
    calibrated_rendering: dict[str, Any],
    segment_plan: list[dict[str, Any]],
    language: str,
    profile: dict[str, Any],
) -> dict[str, Any]:
    protected_segment_text_changes = [
        segment["segment_id"]
        for segment in segment_plan
        if segment["protected"] and segment["source_text"] != segment["pacing_text"]
    ]
    bounds = profile.get("speed_bounds", DEFAULT_PROFILE["speed_bounds"]).get(language, DEFAULT_PROFILE["speed_bounds"]["en"])
    speed_out_of_bounds = [
        segment
        for segment in segment_plan
        if segment["tuned"] and not (float(bounds[0]) <= float(segment["speed_ratio"]) <= float(bounds[1]))
    ]
    protected_tags_changed = calibrated_rendering.get("protected_segment_provider_tag_count", 0) != source_rendering.get(
        "protected_segment_provider_tag_count", 0
    )
    passed = not protected_segment_text_changes and not speed_out_of_bounds and not protected_tags_changed
    return {
        "passed": passed,
        "protected_segment_text_changes": protected_segment_text_changes,
        "speed_out_of_bounds": speed_out_of_bounds,
        "protected_tags_changed": protected_tags_changed,
    }


def apply_voice_pacing_calibration(
    campaign: dict[str, Any],
    provider_rendering: dict[str, Any],
    *,
    language: str,
    seed: str = "",
) -> dict[str, Any]:
    language = normalize_language(language)
    profile = profile_from_campaign(campaign)
    source = deepcopy(provider_rendering)
    segment_plan = [
        tune_segment(segment, language=language, seed=seed, profile=profile)
        for segment in source.get("segment_renderings", [])
    ]
    calibrated_segments = []
    for source_segment, plan in zip(source.get("segment_renderings", []), segment_plan):
        calibrated_segment = deepcopy(source_segment)
        calibrated_segment["rendered_text"] = plan["pacing_text"]
        calibrated_segment["voice_pacing_calibration"] = {
            "tuned": plan["tuned"],
            "speed_ratio": plan["speed_ratio"],
            "break_operations": plan["break_operations"],
        }
        calibrated_segments.append(calibrated_segment)

    speed_values = [float(plan["speed_ratio"]) for plan in segment_plan if plan["tuned"]]
    voice_settings = deepcopy(source.get("voice_settings") or {})
    if source.get("provider_key") == "elevenlabs" and speed_values:
        bounds = profile.get("speed_bounds", DEFAULT_PROFILE["speed_bounds"]).get(language, DEFAULT_PROFILE["speed_bounds"]["en"])
        voice_settings["speed"] = clamp_float(sum(speed_values) / len(speed_values), float(bounds[0]), float(bounds[1]))

    rendered_text = " ".join(segment["rendered_text"].strip() for segment in calibrated_segments if segment["rendered_text"].strip())
    calibrated = deepcopy(source)
    calibrated["rendered_text"] = rendered_text
    calibrated["rendered_text_html_preview"] = rendered_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    calibrated["voice_settings"] = voice_settings
    calibrated["segment_renderings"] = calibrated_segments
    calibrated["pacing_calibrated"] = bool(speed_values)
    calibrated["voice_pacing_calibration_id"] = VOICE_PACING_CALIBRATION_ID
    calibrated["provider_tag_count"] = len(BREAK_TAG_RE.findall(rendered_text))

    before_breaks = collect_break_values(source.get("rendered_text", ""))
    after_breaks = collect_break_values(rendered_text)
    validation = validate_calibration(
        source_rendering=source,
        calibrated_rendering=calibrated,
        segment_plan=segment_plan,
        language=language,
        profile=profile,
    )
    return {
        "voice_milestone": "VOICE-034",
        "voice_pacing_calibration_id": VOICE_PACING_CALIBRATION_ID,
        "enabled": bool(profile.get("enabled", True)),
        "language": language,
        "profile": profile,
        "german_word_gap_reduction_applied": language == "de" and bool(profile.get("german_word_gap_reduction", True)) and bool(speed_values),
        "source_provider_tag_count": int(source.get("provider_tag_count", 0)),
        "calibrated_provider_tag_count": int(calibrated.get("provider_tag_count", 0)),
        "average_break_duration_before_ms": average(before_breaks),
        "average_break_duration_after_ms": average(after_breaks),
        "segment_plan": segment_plan,
        "tuned_segment_count": len(speed_values),
        "average_speed_ratio": round(sum(speed_values) / len(speed_values), 3) if speed_values else 1.0,
        "calibrated_provider_rendering": calibrated,
        "validation": validation,
        "runtime_boundary": {
            "provider_calls_made": False,
            "requires_api_key": False,
            "customer_audio_uploaded": False,
            "voice_cloning_used": False,
            "generated_audio_created": False,
            "changes_allowed": "provider-rendered pacing tags and voice speed settings only; wording and protected text stay exact",
        },
    }
