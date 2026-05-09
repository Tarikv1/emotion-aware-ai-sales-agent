#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
from typing import Any


VOICE_PRIVATE_PATTERN_PROFILE_ID = "VOICE-041-private-pattern-profile"

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
    "enabled": False,
    "review_status": "not_configured",
    "source_review_milestone": None,
    "source_kind": None,
    "rhythm_density_hint": None,
    "expressiveness_variation_hint": None,
    "presence_level_hint": None,
    "elevenlabs_style_target": 0.06,
    "elevenlabs_stability_delta": -0.01,
    "elevenlabs_min_stability": 0.40,
    "elevenlabs_max_style": 0.08,
    "protected_segment_types": sorted(PROTECTED_SEGMENT_TYPES),
}


def normalize_language(language: str | None) -> str:
    return "de" if str(language or "").lower().startswith("de") else "en"


def clamp_float(value: float, low: float, high: float, digits: int = 3) -> float:
    return round(min(high, max(low, value)), digits)


def profile_from_campaign(campaign: dict[str, Any]) -> dict[str, Any]:
    profile = deepcopy(DEFAULT_PROFILE)
    campaign_profile = campaign.get("voice_private_pattern_profile") or campaign.get("private_speech_pattern_profile") or {}
    for key, value in campaign_profile.items():
        if isinstance(value, dict) and isinstance(profile.get(key), dict):
            merged = dict(profile[key])
            merged.update(value)
            profile[key] = merged
        else:
            profile[key] = value
    return profile


def segment_is_protected(segment: dict[str, Any], profile: dict[str, Any]) -> bool:
    protected_types = set(profile.get("protected_segment_types", PROTECTED_SEGMENT_TYPES))
    return (
        segment.get("protected_reason") is not None
        or segment.get("segment_type") in protected_types
        or segment.get("eligible_for_prosody") is False
    )


def profile_blocked_reason(
    profile: dict[str, Any],
    provider_rendering: dict[str, Any],
) -> str | None:
    if not profile.get("enabled", False):
        return "profile_disabled"
    if profile.get("review_status") != "accepted":
        return "profile_not_human_accepted"
    if profile.get("source_review_milestone") != "VOICE-031":
        return "unsupported_source_review_milestone"
    if profile.get("source_kind") != "abstract_private_speech_patterns":
        return "unsupported_source_kind"
    segments = provider_rendering.get("segment_renderings", [])
    if not segments:
        return "no_segments_available"
    if any(segment_is_protected(segment, profile) for segment in segments):
        return "protected_or_ineligible_segment_present"
    return None


