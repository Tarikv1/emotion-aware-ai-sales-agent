#!/usr/bin/env python3
from __future__ import annotations

import html
from copy import deepcopy
from typing import Any


VOICE_EMOTION_SMOOTHING_ID = "VOICE-037-emotion-transition-smoothing"

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
    "style": "emotion-transition-smoothing-v1",
    "protected_segment_types": sorted(PROTECTED_SEGMENT_TYPES),
    "max_transition_delta": 0.42,
    "min_stability_when_smoothed": 0.56,
    "max_stability_when_smoothed": 0.64,
    "max_style_when_smoothed": 0.18,
    "blocked_overemotional_intents": [
        "angry",
        "furious",
        "hostile",
        "abusive",
        "excited-high",
        "theatrical",
        "dramatic",
        "overexcited",
    ],
}

INTENT_VECTORS = {
    "neutral": {"arousal": 0.25, "valence": 0.5},
    "neutral-clear": {"arousal": 0.28, "valence": 0.5},
    "steady-neutral": {"arousal": 0.25, "valence": 0.5},
    "steady-low": {"arousal": 0.26, "valence": 0.42},
    "warm-soft": {"arousal": 0.32, "valence": 0.62},
    "warm-steady": {"arousal": 0.34, "valence": 0.62},
    "warm-slight-rise": {"arousal": 0.46, "valence": 0.64},
    "warm-reassuring": {"arousal": 0.34, "valence": 0.64},
    "slight-rise": {"arousal": 0.48, "valence": 0.58},
    "curious-efficient": {"arousal": 0.52, "valence": 0.58},
    "steady-confident": {"arousal": 0.62, "valence": 0.57},
    "confident-forward": {"arousal": 0.7, "valence": 0.58},
    "confident-low-pressure": {"arousal": 0.6, "valence": 0.58},
    "confident-practical": {"arousal": 0.58, "valence": 0.56},
    "positive": {"arousal": 0.55, "valence": 0.7},
    "skeptical-or-negative": {"arousal": 0.35, "valence": 0.24},
    "concerned": {"arousal": 0.4, "valence": 0.3},
}


def normalize_language(language: str | None) -> str:
    return "de" if str(language or "").lower().startswith("de") else "en"


def normalize_intent(intent: str | None) -> str:
    return str(intent or "").strip().lower().replace("_", "-")


def clamp_float(value: float, low: float, high: float, digits: int = 3) -> float:
    return round(min(high, max(low, value)), digits)


def profile_from_campaign(campaign: dict[str, Any]) -> dict[str, Any]:
    profile = deepcopy(DEFAULT_PROFILE)
    campaign_profile = campaign.get("voice_emotion_smoothing") or campaign.get("emotion_smoothing") or {}
    for key, value in campaign_profile.items():
        if isinstance(value, dict) and isinstance(profile.get(key), dict):
            merged = dict(profile[key])
            merged.update(value)
            profile[key] = merged
        else:
            profile[key] = value
    profile["style"] = "emotion-transition-smoothing-v1"
    return profile


def segment_is_protected(segment: dict[str, Any], profile: dict[str, Any]) -> bool:
    protected_types = set(profile.get("protected_segment_types", PROTECTED_SEGMENT_TYPES))
    return (
        segment.get("protected_reason") is not None
        or segment.get("segment_type") in protected_types
        or segment.get("eligible_for_prosody") is False
    )


def eligible_for_smoothing(provider_rendering: dict[str, Any], profile: dict[str, Any]) -> bool:
    if not profile.get("enabled", True):
        return False
    return any(
        not segment_is_protected(segment, profile)
        for segment in provider_rendering.get("segment_renderings", [])
    )


def vector_for_intent(intent: str) -> dict[str, float]:
    normalized = normalize_intent(intent)
    if normalized in INTENT_VECTORS:
        return deepcopy(INTENT_VECTORS[normalized])
    if "confident" in normalized or "forward" in normalized:
        return {"arousal": 0.62, "valence": 0.56}
    if "warm" in normalized or "reassuring" in normalized:
        return {"arousal": 0.34, "valence": 0.62}
    if "rise" in normalized or "curious" in normalized:
        return {"arousal": 0.5, "valence": 0.58}
    if "low" in normalized or "serious" in normalized:
        return {"arousal": 0.28, "valence": 0.4}
    if "positive" in normalized:
        return {"arousal": 0.55, "valence": 0.7}
    if "skeptical" in normalized or "negative" in normalized or "worried" in normalized:
        return {"arousal": 0.38, "valence": 0.28}
    return {"arousal": 0.3, "valence": 0.5}


def is_blocked_intent(intent: str, profile: dict[str, Any]) -> bool:
    normalized = normalize_intent(intent)
    return any(blocked in normalized for blocked in profile.get("blocked_overemotional_intents", []))


