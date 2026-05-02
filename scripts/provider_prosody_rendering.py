#!/usr/bin/env python3
from __future__ import annotations

import html
import re
from copy import deepcopy
from typing import Any


PROVIDER_RENDERING_ID = "VOICE-016-provider-prosody-rendering"

CARTESIA_TAG_CUES = {"pause", "rate", "emphasis", "stretch"}
ELEVENLABS_MAPPED_CUES = {"pause", "rate", "stretch"}


def replace_first(text: str, target: str, replacement: str) -> tuple[str, bool]:
    if not target:
        return text, False
    pattern = re.compile(re.escape(target), re.IGNORECASE)
    if pattern.search(text) is None:
        return text, False
    return pattern.sub(replacement, text, count=1), True


def insert_after(text: str, target: str, insertion: str) -> tuple[str, bool]:
    if not target:
        return text, False
    pattern = re.compile(re.escape(target), re.IGNORECASE)
    match = pattern.search(text)
    if match is None:
        return text, False
    return text[: match.end()] + insertion + text[match.end() :], True


def seconds_text(ms: int) -> str:
    return f"{ms / 1000:.3f}".rstrip("0").rstrip(".")


def collect_same_target_pause(cues: list[dict[str, Any]], target: str) -> dict[str, Any] | None:
    for cue in cues:
        if cue["type"] == "pause" and cue.get("after", "").lower() == target.lower():
            return cue
    return None


def render_cartesia_segment(segment: dict[str, Any]) -> dict[str, Any]:
    text = segment["tts_text"]
    cues = deepcopy(segment.get("cues", []))
    mapped = []
    unsupported = []
    provider_tags_inserted = []
    stretch_targets_merged_with_pause = set()

    for cue in cues:
        if cue["type"] == "pitch":
            unsupported.append({**cue, "reason": "cartesia_direct_pitch_tag_not_used"})
            continue

        if cue["type"] == "stretch":
            same_target_pause = collect_same_target_pause(cues, cue["target"])
            if same_target_pause is not None:
                stretch_targets_merged_with_pause.add(cue["target"].lower())
                mapped.append({**cue, "rendered_as": "merged_with_pause_break"})
                continue
            tag = f"<break time=\"{int(cue['hold_ms'])}ms\"/>"
            text, changed = insert_after(text, cue["target"], tag)
            if changed:
                mapped.append({**cue, "rendered_as": "break"})
                provider_tags_inserted.append(tag)
            continue

        if cue["type"] == "pause":
            duration = int(cue["duration_ms"])
            if cue.get("after", "").lower() in stretch_targets_merged_with_pause:
                stretch = next(
                    (item for item in cues if item["type"] == "stretch" and item["target"].lower() == cue["after"].lower()),
                    None,
                )
                if stretch is not None:
                    duration = max(duration, int(stretch["hold_ms"]))
            tag = f"<break time=\"{duration}ms\"/>"
            text, changed = insert_after(text, cue["after"], tag)
            if changed:
                mapped.append({**cue, "rendered_as": "break", "rendered_duration_ms": duration})
                provider_tags_inserted.append(tag)
            continue

        if cue["type"] == "rate":
            tag_open = f"<speed ratio=\"{float(cue['ratio']):.3f}\"/>"
            tag_close = "<speed ratio=\"1.000\"/>"
            text, changed = replace_first(text, cue["target"], f"{tag_open}{cue['target']}{tag_close}")
            if changed:
                mapped.append({**cue, "rendered_as": "speed_tag"})
                provider_tags_inserted.extend([tag_open, tag_close])
            continue

        if cue["type"] == "emphasis":
            tag_open = "<volume ratio=\"1.080\"/>"
            tag_close = "<volume ratio=\"1.000\"/>"
            text, changed = replace_first(text, cue["target"], f"{tag_open}{cue['target']}{tag_close}")
            if changed:
                mapped.append({**cue, "rendered_as": "volume_tag"})
                provider_tags_inserted.extend([tag_open, tag_close])
            continue

    return {
        "segment_id": segment["segment_id"],
        "segment_type": segment["segment_type"],
        "protected_reason": segment["protected_reason"],
        "eligible_for_prosody": segment["eligible_for_prosody"],
        "plain_text": segment["tts_text"],
        "rendered_text": text,
        "provider_tags_inserted": provider_tags_inserted,
        "mapped_cues": mapped,
        "unsupported_cues": unsupported,
    }


def elevenlabs_speed_from_rate_cues(cues: list[dict[str, Any]]) -> float:
    ratios = [float(cue["ratio"]) for cue in cues if cue["type"] == "rate"]
    if not ratios:
        return 1.0
    average = sum(ratios) / len(ratios)
    return round(min(1.08, max(0.9, average)), 3)


