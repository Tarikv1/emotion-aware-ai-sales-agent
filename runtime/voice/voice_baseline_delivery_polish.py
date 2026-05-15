#!/usr/bin/env python3
from __future__ import annotations

import html
import re
from copy import deepcopy
from typing import Any


VOICE_BASELINE_DELIVERY_POLISH_ID = "VOICE-044-baseline-delivery-polish"

BREAK_TAG_RE = re.compile(r"<break\s+time=\"(?P<value>[0-9.]+)(?P<unit>ms|s)\"\s*/?>", re.IGNORECASE)
PROVIDER_TAG_RE = re.compile(r"<[^>]+>")

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
    "style": "baseline-shaped-runtime-polish-v1",
    "protected_segment_types": sorted(PROTECTED_SEGMENT_TYPES),
    "english_fast_filler_cleanup": True,
    "german_connector_cleanup": True,
    "german_long_break_cap_seconds": 0.18,
}


def normalize_language(language: str | None) -> str:
    return "de" if str(language or "").lower().startswith("de") else "en"


def profile_from_campaign(campaign: dict[str, Any]) -> dict[str, Any]:
    profile = deepcopy(DEFAULT_PROFILE)
    campaign_profile = campaign.get("voice_baseline_delivery_polish") or campaign.get("baseline_delivery_polish") or {}
    for key, value in campaign_profile.items():
        if isinstance(value, dict) and isinstance(profile.get(key), dict):
            merged = dict(profile[key])
            merged.update(value)
            profile[key] = merged
        else:
            profile[key] = value
    profile["style"] = "baseline-shaped-runtime-polish-v1"
    try:
        profile["german_long_break_cap_seconds"] = max(0.08, float(profile.get("german_long_break_cap_seconds", 0.18)))
    except (TypeError, ValueError):
        profile["german_long_break_cap_seconds"] = DEFAULT_PROFILE["german_long_break_cap_seconds"]
    return profile


def segment_is_protected(segment: dict[str, Any], profile: dict[str, Any]) -> bool:
    protected_types = set(profile.get("protected_segment_types", PROTECTED_SEGMENT_TYPES))
    return (
        segment.get("protected_reason") is not None
        or segment.get("segment_type") in protected_types
        or segment.get("eligible_for_prosody") is False
    )


def collect_provider_tags(text: str) -> list[str]:
    return [match.group(0) for match in PROVIDER_TAG_RE.finditer(text or "")]


def break_to_seconds(match: re.Match[str]) -> float:
    value = float(match.group("value"))
    return value / 1000 if match.group("unit").lower() == "ms" else value


