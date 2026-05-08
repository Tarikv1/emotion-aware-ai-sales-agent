#!/usr/bin/env python3
from __future__ import annotations

import html
import re
from copy import deepcopy
from typing import Any, Callable


VOICE_CONNECTED_SPEECH_ID = "VOICE-035-connected-speech-phrase-flow"

BREAK_TAG_RE = re.compile(r"<break\s+time=\"[0-9.]+(?:ms|s)\"\s*/?>\s*", re.IGNORECASE)
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
    "style": "professional-connected-speech-v1",
    "protected_segment_types": sorted(PROTECTED_SEGMENT_TYPES),
    "join_sentence_to_thinking_filler": True,
    "join_short_bridge_sentence": True,
    "max_flow_joins_per_segment": 3,
}


def normalize_language(language: str | None) -> str:
    return "de" if str(language or "").lower().startswith("de") else "en"


def profile_from_campaign(campaign: dict[str, Any]) -> dict[str, Any]:
    profile = deepcopy(DEFAULT_PROFILE)
    campaign_profile = campaign.get("voice_connected_speech") or campaign.get("connected_speech") or {}
    for key, value in campaign_profile.items():
        if isinstance(value, dict) and isinstance(profile.get(key), dict):
            merged = dict(profile[key])
            merged.update(value)
            profile[key] = merged
        else:
            profile[key] = value
    profile["style"] = "professional-connected-speech-v1"
    return profile


def segment_is_protected(segment: dict[str, Any], profile: dict[str, Any]) -> bool:
    protected_types = set(profile.get("protected_segment_types", PROTECTED_SEGMENT_TYPES))
    return (
        segment.get("protected_reason") is not None
        or segment.get("segment_type") in protected_types
        or segment.get("eligible_for_prosody") is False
    )


def collapse_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def apply_rule_once(
    text: str,
    *,
    rule_id: str,
    pattern: re.Pattern[str],
    replacement: str | Callable[[re.Match[str]], str],
) -> tuple[str, dict[str, Any] | None]:
    match = pattern.search(text)
    if match is None:
        return text, None
    before = match.group(0)
    after = pattern.sub(replacement, text, count=1)
    after_match = pattern.search(after)
    operation = {
        "rule_id": rule_id,
        "before": before,
        "after_text_changed": before not in after,
        "remaining_same_pattern": after_match is not None,
    }
    return after, operation


def english_patterns() -> list[tuple[str, re.Pattern[str], str | Callable[[re.Match[str]], str]]]:
    return [
        (
            "en-join-trust-repair-transition",
            re.compile(
                r"\.\s*(?:<break\s+time=\"[0-9.]+(?:ms|s)\"\s*/?>\s*)?(?:That's why I'll|That is why I will)\b",
                re.IGNORECASE,
            ),
            ", so I'll",
        ),
        (
            "en-join-filler-after-short-sentence",
            re.compile(r"\.\s*(?:<break\s+time=\"[0-9.]+(?:ms|s)\"\s*/?>\s*)?Well,\s+", re.IGNORECASE),
            ", well, ",
        ),
        (
            "en-join-filler-after-so",
            re.compile(r"\.\s*(?:<break\s+time=\"[0-9.]+(?:ms|s)\"\s*/?>\s*)?So,\s+", re.IGNORECASE),
            ", so, ",
        ),
        (
            "en-join-it-bridge",
            re.compile(r"\.\s+It's\b"),
            ", and it's",
        ),
        (
            "en-join-that-bridge",
            re.compile(r"\.\s+That's\b"),
            ", and that's",
        ),
    ]


def german_patterns() -> list[tuple[str, re.Pattern[str], str | Callable[[re.Match[str]], str]]]:
    return [
        (
            "de-join-also-after-short-sentence",
            re.compile(r"\.\s*(?:<break\s+time=\"[0-9.]+(?:ms|s)\"\s*/?>\s*)?Also,\s+Geht's\b"),
            ", also geht's",
        ),
        (
            "de-join-also-generic",
            re.compile(r"\.\s*(?:<break\s+time=\"[0-9.]+(?:ms|s)\"\s*/?>\s*)?Also,\s+", re.IGNORECASE),
            ", also ",
        ),
        (
            "de-join-das-bridge",
            re.compile(r"\.\s+Das\b"),
            ", das",
        ),
    ]