def build_signal(*, source: str, intent: str, signal_id: str, profile: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_intent(intent)
    vector = vector_for_intent(normalized)
    return {
        "signal_id": signal_id,
        "source": source,
        "intent": normalized,
        "arousal": vector["arousal"],
        "valence": vector["valence"],
        "blocked": is_blocked_intent(normalized, profile),
    }


def collect_emotion_signals(voice_context: dict[str, Any], profile: dict[str, Any]) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    decision = voice_context.get("decision_snapshot") or {}
    detected_emotion = decision.get("detected_emotion")
    if detected_emotion:
        signals.append(
            build_signal(
                source="decision_snapshot.detected_emotion",
                intent=str(detected_emotion),
                signal_id="decision-emotion",
                profile=profile,
            )
        )

    for index, marker in enumerate((voice_context.get("speech_interaction") or {}).get("interaction_markers", [])):
        intent = marker.get("pitch_intent")
        if intent:
            signals.append(
                build_signal(
                    source=f"speech_interaction.{marker.get('marker_type', 'marker')}",
                    intent=str(intent),
                    signal_id=str(marker.get("marker_id") or f"interaction-{index}"),
                    profile=profile,
                )
            )

    for index, cue in enumerate((voice_context.get("prosody") or {}).get("prosody_plan", [])):
        if cue.get("type") == "pitch":
            signals.append(
                build_signal(
                    source="prosody.pitch",
                    intent=str(cue.get("direction", "")),
                    signal_id=str(cue.get("cue_id") or f"pitch-{index}"),
                    profile=profile,
                )
            )

    return signals


def transition_delta(previous: dict[str, Any], current: dict[str, Any]) -> float:
    return round(
        abs(float(previous["arousal"]) - float(current["arousal"]))
        + abs(float(previous["valence"]) - float(current["valence"])),
        3,
    )


def smooth_vector(previous: dict[str, Any], current: dict[str, Any], max_delta: float) -> dict[str, float]:
    arousal_step = float(current["arousal"]) - float(previous["arousal"])
    valence_step = float(current["valence"]) - float(previous["valence"])
    total = abs(arousal_step) + abs(valence_step)
    if total <= max_delta or total <= 0:
        return {"arousal": float(current["arousal"]), "valence": float(current["valence"])}
    scale = max_delta / total
    return {
        "arousal": round(float(previous["arousal"]) + (arousal_step * scale), 3),
        "valence": round(float(previous["valence"]) + (valence_step * scale), 3),
    }


def build_transition_plan(signals: list[dict[str, Any]], profile: dict[str, Any]) -> dict[str, Any]:
    blocked_signals = [signal for signal in signals if signal["blocked"]]
    usable_signals = [signal for signal in signals if not signal["blocked"]]
    max_delta = float(profile.get("max_transition_delta", 0.42))
    transitions: list[dict[str, Any]] = []
    smoothed_signals: list[dict[str, Any]] = []

    for signal in usable_signals:
        if not smoothed_signals:
            smoothed_signals.append(deepcopy(signal))
            continue
        previous = smoothed_signals[-1]
        delta = transition_delta(previous, signal)
        smoothed_vector = smooth_vector(previous, signal, max_delta)
        smoothed = deepcopy(signal)
        smoothed["arousal"] = smoothed_vector["arousal"]
        smoothed["valence"] = smoothed_vector["valence"]
        smoothed["smoothed"] = delta > max_delta
        smoothed_signals.append(smoothed)
        if delta > max_delta:
            transitions.append(
                {
                    "from_signal_id": previous["signal_id"],
                    "to_signal_id": signal["signal_id"],
                    "from_intent": previous["intent"],
                    "to_intent": signal["intent"],
                    "transition_delta": delta,
                    "max_allowed_delta": max_delta,
                    "smoothed_arousal": smoothed_vector["arousal"],
                    "smoothed_valence": smoothed_vector["valence"],
                    "reason": "bounded_emotional_inertia",
                }
            )

    return {
        "source_signals": signals,
        "usable_signal_count": len(usable_signals),
        "blocked_overemotional_signals": blocked_signals,
        "smoothed_signals": smoothed_signals,
        "transitions": transitions,
    }


def smoothed_voice_settings(settings: dict[str, Any], profile: dict[str, Any], *, smoothing_needed: bool) -> dict[str, Any]:
    voice_settings = deepcopy(settings)
    if not smoothing_needed:
        return voice_settings
    current_stability = float(voice_settings.get("stability", 0.45))
    current_style = float(voice_settings.get("style", 0.0))
    min_stability = float(profile.get("min_stability_when_smoothed", 0.56))
    max_stability = float(profile.get("max_stability_when_smoothed", 0.64))
    max_style = float(profile.get("max_style_when_smoothed", 0.18))
    voice_settings["stability"] = clamp_float(max(current_stability, min_stability), 0.0, max_stability)
    voice_settings["style"] = clamp_float(min(current_style, max_style), 0.0, 1.0)
    return voice_settings


def validate_smoothing(
    *,
    source_rendering: dict[str, Any],
    smoothed_rendering: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:
    protected_segment_text_changes = []
    for source_segment, smoothed_segment in zip(
        source_rendering.get("segment_renderings", []),
        smoothed_rendering.get("segment_renderings", []),
    ):
        if segment_is_protected(source_segment, profile) and source_segment.get("rendered_text") != smoothed_segment.get("rendered_text"):
            protected_segment_text_changes.append(source_segment.get("segment_id"))

    rendered_text_changed = source_rendering.get("rendered_text", "") != smoothed_rendering.get("rendered_text", "")
    boundary_flags_changed = any(
        bool(source_rendering.get(flag)) != bool(smoothed_rendering.get(flag))
        for flag in [
            "api_call_made",
            "requires_api_key",
            "customer_audio_uploaded",
            "voice_cloning_used",
            "generated_audio_created",
        ]
    )
    source_settings = source_rendering.get("voice_settings") or {}
    smoothed_settings = smoothed_rendering.get("voice_settings") or {}
    speed_changed = source_settings.get("speed") != smoothed_settings.get("speed")
    style_out_of_bounds = float(smoothed_settings.get("style", 0.0)) > float(profile.get("max_style_when_smoothed", 0.18))
    stability_out_of_bounds = not (0.0 <= float(smoothed_settings.get("stability", 0.45)) <= 1.0)
    passed = not (
        protected_segment_text_changes
        or rendered_text_changed
        or boundary_flags_changed
        or speed_changed
        or style_out_of_bounds
        or stability_out_of_bounds
    )
    return {
        "passed": passed,
        "protected_segment_text_changes": protected_segment_text_changes,
        "rendered_text_changed": rendered_text_changed,
        "boundary_flags_changed": boundary_flags_changed,
        "speed_changed": speed_changed,
        "style_out_of_bounds": style_out_of_bounds,
        "stability_out_of_bounds": stability_out_of_bounds,
    }


def apply_voice_emotion_smoothing(
    campaign: dict[str, Any],
    provider_rendering: dict[str, Any],
    *,
    voice_context: dict[str, Any] | None = None,
    language: str,
    seed: str = "",
) -> dict[str, Any]:
    del seed
    normalized_language = normalize_language(language)
    profile = profile_from_campaign(campaign)
    source = deepcopy(provider_rendering)
    context = voice_context or {}
    eligible = eligible_for_smoothing(source, profile)
    transition_plan = build_transition_plan(collect_emotion_signals(context, profile), profile)
    smoothing_needed = eligible and (
        bool(transition_plan["transitions"]) or bool(transition_plan["blocked_overemotional_signals"])
    )

    smoothed = deepcopy(source)
    smoothed["voice_settings"] = smoothed_voice_settings(
        source.get("voice_settings") or {},
        profile,
        smoothing_needed=smoothing_needed,
    )
    for segment in smoothed.get("segment_renderings", []):
        segment["voice_emotion_smoothing"] = {
            "tuned": smoothing_needed and not segment_is_protected(segment, profile),
            "transition_count": len(transition_plan["transitions"]),
            "blocked_overemotional_cue_count": len(transition_plan["blocked_overemotional_signals"]),
        }
    smoothed["rendered_text_html_preview"] = html.escape(str(smoothed.get("rendered_text", "")))
    smoothed["emotion_transition_smoothing_applied"] = smoothing_needed
    smoothed["voice_emotion_smoothing_id"] = VOICE_EMOTION_SMOOTHING_ID

    validation = validate_smoothing(
        source_rendering=source,
        smoothed_rendering=smoothed,
        profile=profile,
    )
    return {
        "voice_milestone": "VOICE-037",
        "voice_emotion_smoothing_id": VOICE_EMOTION_SMOOTHING_ID,
        "enabled": bool(profile.get("enabled", True)),
        "language": normalized_language,
        "profile": profile,
        "eligible_for_smoothing": eligible,
        "transition_smoothing_applied": smoothing_needed,
        "detected_transition_count": len(transition_plan["transitions"]),
        "smoothed_transition_count": len(transition_plan["transitions"]) if smoothing_needed else 0,
        "blocked_overemotional_cue_count": len(transition_plan["blocked_overemotional_signals"]),
        "source_voice_settings": source.get("voice_settings") or {},
        "smoothed_voice_settings": smoothed.get("voice_settings") or {},
        "source_rendered_text": source.get("rendered_text", ""),
        "transition_plan": transition_plan,
        "smoothed_provider_rendering": smoothed,
        "validation": validation,
        "runtime_boundary": {
            "provider_calls_made": False,
            "requires_api_key": False,
            "customer_audio_uploaded": False,
            "voice_cloning_used": False,
            "generated_audio_created": False,
            "changes_allowed": "provider-facing voice stability/style smoothing only; wording, speed, call policy, and protected text stay exact",
            "changes_forbidden": [
                "changing final_response",
                "changing rendered text",
                "changing protected campaign or compliance text",
                "adding claims",
                "uploading customer audio",
                "voice cloning",
            ],
        },
    }