def format_seconds(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def cleanup_english_fast_fillers(text: str) -> tuple[str, list[dict[str, Any]]]:
    adjustments: list[dict[str, Any]] = []

    def replace(match: re.Match[str]) -> str:
        filler = match.group("filler").lower()
        target = match.group("target")
        replacement = f". {target[:1].upper()}{target[1:]}"
        adjustments.append(
            {
                "adjustment_id": f"en-remove-fast-{filler}-trust-filler",
                "reason": "VOICE-042/VOICE-043 listening path: short mid-sentence filler can blur in trust-style lines.",
                "before": match.group(0),
                "after": replacement,
            }
        )
        return replacement

    pattern = re.compile(r",\s*(?P<filler>so|well),\s+(?P<target>you're right to ask\b)", re.IGNORECASE)
    output = pattern.sub(replace, text)

    def replace_sentence_filler(match: re.Match[str]) -> str:
        filler = match.group("filler").lower()
        target = match.group("target")
        replacement = f". {target[:1].upper()}{target[1:]}"
        adjustments.append(
            {
                "adjustment_id": f"en-remove-fast-{filler}-trust-sentence-filler",
                "reason": "VOICE-044 baseline polish: short filler after a break blurred in trust-style lines.",
                "before": match.group(0),
                "after": replacement,
            }
        )
        return replacement

    sentence_pattern = re.compile(
        r"\.\s*(?:<break\s+time=\"[0-9.]+(?:ms|s)\"\s*/?>\s*)?(?P<filler>um|uh|so|well),\s+(?P<target>you're right to ask\b)",
        re.IGNORECASE,
    )
    return sentence_pattern.sub(replace_sentence_filler, output), adjustments


def cleanup_german_connector(text: str) -> tuple[str, list[dict[str, Any]]]:
    adjustments: list[dict[str, Any]] = []

    def replace(match: re.Match[str]) -> str:
        adjustments.append(
            {
                "adjustment_id": "de-lower-also-wenns-connector",
                "reason": "Avoid artificial sentence-case connector after connected-speech joining.",
                "before": match.group(0),
                "after": "also wenn's",
            }
        )
        return "also wenn's"

    output = re.sub(r"\b[Aa]lso,?\s+Wenn's", replace, text)

    def replace_aeh(match: re.Match[str]) -> str:
        replacement = f"{match.group('prefix')}Wenn's"
        adjustments.append(
            {
                "adjustment_id": "de-remove-fast-aeh-before-wenns",
                "reason": "Remove a clipped filler before a short next-step connector in the baseline German path.",
                "before": match.group(0),
                "after": replacement,
            }
        )
        return replacement

    aeh_pattern = re.compile(
        r"(?P<prefix>(?:<break\s+time=\"[0-9.]+(?:ms|s)\"\s*/?>\s*)?)Äh,\s+Wenn's",
        re.IGNORECASE,
    )
    return aeh_pattern.sub(replace_aeh, output), adjustments


def cap_german_breaks(text: str, cap_seconds: float) -> tuple[str, list[dict[str, Any]]]:
    adjustments: list[dict[str, Any]] = []

    def replace(match: re.Match[str]) -> str:
        original_seconds = break_to_seconds(match)
        if original_seconds <= cap_seconds:
            return match.group(0)
        replacement = f"<break time=\"{format_seconds(cap_seconds)}s\" />"
        adjustments.append(
            {
                "adjustment_id": "de-cap-long-baseline-break",
                "reason": "Keep German baseline pauses present but less dense after listening feedback.",
                "before": match.group(0),
                "after": replacement,
                "original_seconds": round(original_seconds, 3),
                "capped_seconds": round(cap_seconds, 3),
            }
        )
        return replacement

    return BREAK_TAG_RE.sub(replace, text), adjustments


def polish_text(text: str, *, language: str, profile: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    output = text
    adjustments: list[dict[str, Any]] = []
    if language == "en" and profile.get("english_fast_filler_cleanup", True):
        output, new_adjustments = cleanup_english_fast_fillers(output)
        adjustments.extend(new_adjustments)
    if language == "de":
        if profile.get("german_long_break_cap_seconds", 0) > 0:
            output, new_adjustments = cap_german_breaks(output, float(profile["german_long_break_cap_seconds"]))
            adjustments.extend(new_adjustments)
        if profile.get("german_connector_cleanup", True):
            output, new_adjustments = cleanup_german_connector(output)
            adjustments.extend(new_adjustments)
    return output, adjustments


def validate_polish(
    *,
    source_rendering: dict[str, Any],
    polished_rendering: dict[str, Any],
    segment_plan: list[dict[str, Any]],
) -> dict[str, Any]:
    protected_segment_text_changes = [
        segment["segment_id"]
        for segment in segment_plan
        if segment["protected"] and segment["source_text"] != segment["polished_text"]
    ]
    boundary_flags_changed = any(
        bool(source_rendering.get(flag)) != bool(polished_rendering.get(flag))
        for flag in [
            "api_call_made",
            "requires_api_key",
            "customer_audio_uploaded",
            "voice_cloning_used",
            "generated_audio_created",
        ]
    )
    voice_settings_changed = source_rendering.get("voice_settings", {}) != polished_rendering.get("voice_settings", {})
    markdown_in_rendered_text = "**" in polished_rendering.get("rendered_text", "")
    passed = not protected_segment_text_changes and not boundary_flags_changed and not voice_settings_changed and not markdown_in_rendered_text
    return {
        "passed": passed,
        "protected_segment_text_changes": protected_segment_text_changes,
        "boundary_flags_changed": boundary_flags_changed,
        "voice_settings_changed": voice_settings_changed,
        "markdown_in_rendered_text": markdown_in_rendered_text,
    }


def apply_voice_baseline_delivery_polish(
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
    if not profile.get("enabled", True):
        validation = validate_polish(source_rendering=source, polished_rendering=source, segment_plan=[])
        return {
            "voice_milestone": "VOICE-044",
            "voice_baseline_delivery_polish_id": VOICE_BASELINE_DELIVERY_POLISH_ID,
            "enabled": False,
            "applied": False,
            "language": language,
            "profile": profile,
            "adjustment_count": 0,
            "adjustments": [],
            "segment_plan": [],
            "polished_provider_rendering": source,
            "validation": validation,
            "runtime_boundary": runtime_boundary(),
        }

    segment_plan: list[dict[str, Any]] = []
    polished_segments = []
    all_adjustments: list[dict[str, Any]] = []
    for segment in source.get("segment_renderings", []):
        segment_copy = deepcopy(segment)
        protected = segment_is_protected(segment_copy, profile)
        source_text = str(segment_copy.get("rendered_text", ""))
        if protected:
            polished_text = source_text
            adjustments: list[dict[str, Any]] = []
        else:
            polished_text, adjustments = polish_text(source_text, language=language, profile=profile)
        for adjustment in adjustments:
            adjustment["segment_id"] = segment_copy.get("segment_id")
            adjustment["segment_type"] = segment_copy.get("segment_type")
        all_adjustments.extend(adjustments)
        segment_copy["rendered_text"] = polished_text
        segment_copy["provider_tags_inserted"] = collect_provider_tags(polished_text)
        if adjustments:
            segment_copy["voice_baseline_delivery_polish"] = {
                "tuned": True,
                "adjustments": adjustments,
            }
        polished_segments.append(segment_copy)
        segment_plan.append(
            {
                "segment_id": segment_copy.get("segment_id"),
                "segment_type": segment_copy.get("segment_type"),
                "protected": protected,
                "source_text": source_text,
                "polished_text": polished_text,
                "adjustment_count": len(adjustments),
                "adjustments": adjustments,
            }
        )

    if all_adjustments:
        rendered_text = " ".join(segment["rendered_text"].strip() for segment in polished_segments if segment.get("rendered_text", "").strip())
        polished = deepcopy(source)
        polished["rendered_text"] = rendered_text
        polished["rendered_text_html_preview"] = html.escape(rendered_text)
        polished["segment_renderings"] = polished_segments
        polished["provider_tag_count"] = len(collect_provider_tags(rendered_text))
        polished["protected_segment_provider_tag_count"] = sum(
            len(segment.get("provider_tags_inserted", []))
            for segment in polished_segments
            if segment.get("protected_reason") is not None
        )
        polished["baseline_delivery_polish_applied"] = True
        polished["voice_baseline_delivery_polish_id"] = VOICE_BASELINE_DELIVERY_POLISH_ID
    else:
        polished = deepcopy(source)

    validation = validate_polish(
        source_rendering=source,
        polished_rendering=polished,
        segment_plan=segment_plan,
    )
    return {
        "voice_milestone": "VOICE-044",
        "voice_baseline_delivery_polish_id": VOICE_BASELINE_DELIVERY_POLISH_ID,
        "enabled": True,
        "applied": bool(all_adjustments),
        "language": language,
        "profile": profile,
        "adjustment_count": len(all_adjustments),
        "adjustments": all_adjustments,
        "segment_plan": segment_plan,
        "polished_provider_rendering": polished,
        "validation": validation,
        "runtime_boundary": runtime_boundary(),
    }


def runtime_boundary() -> dict[str, Any]:
    return {
        "provider_calls_made": False,
        "requires_api_key": False,
        "customer_audio_uploaded": False,
        "voice_cloning_used": False,
        "generated_audio_created": False,
        "changes_allowed": "provider-facing baseline TTS polish only for eligible freeform segments",
        "changes_forbidden": [
            "changing final_response",
            "changing protected campaign, compliance, handoff, hangup, or do-not-call text",
            "changing provider speed, style, stability, or voice identity settings",
            "enabling private-pattern provider settings",
            "adding claims, pressure, or urgency",
            "reading or uploading private audio",
        ],
    }
