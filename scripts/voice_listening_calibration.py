#!/usr/bin/env python3
from __future__ import annotations

import html
import re
from copy import deepcopy
from typing import Any


VOICE_LISTENING_CALIBRATION_ID = "VOICE-036-listening-feedback-calibration"

PROVIDER_TAG_RE = re.compile(r"<[^>]+>")
GERMAN_COMPRESSED_OPENING_RE = re.compile(r"(Das verstehe ich,)\s+also\s+geht's", re.IGNORECASE)

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
    "style": "listening-feedback-calibration-v1",
    "protected_segment_types": sorted(PROTECTED_SEGMENT_TYPES),
    "german_connected_break_seconds": 0.08,
    "german_relaxed_speed": 0.995,
    "german_relaxed_speed_bounds": [0.97, 1.02],
    "emphasis_guard_enabled": True,
    "allowed_emphasis_targets": {
        "en": ["specialist", "verified", "non-binding", "next step", "budget", "decision"],
        "de": ["fachberater", "geprueft", "unverbindlich", "naechster schritt", "budget", "entscheidung"],
    },
    "blocked_single_word_emphasis": {
        "en": ["important", "practical", "realistic", "safe"],
        "de": ["wichtig", "praktisch", "realistisch", "sicher"],
    },
}


def normalize_language(language: str | None) -> str:
    return "de" if str(language or "").lower().startswith("de") else "en"


def normalize_text(text: str | None) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def profile_from_campaign(campaign: dict[str, Any]) -> dict[str, Any]:
    profile = deepcopy(DEFAULT_PROFILE)
    campaign_profile = campaign.get("voice_listening_calibration") or campaign.get("listening_calibration") or {}
    for key, value in campaign_profile.items():
        if isinstance(value, dict) and isinstance(profile.get(key), dict):
            merged = dict(profile[key])
            merged.update(value)
            profile[key] = merged
        else:
            profile[key] = value
    profile["style"] = "listening-feedback-calibration-v1"
    return profile


def collect_provider_tags(text: str) -> list[str]:
    return [match.group(0) for match in PROVIDER_TAG_RE.finditer(text or "")]


def cue_counts(cues: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"emphasis": 0, "pause": 0, "pitch": 0, "rate": 0, "stretch": 0}
    for cue in cues:
        cue_type = cue.get("type")
        counts[cue_type] = counts.get(cue_type, 0) + 1
    return counts


def target_allowed(target: str, *, language: str, profile: dict[str, Any]) -> bool:
    normalized_target = normalize_text(target)
    if not normalized_target:
        return False
    blocked = {normalize_text(item) for item in profile.get("blocked_single_word_emphasis", {}).get(language, [])}
    if normalized_target in blocked:
        return False
    allowed = {normalize_text(item) for item in profile.get("allowed_emphasis_targets", {}).get(language, [])}
    return normalized_target in allowed


def apply_emphasis_target_guard(
    campaign: dict[str, Any],
    prosody: dict[str, Any],
    *,
    language: str,
) -> dict[str, Any]:
    language = normalize_language(language)
    profile = profile_from_campaign(campaign)
    source = deepcopy(prosody)
    if not profile.get("enabled", True) or not profile.get("emphasis_guard_enabled", True):
        return {
            "voice_milestone": "VOICE-036",
            "voice_listening_calibration_id": VOICE_LISTENING_CALIBRATION_ID,
            "enabled": bool(profile.get("enabled", True)),
            "language": language,
            "profile": profile,
            "blocked_emphasis_count": 0,
            "allowed_emphasis_count": sum(1 for cue in source.get("prosody_plan", []) if cue.get("type") == "emphasis"),
            "blocked_emphasis": [],
            "guarded_prosody": source,
        }

    blocked: list[dict[str, Any]] = []

    def filter_cues(cues: list[dict[str, Any]], *, record_blocked: bool) -> list[dict[str, Any]]:
        guarded = []
        for cue in cues:
            if cue.get("type") != "emphasis":
                guarded.append(cue)
                continue
            if target_allowed(str(cue.get("target", "")), language=language, profile=profile):
                guarded.append(cue)
                continue
            if record_blocked:
                blocked.append(
                    {
                        "segment_id": cue.get("segment_id"),
                        "segment_type": cue.get("segment_type"),
                        "target": cue.get("target"),
                        "reason": "blocked_by_conservative_emphasis_guard",
                    }
                )
        return guarded

    guarded = deepcopy(source)
    guarded["prosody_plan"] = filter_cues(source.get("prosody_plan", []), record_blocked=True)
    for segment in guarded.get("output_segments", []):
        segment["cues"] = filter_cues(segment.get("cues", []), record_blocked=False)
        segment["cue_count"] = len(segment["cues"])
        segment["debug_text"] = str(segment.get("debug_text", "")).replace("**", "")
    guarded["cue_count"] = len(guarded.get("prosody_plan", []))
    guarded["cue_counts"] = cue_counts(guarded.get("prosody_plan", []))
    guarded["debug_text"] = str(guarded.get("debug_text", "")).replace("**", "")
    guarded["voice_emphasis_guard_id"] = VOICE_LISTENING_CALIBRATION_ID
    return {
        "voice_milestone": "VOICE-036",
        "voice_listening_calibration_id": VOICE_LISTENING_CALIBRATION_ID,
        "enabled": True,
        "language": language,
        "profile": profile,
        "blocked_emphasis_count": len(blocked),
        "allowed_emphasis_count": sum(1 for cue in guarded.get("prosody_plan", []) if cue.get("type") == "emphasis"),
        "blocked_emphasis": blocked,
        "guarded_prosody": guarded,
    }