def apply_elevenlabs_settings(
    voice_settings: dict[str, Any],
    profile: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    settings = deepcopy(voice_settings)
    adjustments: list[dict[str, Any]] = []
    expressiveness = profile.get("expressiveness_variation_hint")
    if expressiveness == "higher_expressiveness_variation_candidate":
        original_style = float(settings.get("style", 0.0))
        target_style = clamp_float(
            float(profile.get("elevenlabs_style_target", DEFAULT_PROFILE["elevenlabs_style_target"])),
            0.0,
            float(profile.get("elevenlabs_max_style", DEFAULT_PROFILE["elevenlabs_max_style"])),
        )
        settings["style"] = max(original_style, target_style)
        adjustments.append(
            {
                "setting": "style",
                "before": round(original_style, 3),
                "after": settings["style"],
                "reason": "higher_expressiveness_variation_candidate",
            }
        )

        original_stability = float(settings.get("stability", 0.45))
        delta = float(profile.get("elevenlabs_stability_delta", DEFAULT_PROFILE["elevenlabs_stability_delta"]))
        min_stability = float(profile.get("elevenlabs_min_stability", DEFAULT_PROFILE["elevenlabs_min_stability"]))
        settings["stability"] = clamp_float(original_stability + delta, min_stability, 1.0)
        adjustments.append(
            {
                "setting": "stability",
                "before": round(original_stability, 3),
                "after": settings["stability"],
                "reason": "bounded_variation_without_voice_cloning",
            }
        )
        return settings, adjustments, "bounded_elevenlabs_expressiveness_settings"
    return settings, adjustments, "no_provider_setting_adjustment"


def apply_provider_settings(
    provider_rendering: dict[str, Any],
    profile: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    provider_key = provider_rendering.get("provider_key")
    if provider_key != "elevenlabs":
        return deepcopy(provider_rendering), [], "unsupported_provider_metadata_only"
    profiled = deepcopy(provider_rendering)
    settings, adjustments, action = apply_elevenlabs_settings(profiled.get("voice_settings", {}), profile)
    profiled["voice_settings"] = settings
    return profiled, adjustments, action


def add_segment_metadata(provider_rendering: dict[str, Any], profile: dict[str, Any], *, applied: bool) -> dict[str, Any]:
    profiled = deepcopy(provider_rendering)
    for segment in profiled.get("segment_renderings", []):
        segment["voice_private_pattern_profile"] = {
            "applied": applied,
            "rhythm_density_hint": profile.get("rhythm_density_hint"),
            "expressiveness_variation_hint": profile.get("expressiveness_variation_hint"),
            "presence_level_hint": profile.get("presence_level_hint"),
            "text_changed": False,
        }
    return profiled


def validate_private_pattern_profile(
    *,
    source_rendering: dict[str, Any],
    profiled_rendering: dict[str, Any],
    applied: bool,
) -> dict[str, Any]:
    source_text = source_rendering.get("rendered_text")
    profiled_text = profiled_rendering.get("rendered_text")
    segment_text_changes = [
        segment.get("segment_id")
        for source_segment, segment in zip(
            source_rendering.get("segment_renderings", []),
            profiled_rendering.get("segment_renderings", []),
        )
        if source_segment.get("rendered_text") != segment.get("rendered_text")
    ]
    boundary_flags_changed = any(
        bool(source_rendering.get(flag)) != bool(profiled_rendering.get(flag))
        for flag in [
            "api_call_made",
            "requires_api_key",
            "customer_audio_uploaded",
            "voice_cloning_used",
            "generated_audio_created",
        ]
    )
    provider_call_made = bool(profiled_rendering.get("api_call_made", False))
    customer_audio_uploaded = bool(profiled_rendering.get("customer_audio_uploaded", False))
    voice_cloning_used = bool(profiled_rendering.get("voice_cloning_used", False))
    passed = (
        source_text == profiled_text
        and not segment_text_changes
        and not boundary_flags_changed
        and not provider_call_made
        and not customer_audio_uploaded
        and not voice_cloning_used
    )
    return {
        "passed": passed,
        "applied": applied,
        "rendered_text_unchanged": source_text == profiled_text,
        "segment_text_changes": segment_text_changes,
        "boundary_flags_changed": boundary_flags_changed,
        "provider_call_made": provider_call_made,
        "customer_audio_uploaded": customer_audio_uploaded,
        "voice_cloning_used": voice_cloning_used,
    }


def safe_profile_metadata(profile: dict[str, Any]) -> dict[str, Any]:
    allowed = [
        "enabled",
        "review_status",
        "source_review_milestone",
        "source_kind",
        "rhythm_density_hint",
        "expressiveness_variation_hint",
        "presence_level_hint",
        "elevenlabs_style_target",
        "elevenlabs_stability_delta",
        "elevenlabs_min_stability",
        "elevenlabs_max_style",
    ]
    return {key: profile.get(key) for key in allowed}


def apply_voice_private_pattern_profile(
    campaign: dict[str, Any],
    provider_rendering: dict[str, Any],
    *,
    language: str,
    seed: str = "",
) -> dict[str, Any]:
    del seed
    language = normalize_language(language)
    profile = profile_from_campaign(campaign)
    source = deepcopy(provider_rendering)
    blocked_reason = profile_blocked_reason(profile, source)
    applied = blocked_reason is None

    if applied:
        profiled, setting_adjustments, provider_action = apply_provider_settings(source, profile)
        profiled = add_segment_metadata(profiled, profile, applied=True)
    else:
        profiled = deepcopy(source)
        setting_adjustments = []
        provider_action = "blocked_or_disabled"

    if applied:
        profiled["voice_private_pattern_profile_applied"] = True
        profiled["voice_private_pattern_profile_id"] = VOICE_PRIVATE_PATTERN_PROFILE_ID
    validation = validate_private_pattern_profile(
        source_rendering=source,
        profiled_rendering=profiled,
        applied=applied,
    )
    return {
        "voice_milestone": "VOICE-041",
        "voice_private_pattern_profile_id": VOICE_PRIVATE_PATTERN_PROFILE_ID,
        "enabled": bool(profile.get("enabled", False)),
        "applied": applied,
        "blocked_reason": blocked_reason,
        "language": language,
        "profile": safe_profile_metadata(profile),
        "eligible_segment_count": sum(
            1 for segment in source.get("segment_renderings", []) if not segment_is_protected(segment, profile)
        ),
        "setting_adjustments": setting_adjustments,
        "provider_action": provider_action,
        "rhythm_density_action": (
            "metadata_only_no_pacing_change"
            if applied and profile.get("rhythm_density_hint") == "higher_turn_density_candidate"
            else "not_applied"
        ),
        "presence_action": (
            "blocked_low_presence_copy"
            if profile.get("presence_level_hint") == "lower_presence_candidate"
            else "not_applicable"
        ),
        "profiled_provider_rendering": profiled,
        "validation": validation,
        "runtime_boundary": {
            "provider_calls_made": False,
            "requires_api_key": False,
            "customer_audio_uploaded": False,
            "voice_cloning_used": False,
            "raw_audio_read": False,
            "transcription_created": False,
            "generated_audio_created": False,
            "changes_allowed": "bounded provider voice settings and segment metadata only for accepted abstract private speech-pattern profiles",
            "changes_forbidden": [
                "reading raw private audio at runtime",
                "uploading private audio",
                "voice cloning",
                "changing final_response",
                "rewriting provider text",
                "changing accepted pacing speed",
                "applying to protected or ineligible segments",
                "copying low vocal presence into the agent",
            ],
        },
    }