def render_elevenlabs_segment(segment: dict[str, Any]) -> dict[str, Any]:
    text = segment["tts_text"]
    cues = deepcopy(segment.get("cues", []))
    mapped = []
    unsupported = []
    provider_tags_inserted = []
    pause_targets = {cue.get("after", "").lower() for cue in cues if cue["type"] == "pause"}

    for cue in cues:
        if cue["type"] == "pause":
            tag = f"<break time=\"{seconds_text(int(cue['duration_ms']))}s\" />"
            text, changed = insert_after(text, cue["after"], f" {tag}")
            if changed:
                mapped.append({**cue, "rendered_as": "break_tag"})
                provider_tags_inserted.append(tag)
            continue

        if cue["type"] == "rate":
            mapped.append({**cue, "rendered_as": "request_voice_settings_speed"})
            continue

        if cue["type"] == "stretch":
            if cue["target"].lower() in pause_targets:
                mapped.append({**cue, "rendered_as": "covered_by_break_tag"})
                continue
            text, changed = replace_first(text, cue["target"], cue["variant"])
            if changed:
                mapped.append({**cue, "rendered_as": "ellipsis_variant"})
            continue

        unsupported.append({**cue, "reason": f"elevenlabs_{cue['type']}_direct_mapping_not_used"})

    return {
        "segment_id": segment["segment_id"],
        "segment_type": segment["segment_type"],
        "protected_reason": segment["protected_reason"],
        "eligible_for_prosody": segment["eligible_for_prosody"],
        "plain_text": segment["tts_text"],
        "rendered_text": text,
        "provider_tags_inserted": provider_tags_inserted,
        "mapped_cues": mapped,
        "unsupported_cues": unsupported,
    }


def cue_counts(cues: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"emphasis": 0, "pause": 0, "pitch": 0, "rate": 0, "stretch": 0}
    for cue in cues:
        counts[cue["type"]] = counts.get(cue["type"], 0) + 1
    return counts


def render_provider_variant(
    result: dict[str, Any],
    provider: dict[str, Any],
) -> dict[str, Any]:
    packet = result["prosody_naturalness"]
    provider_key = provider["provider_key"]
    if provider_key == "cartesia":
        segment_renderings = [render_cartesia_segment(segment) for segment in packet["output_segments"]]
        voice_settings = None
    elif provider_key == "elevenlabs":
        segment_renderings = [render_elevenlabs_segment(segment) for segment in packet["output_segments"]]
        voice_settings = dict(provider.get("base_voice_settings", {}))
        voice_settings["speed"] = elevenlabs_speed_from_rate_cues(packet["prosody_plan"])
    else:
        raise ValueError(f"Unknown provider key: {provider_key}")

    rendered_text = " ".join(segment["rendered_text"].strip() for segment in segment_renderings if segment["rendered_text"].strip())
    mapped_cues = [cue for segment in segment_renderings for cue in segment["mapped_cues"]]
    unsupported_cues = [cue for segment in segment_renderings for cue in segment["unsupported_cues"]]
    provider_tags = [tag for segment in segment_renderings for tag in segment["provider_tags_inserted"]]
    mapped_counts = cue_counts(mapped_cues)
    unsupported_counts = cue_counts(unsupported_cues)
    protected_tag_count = sum(
        len(segment["provider_tags_inserted"])
        for segment in segment_renderings
        if segment["protected_reason"] is not None
    )

    return {
        "provider_rendering_id": PROVIDER_RENDERING_ID,
        "provider_key": provider_key,
        "provider_name": provider["provider_name"],
        "provider_rendering_mode": provider["provider_rendering_mode"],
        "model_id": provider["model_id"],
        "language": result["language"],
        "case_id": result["case_id"],
        "plain_text": packet["tts_text"],
        "rendered_text": rendered_text,
        "rendered_text_html_preview": html.escape(rendered_text),
        "voice_settings": voice_settings or {},
        "segment_renderings": segment_renderings,
        "mapped_cues": mapped_cues,
        "unsupported_cues": unsupported_cues,
        "mapped_cue_counts": mapped_counts,
        "unsupported_cue_counts": unsupported_counts,
        "provider_tag_count": len(provider_tags),
        "protected_segment_provider_tag_count": protected_tag_count,
        "api_call_made": False,
        "requires_api_key": False,
        "customer_audio_uploaded": False,
        "voice_cloning_used": False,
        "generated_audio_created": False,
        "runtime_boundary": "offline rendering preview only; live audio belongs to explicit opt-in provider checkpoints such as VOICE-017 or RESP-003",
    }


def validate_variant(variant: dict[str, Any]) -> dict[str, Any]:
    markdown_in_rendered_text = "**" in variant["rendered_text"]
    protected_segment_tags = [
        segment["segment_id"]
        for segment in variant["segment_renderings"]
        if segment["protected_reason"] is not None and segment["provider_tags_inserted"]
    ]
    protected_segment_changes = [
        segment["segment_id"]
        for segment in variant["segment_renderings"]
        if segment["protected_reason"] is not None and segment["rendered_text"] != segment["plain_text"]
    ]
    passed = not markdown_in_rendered_text and not protected_segment_tags and not protected_segment_changes
    return {
        "passed": passed,
        "markdown_in_rendered_text": markdown_in_rendered_text,
        "protected_segment_tags": protected_segment_tags,
        "protected_segment_changes": protected_segment_changes,
    }


def render_case(result: dict[str, Any], providers: list[dict[str, Any]]) -> dict[str, Any]:
    variants = [render_provider_variant(result, provider) for provider in providers]
    validations = {variant["provider_key"]: validate_variant(variant) for variant in variants}
    return {
        "case_id": result["case_id"],
        "case_title": result["case_title"],
        "campaign_id": result["campaign_id"],
        "language": result["language"],
        "prosody_cue_count": result["prosody_naturalness"]["cue_count"],
        "prosody_cue_counts": result["prosody_naturalness"]["cue_counts"],
        "plain_text": result["prosody_naturalness"]["tts_text"],
        "debug_text": result["prosody_naturalness"]["debug_text"],
        "provider_variants": variants,
        "validation": {
            "passed": all(validation["passed"] for validation in validations.values()),
            "provider_validations": validations,
        },
    }
