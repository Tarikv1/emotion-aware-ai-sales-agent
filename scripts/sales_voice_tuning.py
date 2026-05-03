#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from typing import Any


SALES_VOICE_TUNING_ID = "VOICE-018-professional-sales-voice-tuning"

PROTECTED_TYPES = {
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

DEFAULT_SPEED_RANGES = {
    "freeform_objection_handling": [1.11, 1.16],
    "freeform_transition": [1.08, 1.13],
    "freeform_explanation": [1.1, 1.15],
    "freeform_empathy": [1.03, 1.08],
}

DEFAULT_EMOTION_INTENTS = {
    "freeform_objection_handling": "confident-low-pressure",
    "freeform_transition": "curious-efficient",
    "freeform_explanation": "confident-practical",
    "freeform_empathy": "warm-reassuring",
}

PITCH_INTENTS = {
    "confident-low-pressure": "steady-confident",
    "curious-efficient": "slight-rise",
    "confident-practical": "steady-confident",
    "warm-reassuring": "warm-soft",
    "neutral-clear": "steady-neutral",
}

BREAK_TAG_RE = re.compile(r"<break\s+time=\"(?P<value>[0-9.]+)(?P<unit>ms|s)\"\s*/?>", re.IGNORECASE)
SPEED_TAG_RE = re.compile(r"<speed\s+ratio=\"(?P<ratio>[0-9.]+)\"\s*/>", re.IGNORECASE)


def stable_unit(seed: str) -> float:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def stable_range_float(seed: str, low: float, high: float, digits: int = 3) -> float:
    if high <= low:
        return round(low, digits)
    return round(low + stable_unit(seed) * (high - low), digits)


def clamp_float(value: float, low: float, high: float, digits: int = 3) -> float:
    return round(min(high, max(low, value)), digits)


def segment_is_protected(segment: dict[str, Any]) -> bool:
    return bool(segment.get("protected_reason")) or segment.get("segment_type") in PROTECTED_TYPES


def active_case_for_tuning(case: dict[str, Any], profile: dict[str, Any]) -> bool:
    if not profile.get("tune_only_when_source_has_prosody_cues", True):
        return True
    return int(case.get("prosody_cue_count", 0)) > 0


def speed_for_segment(segment: dict[str, Any], case_id: str, profile: dict[str, Any]) -> float:
    speed_bounds = profile.get("speed_bounds", {})
    min_speed = float(speed_bounds.get("min", 1.0))
    max_speed = float(speed_bounds.get("max", 1.16))
    ranges = profile.get("segment_type_speed_ranges") or DEFAULT_SPEED_RANGES
    low, high = ranges.get(segment.get("segment_type"), [1.06, 1.12])
    return clamp_float(
        stable_range_float(f"{case_id}:{segment.get('segment_id')}:sales-speed", float(low), float(high)),
        min_speed,
        max_speed,
    )


def emotion_intent_for_segment(segment: dict[str, Any], profile: dict[str, Any]) -> str:
    intents = profile.get("emotion_intents_by_segment_type") or DEFAULT_EMOTION_INTENTS
    return intents.get(segment.get("segment_type"), "confident-practical")


def compress_break_tags(text: str, case_id: str, segment_id: str, profile: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    pause_bounds = profile.get("pause_bounds_ms", {})
    min_ms = int(pause_bounds.get("min", 90))
    max_ms = int(pause_bounds.get("max", 280))
    operations: list[dict[str, Any]] = []

    def replace(match: re.Match[str]) -> str:
        value = float(match.group("value"))
        unit = match.group("unit").lower()
        original_ms = int(round(value * 1000)) if unit == "s" else int(round(value))
        scale = stable_range_float(f"{case_id}:{segment_id}:pause-scale:{match.start()}", 0.68, 0.84)
        tuned_ms = int(round(min(max_ms, max(min_ms, original_ms * scale))))
        operations.append(
            {
                "operation": "compress_pause",
                "original_ms": original_ms,
                "tuned_ms": tuned_ms,
                "scale": scale,
            }
        )
        if unit == "s":
            seconds = f"{tuned_ms / 1000:.3f}".rstrip("0").rstrip(".")
            return f"<break time=\"{seconds}s\" />"
        return f"<break time=\"{tuned_ms}ms\"/>"

    return BREAK_TAG_RE.sub(replace, text), operations


def tune_cartesia_speed_tags(text: str, target_speed: float) -> tuple[str, list[dict[str, Any]]]:
    operations: list[dict[str, Any]] = []
    speed_tags_seen = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal speed_tags_seen
        speed_tags_seen += 1
        original = float(match.group("ratio"))
        if abs(original - 1.0) < 0.001:
            tuned = target_speed
            operation = "restore_outer_sales_speed"
        elif original < 1.0:
            tuned = clamp_float(max(1.0, target_speed - 0.08), 1.0, 1.16)
            operation = "retune_careful_phrase_speed"
        else:
            tuned = clamp_float(max(target_speed, original), 1.0, 1.16)
            operation = "retune_quick_phrase_speed"
        operations.append(
            {
                "operation": operation,
                "original_ratio": round(original, 3),
                "tuned_ratio": tuned,
            }
        )
        return f"<speed ratio=\"{tuned:.3f}\"/>"

    tuned_text = SPEED_TAG_RE.sub(replace, text)
    operations.append(
        {
            "operation": "wrap_segment_sales_speed",
            "tuned_ratio": target_speed,
            "nested_speed_tags_seen": speed_tags_seen,
        }
    )
    tuned_text = f"<speed ratio=\"{target_speed:.3f}\"/>{tuned_text}<speed ratio=\"1.000\"/>"
    return tuned_text, operations


def tune_segment_text(
    segment: dict[str, Any],
    provider_key: str,
    case_id: str,
    speed_ratio: float,
    profile: dict[str, Any],
) -> tuple[str, list[dict[str, Any]]]:
    text = segment["rendered_text"]
    tuned_text, pause_operations = compress_break_tags(text, case_id, segment["segment_id"], profile)
    operations = pause_operations
    if provider_key == "cartesia":
        tuned_text, speed_operations = tune_cartesia_speed_tags(tuned_text, speed_ratio)
        operations.extend(speed_operations)
    return tuned_text, operations


def build_segment_plan(
    segment: dict[str, Any],
    provider_key: str,
    case_id: str,
    case_active: bool,
    profile: dict[str, Any],
) -> dict[str, Any]:
    protected = segment_is_protected(segment)
    if protected or not case_active:
        emotion_intent = profile.get("protected_emotion_intent", "neutral-clear") if protected else "neutral-clear"
        return {
            "segment_id": segment["segment_id"],
            "segment_type": segment["segment_type"],
            "protected": protected,
            "protected_reason": segment.get("protected_reason"),
            "tuned": False,
            "source_text": segment["rendered_text"],
            "sales_tuned_text": segment["rendered_text"],
            "speed_ratio": 1.0,
            "emotion_intent": emotion_intent,
            "pitch_intent": PITCH_INTENTS[emotion_intent],
            "pause_compression_count": 0,
            "operations": [],
            "provider_hint": "Protected or cue-free segment kept exact.",
        }

    speed_ratio = speed_for_segment(segment, case_id, profile)
    emotion_intent = emotion_intent_for_segment(segment, profile)
    tuned_text, operations = tune_segment_text(segment, provider_key, case_id, speed_ratio, profile)
    return {
        "segment_id": segment["segment_id"],
        "segment_type": segment["segment_type"],
        "protected": False,
        "protected_reason": None,
        "tuned": True,
        "source_text": segment["rendered_text"],
        "sales_tuned_text": tuned_text,
        "speed_ratio": speed_ratio,
        "emotion_intent": emotion_intent,
        "pitch_intent": PITCH_INTENTS.get(emotion_intent, "steady-confident"),
        "pause_compression_count": sum(1 for item in operations if item["operation"] == "compress_pause"),
        "operations": operations,
        "provider_hint": "Professional-sales pacing metadata; live provider mapping still requires explicit TTS checkpoint.",
    }


def validate_variant(variant: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    speed_bounds = profile.get("speed_bounds", {})
    min_speed = float(speed_bounds.get("min", 1.0))
    max_speed = float(speed_bounds.get("max", 1.16))
    protected_segment_text_changes = []
    speed_out_of_bounds = []
    missing_emotion_intents = []

    for segment in variant["segment_delivery_plan"]:
        if segment["protected"] and segment["source_text"] != segment["sales_tuned_text"]:
            protected_segment_text_changes.append(segment["segment_id"])
        if segment["speed_ratio"] < min_speed or segment["speed_ratio"] > max_speed:
            speed_out_of_bounds.append(segment)
        if segment["tuned"] and not segment["emotion_intent"]:
            missing_emotion_intents.append(segment["segment_id"])

    return {
        "passed": not protected_segment_text_changes and not speed_out_of_bounds and not missing_emotion_intents,
        "protected_segment_text_changes": protected_segment_text_changes,
        "speed_out_of_bounds": speed_out_of_bounds,
        "missing_emotion_intents": missing_emotion_intents,
    }


def apply_sales_voice_tuning(case: dict[str, Any], provider_variant: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    case_active = active_case_for_tuning(case, profile)
    provider_key = provider_variant["provider_key"]
    segment_plan = [
        build_segment_plan(segment, provider_key, case["case_id"], case_active, profile)
        for segment in provider_variant["segment_renderings"]
    ]
    tuned_segments = [segment for segment in segment_plan if segment["tuned"]]
    tuned_text = " ".join(segment["sales_tuned_text"].strip() for segment in segment_plan if segment["sales_tuned_text"].strip())
    speed_values = [segment["speed_ratio"] for segment in tuned_segments]
    voice_settings = deepcopy(provider_variant.get("voice_settings") or {})
    if provider_key == "elevenlabs" and speed_values:
        voice_settings["speed"] = clamp_float(sum(speed_values) / len(speed_values), 1.0, 1.16)

    variant = {
        "sales_voice_tuning_id": SALES_VOICE_TUNING_ID,
        "provider_key": provider_key,
        "provider_name": provider_variant["provider_name"],
        "case_active_for_tuning": case_active,
        "source_rendered_text": provider_variant["rendered_text"],
        "sales_tuned_text": tuned_text,
        "voice_settings": voice_settings,
        "segment_delivery_plan": segment_plan,
        "tuned_segment_count": len(tuned_segments),
        "pause_compression_count": sum(segment["pause_compression_count"] for segment in segment_plan),
        "average_speed_ratio": round(sum(speed_values) / len(speed_values), 3) if speed_values else 1.0,
        "max_speed_ratio": max(speed_values) if speed_values else 1.0,
        "emotion_intents": sorted({segment["emotion_intent"] for segment in segment_plan if segment["tuned"]}),
        "pitch_intents": sorted({segment["pitch_intent"] for segment in segment_plan if segment["tuned"]}),
        "provider_calls_made": False,
        "requires_api_key": False,
        "customer_audio_uploaded": False,
        "voice_cloning_used": False,
        "generated_audio_created": False,
        "runtime_boundary": "offline sales-voice tuning preview only; live audio belongs to a later explicit provider checkpoint",
    }
    variant["validation"] = validate_variant(variant, profile)
    return variant