def segment_is_protected(segment: dict[str, Any], profile: dict[str, Any]) -> bool:
    protected_types = set(profile.get("protected_segment_types", PROTECTED_SEGMENT_TYPES))
    return (
        segment.get("protected_reason") is not None
        or segment.get("segment_type") in protected_types
        or segment.get("eligible_for_prosody") is False
    )


def format_break(seconds: float) -> str:
    text = f"{seconds:.3f}".rstrip("0").rstrip(".")
    return f"<break time=\"{text}s\" />"


def relax_german_segment(segment: dict[str, Any], *, profile: dict[str, Any]) -> dict[str, Any]:
    source_text = segment.get("rendered_text", "")
    protected = segment_is_protected(segment, profile)
    if protected:
        return {
            "segment_id": segment.get("segment_id"),
            "segment_type": segment.get("segment_type"),
            "protected": True,
            "source_text": source_text,
            "calibrated_text": source_text,
            "adjustments": [],
        }

    break_tag = format_break(float(profile.get("german_connected_break_seconds", 0.08)))
    calibrated_text, count = GERMAN_COMPRESSED_OPENING_RE.subn(rf"\1 {break_tag} also geht's", source_text, count=1)
    adjustments = []
    if count:
        adjustments.append(
            {
                "adjustment_id": "de-relax-connected-opening",
                "reason": "VOICE-035 listening feedback: German connected phrase was too compressed.",
                "break_tag": break_tag,
            }
        )
    return {
        "segment_id": segment.get("segment_id"),
        "segment_type": segment.get("segment_type"),
        "protected": False,
        "source_text": source_text,
        "calibrated_text": calibrated_text,
        "adjustments": adjustments,
    }


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
        if segment["protected"] and segment["source_text"] != segment["calibrated_text"]
    ]
    markdown_in_rendered_text = "**" in calibrated_rendering.get("rendered_text", "")
    speed_out_of_bounds = False
    if language == "de" and any(segment["adjustments"] for segment in segment_plan):
        low, high = profile.get("german_relaxed_speed_bounds", [1.03, 1.08])
        speed = float((calibrated_rendering.get("voice_settings") or {}).get("speed", 1.0))
        speed_out_of_bounds = not (float(low) <= speed <= float(high))
    boundary_flags_changed = any(
        bool(source_rendering.get(flag)) != bool(calibrated_rendering.get(flag))
        for flag in [
            "api_call_made",
            "requires_api_key",
            "customer_audio_uploaded",
            "voice_cloning_used",
            "generated_audio_created",
        ]
    )
    passed = not protected_segment_text_changes and not markdown_in_rendered_text and not speed_out_of_bounds and not boundary_flags_changed
    return {
        "passed": passed,
        "protected_segment_text_changes": protected_segment_text_changes,
        "markdown_in_rendered_text": markdown_in_rendered_text,
        "speed_out_of_bounds": speed_out_of_bounds,
        "boundary_flags_changed": boundary_flags_changed,
    }


