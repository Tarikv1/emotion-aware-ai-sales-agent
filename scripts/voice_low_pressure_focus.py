#!/usr/bin/env python3
from __future__ import annotations

import html
import re
from copy import deepcopy
from typing import Any


VOICE_LOW_PRESSURE_FOCUS_ID = "VOICE-040-low-pressure-focus"
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
    "style": "low-pressure-focus-v1",
    "protected_segment_types": sorted(PROTECTED_SEGMENT_TYPES),
    "languages": ["en"],
    "max_rewrites_per_segment": 1,
    "rewrite_rules": [
        {
            "rule_id": "en-low-pressure-focus-with-bridge",
            "pattern": r"\byou (?:do not|don't) need to change anything today,\s+well,\s+(we can quickly check)",
            "replacement": r"no changes needed today, \1",
            "reason": "VOICE-039 listening feedback: avoid risky emphasis on the low-pressure phrase and keep the next step flowing.",
        },
        {
            "rule_id": "en-low-pressure-focus-plain",
            "pattern": r"\byou (?:do not|don't) need to change anything today\b",
            "replacement": "no changes needed today",
            "reason": "VOICE-039 listening feedback: avoid risky emphasis on the low-pressure phrase.",
        },
    ],
}


def normalize_language(language: str | None) -> str:
    return "de" if str(language or "").lower().startswith("de") else "en"


def profile_from_campaign(campaign: dict[str, Any]) -> dict[str, Any]:
    profile = deepcopy(DEFAULT_PROFILE)
    campaign_profile = campaign.get("voice_low_pressure_focus") or campaign.get("low_pressure_focus") or {}
    for key, value in campaign_profile.items():
        if isinstance(value, dict) and isinstance(profile.get(key), dict):
            merged = dict(profile[key])
            merged.update(value)
            profile[key] = merged
        else:
            profile[key] = value
    profile["style"] = "low-pressure-focus-v1"
    return profile


def collect_provider_tags(text: str) -> list[str]:
    return [match.group(0) for match in PROVIDER_TAG_RE.finditer(text or "")]


def segment_is_protected(segment: dict[str, Any], profile: dict[str, Any]) -> bool:
    protected_types = set(profile.get("protected_segment_types", PROTECTED_SEGMENT_TYPES))
    return (
        segment.get("protected_reason") is not None
        or segment.get("segment_type") in protected_types
        or segment.get("eligible_for_prosody") is False
    )


def replacement_with_matching_case(match_text: str, replacement: str) -> str:
    if not match_text:
        return replacement
    return replacement[:1].upper() + replacement[1:] if match_text[0].isupper() else replacement


def rewrite_segment_text(
    text: str,
    *,
    profile: dict[str, Any],
    segment_id: str | None,
    segment_type: str | None,
) -> tuple[str, list[dict[str, Any]]]:
    output = text
    rewrites: list[dict[str, Any]] = []
    max_rewrites = int(profile.get("max_rewrites_per_segment", 1))
    for rule in profile.get("rewrite_rules", []):
        if len(rewrites) >= max_rewrites:
            break
        pattern = re.compile(str(rule["pattern"]), re.IGNORECASE)
        match = pattern.search(output)
        if match is None:
            continue
        replacement = match.expand(str(rule["replacement"]))
        replacement = replacement_with_matching_case(match.group(0), replacement)
        output = pattern.sub(replacement, output, count=1)
        rewrites.append(
            {
                "rule_id": rule["rule_id"],
                "segment_id": segment_id,
                "segment_type": segment_type,
                "before": match.group(0),
                "after": replacement,
                "reason": rule.get("reason", "low_pressure_focus"),
            }
        )
    return output, rewrites


def validate_low_pressure_focus(
    *,
    source_rendering: dict[str, Any],
    focused_rendering: dict[str, Any],
    segment_plan: list[dict[str, Any]],
    language: str,
    enabled: bool,
) -> dict[str, Any]:
    protected_segment_text_changes = [
        segment["segment_id"]
        for segment in segment_plan
        if segment["protected"] and segment["source_text"] != segment["focused_text"]
    ]
    non_english_rewrite_count = (
        sum(segment["rewrite_count"] for segment in segment_plan)
        if normalize_language(language) != "en"
        else 0
    )
    markdown_in_rendered_text = "**" in focused_rendering.get("rendered_text", "")
    plain_text_changed = source_rendering.get("plain_text") != focused_rendering.get("plain_text")
    boundary_flags_changed = any(
        bool(source_rendering.get(flag)) != bool(focused_rendering.get(flag))
        for flag in [
            "api_call_made",
            "requires_api_key",
            "customer_audio_uploaded",
            "voice_cloning_used",
            "generated_audio_created",
        ]
    )
    passed = not (
        protected_segment_text_changes
        or non_english_rewrite_count
        or markdown_in_rendered_text
        or plain_text_changed
        or boundary_flags_changed
    )
    return {
        "passed": passed,
        "enabled": enabled,
        "protected_segment_text_changes": protected_segment_text_changes,
        "non_english_rewrite_count": non_english_rewrite_count,
        "markdown_in_rendered_text": markdown_in_rendered_text,
        "plain_text_changed": plain_text_changed,
        "boundary_flags_changed": boundary_flags_changed,
    }


