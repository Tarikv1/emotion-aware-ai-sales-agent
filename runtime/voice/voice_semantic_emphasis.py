#!/usr/bin/env python3
from __future__ import annotations

import html
import re
from copy import deepcopy
from typing import Any


VOICE_SEMANTIC_EMPHASIS_ID = "VOICE-039-runtime-semantic-emphasis"
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
    "style": "clear-simple-runtime-wording-v1",
    "protected_segment_types": sorted(PROTECTED_SEGMENT_TYPES),
    "languages": ["en"],
    "max_rewrites_per_segment": 1,
    "rewrite_rules": [
        {
            "rule_id": "en-clear-open-review-worth-time",
            "pattern": r"\bthe practical next step is to check whether reviewing options is worth your time\b",
            "replacement": "we can quickly check if a review is worth your time",
            "reason": "VOICE-038 listening review preferred the clear/simple clause over the fragile abstract clause.",
        },
        {
            "rule_id": "en-clear-open-a-review-worth-time",
            "pattern": r"\bthe practical next step is to check whether a review is worth your time\b",
            "replacement": "we can quickly check if a review is worth your time",
            "reason": "VOICE-038 listening review preferred the clear/simple clause over the fragile abstract clause.",
        },
    ],
}


def normalize_language(language: str | None) -> str:
    return "de" if str(language or "").lower().startswith("de") else "en"


def profile_from_campaign(campaign: dict[str, Any]) -> dict[str, Any]:
    profile = deepcopy(DEFAULT_PROFILE)
    campaign_profile = campaign.get("voice_semantic_emphasis") or campaign.get("semantic_emphasis") or {}
    for key, value in campaign_profile.items():
        if isinstance(value, dict) and isinstance(profile.get(key), dict):
            merged = dict(profile[key])
            merged.update(value)
            profile[key] = merged
        else:
            profile[key] = value
    profile["style"] = "clear-simple-runtime-wording-v1"
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
        replacement = replacement_with_matching_case(match.group(0), str(rule["replacement"]))
        output = pattern.sub(replacement, output, count=1)
        rewrites.append(
            {
                "rule_id": rule["rule_id"],
                "segment_id": segment_id,
                "segment_type": segment_type,
                "before": match.group(0),
                "after": replacement,
                "reason": rule.get("reason", "clear_simple_runtime_wording"),
            }
        )
    return output, rewrites


def validate_semantic_emphasis(
    *,
    source_rendering: dict[str, Any],
    semantic_rendering: dict[str, Any],
    segment_plan: list[dict[str, Any]],
    language: str,
    enabled: bool,
) -> dict[str, Any]:
    protected_segment_text_changes = [
        segment["segment_id"]
        for segment in segment_plan
        if segment["protected"] and segment["source_text"] != segment["semantic_text"]
    ]
    non_english_rewrite_count = (
        sum(segment["rewrite_count"] for segment in segment_plan)
        if normalize_language(language) != "en"
        else 0
    )
    markdown_in_rendered_text = "**" in semantic_rendering.get("rendered_text", "")
    plain_text_changed = source_rendering.get("plain_text") != semantic_rendering.get("plain_text")
    boundary_flags_changed = any(
        bool(source_rendering.get(flag)) != bool(semantic_rendering.get(flag))
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


def apply_voice_semantic_emphasis(
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
    semantic_segments = []
    rewrites: list[dict[str, Any]] = []

    for source_segment in source.get("segment_renderings", []):
        protected = segment_is_protected(source_segment, profile)
        source_text = str(source_segment.get("rendered_text", ""))
        if enabled and language_allowed and not protected:
            semantic_text, segment_rewrites = rewrite_segment_text(
                source_text,
                profile=profile,
                segment_id=source_segment.get("segment_id"),
                segment_type=source_segment.get("segment_type"),
            )
        else:
            semantic_text = source_text
            segment_rewrites = []

        semantic_segment = deepcopy(source_segment)
        semantic_segment["rendered_text"] = semantic_text
        semantic_segment["provider_tags_inserted"] = collect_provider_tags(semantic_text)
        semantic_segment["voice_semantic_emphasis"] = {
            "tuned": bool(segment_rewrites),
            "rewrite_count": len(segment_rewrites),
            "rewrites": segment_rewrites,
        }
        semantic_segments.append(semantic_segment)
        rewrites.extend(segment_rewrites)
        segment_plan.append(
            {
                "segment_id": source_segment.get("segment_id"),
                "segment_type": source_segment.get("segment_type"),
                "protected": protected,
                "protected_reason": source_segment.get("protected_reason") or ("protected_segment_type" if protected else None),
                "source_text": source_text,
                "semantic_text": semantic_text,
                "rewrite_count": len(segment_rewrites),
            }
        )

    rendered_text = " ".join(
        segment["rendered_text"].strip()
        for segment in semantic_segments
        if segment["rendered_text"].strip()
    )
    semantic = deepcopy(source)
    semantic["rendered_text"] = rendered_text
    semantic["rendered_text_html_preview"] = html.escape(rendered_text)
    semantic["segment_renderings"] = semantic_segments
    provider_tags = [tag for segment in semantic_segments for tag in segment.get("provider_tags_inserted", [])]
    semantic["provider_tag_count"] = len(provider_tags)
    semantic["protected_segment_provider_tag_count"] = sum(
        len(segment.get("provider_tags_inserted", []))
        for segment in semantic_segments
        if segment.get("protected_reason") is not None
    )
    semantic["semantic_emphasis_candidate_applied"] = bool(rewrites)
    semantic["voice_semantic_emphasis_id"] = VOICE_SEMANTIC_EMPHASIS_ID

    validation = validate_semantic_emphasis(
        source_rendering=source,
        semantic_rendering=semantic,
        segment_plan=segment_plan,
        language=normalized_language,
        enabled=enabled,
    )
    return {
        "voice_milestone": "VOICE-039",
        "voice_semantic_emphasis_id": VOICE_SEMANTIC_EMPHASIS_ID,
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
        "semantic_rendered_text": semantic.get("rendered_text", ""),
        "semantic_provider_rendering": semantic,
        "validation": validation,
        "runtime_boundary": {
            "provider_calls_made": False,
            "requires_api_key": False,
            "customer_audio_uploaded": False,
            "voice_cloning_used": False,
            "generated_audio_created": False,
            "changes_allowed": "provider-facing freeform English TTS wording only, promoted from VOICE-038 listening feedback",
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