def apply_voice_listening_calibration(
    campaign: dict[str, Any],
    provider_rendering: dict[str, Any],
    emphasis_guard: dict[str, Any],
    *,
    language: str,
    seed: str = "",
) -> dict[str, Any]:
    del seed
    language = normalize_language(language)
    profile = profile_from_campaign(campaign)
    source = deepcopy(provider_rendering)
    if language == "de":
        segment_plan = [
            relax_german_segment(segment, profile=profile)
            for segment in source.get("segment_renderings", [])
        ]
    else:
        segment_plan = [
            {
                "segment_id": segment.get("segment_id"),
                "segment_type": segment.get("segment_type"),
                "protected": segment_is_protected(segment, profile),
                "source_text": segment.get("rendered_text", ""),
                "calibrated_text": segment.get("rendered_text", ""),
                "adjustments": [],
            }
            for segment in source.get("segment_renderings", [])
        ]

    calibrated_segments = []
    for source_segment, plan in zip(source.get("segment_renderings", []), segment_plan):
        calibrated_segment = deepcopy(source_segment)
        calibrated_segment["rendered_text"] = plan["calibrated_text"]
        calibrated_segment["provider_tags_inserted"] = collect_provider_tags(plan["calibrated_text"])
        calibrated_segment["voice_listening_calibration"] = {
            "tuned": bool(plan["adjustments"]),
            "adjustments": plan["adjustments"],
        }
        calibrated_segments.append(calibrated_segment)

    rendered_text = " ".join(
        segment["rendered_text"].strip()
        for segment in calibrated_segments
        if segment["rendered_text"].strip()
    )
    calibrated = deepcopy(source)
    calibrated["rendered_text"] = rendered_text
    calibrated["rendered_text_html_preview"] = html.escape(rendered_text)
    calibrated["segment_renderings"] = calibrated_segments
    calibrated["provider_tag_count"] = len(collect_provider_tags(rendered_text))
    calibrated["protected_segment_provider_tag_count"] = sum(
        len(segment.get("provider_tags_inserted", []))
        for segment in calibrated_segments
        if segment.get("protected_reason") is not None
    )
    calibrated["voice_listening_calibration_id"] = VOICE_LISTENING_CALIBRATION_ID

    listening_adjustment_count = sum(len(plan["adjustments"]) for plan in segment_plan)
    voice_settings = deepcopy(calibrated.get("voice_settings") or {})
    german_connected_speech_relaxed = language == "de" and listening_adjustment_count > 0
    if german_connected_speech_relaxed and calibrated.get("provider_key") == "elevenlabs":
        voice_settings["speed"] = float(profile.get("german_relaxed_speed", 1.065))
        calibrated["voice_settings"] = voice_settings

    validation = validate_calibration(
        source_rendering=source,
        calibrated_rendering=calibrated,
        segment_plan=segment_plan,
        language=language,
        profile=profile,
    )
    return {
        "voice_milestone": "VOICE-036",
        "voice_listening_calibration_id": VOICE_LISTENING_CALIBRATION_ID,
        "enabled": bool(profile.get("enabled", True)),
        "language": language,
        "profile": profile,
        "emphasis_guard": {
            "blocked_emphasis_count": int(emphasis_guard.get("blocked_emphasis_count", 0)),
            "allowed_emphasis_count": int(emphasis_guard.get("allowed_emphasis_count", 0)),
            "blocked_emphasis": emphasis_guard.get("blocked_emphasis", []),
        },
        "german_connected_speech_relaxed": german_connected_speech_relaxed,
        "listening_adjustment_count": listening_adjustment_count,
        "segment_plan": segment_plan,
        "calibrated_provider_rendering": calibrated,
        "validation": validation,
        "runtime_boundary": {
            "provider_calls_made": False,
            "requires_api_key": False,
            "customer_audio_uploaded": False,
            "voice_cloning_used": False,
            "generated_audio_created": False,
            "changes_allowed": "provider-facing emphasis filtering, tiny German breath tag, and bounded German speed relaxation only",
            "changes_forbidden": [
                "changing final_response",
                "changing campaign or compliance text",
                "changing sales policy decisions",
                "adding product claims or promises",
                "uploading customer audio",
            ],
        },
    }