def flow_join_text(text: str, *, language: str, profile: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    if not profile.get("enabled", True):
        return text, []
    patterns = german_patterns() if language == "de" else english_patterns()
    max_joins = int(profile.get("max_flow_joins_per_segment", 3))
    operations: list[dict[str, Any]] = []
    output = text
    for rule_id, pattern, replacement in patterns:
        if len(operations) >= max_joins:
            break
        output, operation = apply_rule_once(output, rule_id=rule_id, pattern=pattern, replacement=replacement)
        if operation is not None:
            operations.append(operation)
    return collapse_spaces(output), operations


def tune_segment(segment: dict[str, Any], *, language: str, profile: dict[str, Any]) -> dict[str, Any]:
    source_text = segment.get("rendered_text", "")
    protected = segment_is_protected(segment, profile)
    if protected:
        return {
            "segment_id": segment.get("segment_id"),
            "segment_type": segment.get("segment_type"),
            "protected": True,
            "protected_reason": segment.get("protected_reason") or "protected_segment_type",
            "source_text": source_text,
            "connected_text": source_text,
            "flow_join_count": 0,
            "flow_operations": [],
            "provider_hint": "Protected segment kept exact.",
        }
    connected_text, operations = flow_join_text(source_text, language=language, profile=profile)
    return {
        "segment_id": segment.get("segment_id"),
        "segment_type": segment.get("segment_type"),
        "protected": False,
        "protected_reason": None,
        "source_text": source_text,
        "connected_text": connected_text,
        "flow_join_count": len(operations),
        "flow_operations": operations,
        "provider_hint": "Sentence-boundary filler and short bridge phrases joined for provider-facing spoken flow.",
    }


def collect_provider_tags(text: str) -> list[str]:
    return [match.group(0) for match in PROVIDER_TAG_RE.finditer(text)]


def validate_connected_speech(
    *,
    source_rendering: dict[str, Any],
    connected_rendering: dict[str, Any],
    segment_plan: list[dict[str, Any]],
) -> dict[str, Any]:
    protected_segment_text_changes = [
        segment["segment_id"]
        for segment in segment_plan
        if segment["protected"] and segment["source_text"] != segment["connected_text"]
    ]
    markdown_in_rendered_text = "**" in connected_rendering.get("rendered_text", "")
    boundary_flags_changed = any(
        bool(source_rendering.get(flag)) != bool(connected_rendering.get(flag))
        for flag in [
            "api_call_made",
            "requires_api_key",
            "customer_audio_uploaded",
            "voice_cloning_used",
            "generated_audio_created",
        ]
    )
    passed = not protected_segment_text_changes and not markdown_in_rendered_text and not boundary_flags_changed
    return {
        "passed": passed,
        "protected_segment_text_changes": protected_segment_text_changes,
        "markdown_in_rendered_text": markdown_in_rendered_text,
        "boundary_flags_changed": boundary_flags_changed,
    }


def apply_voice_connected_speech(
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
    segment_plan = [
        tune_segment(segment, language=language, profile=profile)
        for segment in source.get("segment_renderings", [])
    ]

    connected_segments = []
    for source_segment, plan in zip(source.get("segment_renderings", []), segment_plan):
        connected_segment = deepcopy(source_segment)
        connected_segment["rendered_text"] = plan["connected_text"]
        connected_segment["provider_tags_inserted"] = collect_provider_tags(plan["connected_text"])
        connected_segment["voice_connected_speech"] = {
            "tuned": plan["flow_join_count"] > 0,
            "flow_join_count": plan["flow_join_count"],
            "flow_operations": plan["flow_operations"],
        }
        connected_segments.append(connected_segment)

    rendered_text = " ".join(
        segment["rendered_text"].strip()
        for segment in connected_segments
        if segment["rendered_text"].strip()
    )
    connected = deepcopy(source)
    connected["rendered_text"] = rendered_text
    connected["rendered_text_html_preview"] = html.escape(rendered_text)
    connected["segment_renderings"] = connected_segments
    connected["provider_tag_count"] = len(collect_provider_tags(rendered_text))
    connected["protected_segment_provider_tag_count"] = sum(
        len(segment.get("provider_tags_inserted", []))
        for segment in connected_segments
        if segment.get("protected_reason") is not None
    )
    connected["connected_speech_applied"] = any(plan["flow_join_count"] > 0 for plan in segment_plan)
    connected["voice_connected_speech_id"] = VOICE_CONNECTED_SPEECH_ID

    validation = validate_connected_speech(
        source_rendering=source,
        connected_rendering=connected,
        segment_plan=segment_plan,
    )
    flow_join_count = sum(int(plan["flow_join_count"]) for plan in segment_plan)
    return {
        "voice_milestone": "VOICE-035",
        "voice_connected_speech_id": VOICE_CONNECTED_SPEECH_ID,
        "enabled": bool(profile.get("enabled", True)),
        "language": language,
        "profile": profile,
        "source_provider_tag_count": int(source.get("provider_tag_count", 0)),
        "connected_provider_tag_count": int(connected.get("provider_tag_count", 0)),
        "flow_join_count": flow_join_count,
        "tuned_segment_count": sum(1 for plan in segment_plan if plan["flow_join_count"] > 0),
        "segment_plan": segment_plan,
        "connected_provider_rendering": connected,
        "validation": validation,
        "runtime_boundary": {
            "provider_calls_made": False,
            "requires_api_key": False,
            "customer_audio_uploaded": False,
            "voice_cloning_used": False,
            "generated_audio_created": False,
            "changes_allowed": "provider-facing connected-speech punctuation for eligible freeform TTS text only",
            "changes_forbidden": [
                "changing final_response",
                "changing protected campaign questions",
                "changing compliance, handoff, hangup, or do-not-call text",
                "adding product claims or promises",
            ],
        },
    }