def apply_voice_low_pressure_focus(
    campaign: dict[str, Any],
    provider_rendering: dict[str, Any],
    *,
    language: str,
    seed: str = "",
) -> dict[str, Any]:
    del seed
    normalized_language = normalize_language(language)
    profile = profile_from_campaign(campaign)
    source = deepcopy(provider_rendering)
    enabled = bool(profile.get("enabled", True))
    language_allowed = normalized_language in set(profile.get("languages", ["en"]))

    segment_plan: list[dict[str, Any]] = []
    focused_segments = []
    rewrites: list[dict[str, Any]] = []

    for source_segment in source.get("segment_renderings", []):
        protected = segment_is_protected(source_segment, profile)
        source_text = str(source_segment.get("rendered_text", ""))
        if enabled and language_allowed and not protected:
            focused_text, segment_rewrites = rewrite_segment_text(
                source_text,
                profile=profile,
                segment_id=source_segment.get("segment_id"),
                segment_type=source_segment.get("segment_type"),
            )
        else:
            focused_text = source_text
            segment_rewrites = []

        focused_segment = deepcopy(source_segment)
        focused_segment["rendered_text"] = focused_text
        focused_segment["provider_tags_inserted"] = collect_provider_tags(focused_text)
        focused_segment["voice_low_pressure_focus"] = {
            "tuned": bool(segment_rewrites),
            "rewrite_count": len(segment_rewrites),
            "rewrites": segment_rewrites,
        }
        focused_segments.append(focused_segment)
        rewrites.extend(segment_rewrites)
        segment_plan.append(
            {
                "segment_id": source_segment.get("segment_id"),
                "segment_type": source_segment.get("segment_type"),
                "protected": protected,
                "protected_reason": source_segment.get("protected_reason") or ("protected_segment_type" if protected else None),
                "source_text": source_text,
                "focused_text": focused_text,
                "rewrite_count": len(segment_rewrites),
            }
        )

    rendered_text = " ".join(
        segment["rendered_text"].strip()
        for segment in focused_segments
        if segment["rendered_text"].strip()
    )
    focused = deepcopy(source)
    focused["rendered_text"] = rendered_text
    focused["rendered_text_html_preview"] = html.escape(rendered_text)
    focused["segment_renderings"] = focused_segments
    provider_tags = [tag for segment in focused_segments for tag in segment.get("provider_tags_inserted", [])]
    focused["provider_tag_count"] = len(provider_tags)
    focused["protected_segment_provider_tag_count"] = sum(
        len(segment.get("provider_tags_inserted", []))
        for segment in focused_segments
        if segment.get("protected_reason") is not None
    )
    focused["low_pressure_focus_applied"] = bool(rewrites)
    focused["voice_low_pressure_focus_id"] = VOICE_LOW_PRESSURE_FOCUS_ID

    validation = validate_low_pressure_focus(
        source_rendering=source,
        focused_rendering=focused,
        segment_plan=segment_plan,
        language=normalized_language,
        enabled=enabled,
    )
    return {
        "voice_milestone": "VOICE-040",
        "voice_low_pressure_focus_id": VOICE_LOW_PRESSURE_FOCUS_ID,
        "enabled": enabled,
        "language": normalized_language,
        "language_allowed": language_allowed,
        "profile": profile,
        "eligible_segment_count": sum(1 for segment in segment_plan if not segment["protected"] and language_allowed and enabled),
        "protected_segment_count": sum(1 for segment in segment_plan if segment["protected"]),
        "rewrite_count": len(rewrites),
        "rewrites": rewrites,
        "segment_plan": segment_plan,
        "source_rendered_text": source.get("rendered_text", ""),
        "focused_rendered_text": focused.get("rendered_text", ""),
        "focused_provider_rendering": focused,
        "validation": validation,
        "runtime_boundary": {
            "provider_calls_made": False,
            "requires_api_key": False,
            "customer_audio_uploaded": False,
            "voice_cloning_used": False,
            "generated_audio_created": False,
            "changes_allowed": "provider-facing freeform English low-pressure wording only, based on VOICE-039 listening feedback",
            "changes_forbidden": [
                "changing final_response",
                "changing call_control",
                "changing protected campaign or compliance text",
                "rewriting German text",
                "adding claims",
                "uploading customer audio",
                "voice cloning",
            ],
        },
    }
