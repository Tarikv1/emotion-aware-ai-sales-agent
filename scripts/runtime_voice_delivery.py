#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
from typing import Any

from prosody_naturalness import apply_prosody_naturalness
from provider_prosody_rendering import render_provider_variant, validate_variant
from speech_imperfections import apply_speech_imperfections
from speech_interaction import apply_speech_interaction
from speech_realism import apply_speech_realism
from spoken_text_normalization import apply_spoken_text_normalization
from voice_connected_speech import apply_voice_connected_speech
from voice_emotion_smoothing import apply_voice_emotion_smoothing
from voice_listening_calibration import apply_emphasis_target_guard, apply_voice_listening_calibration
from voice_low_pressure_focus import apply_voice_low_pressure_focus
from voice_pacing_calibration import apply_voice_pacing_calibration
from voice_semantic_emphasis import apply_voice_semantic_emphasis


RUNTIME_VOICE_DELIVERY_ID = "RESP-002-runtime-voice-delivery"

PROVIDERS = {
    "elevenlabs": {
        "provider_key": "elevenlabs",
        "provider_name": "ElevenLabs Flash v2.5",
        "provider_rendering_mode": "break_tags_and_request_settings",
        "model_id": "eleven_flash_v2_5",
        "supported_cues": ["pause", "rate", "stretch"],
        "unsupported_cues": ["pitch", "emphasis"],
        "base_voice_settings": {
            "stability": 0.45,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True,
            "speed": 1.0,
        },
    },
    "cartesia": {
        "provider_key": "cartesia",
        "provider_name": "Cartesia Sonic 3",
        "provider_rendering_mode": "ssml_like",
        "model_id": "sonic-3",
        "supported_cues": ["pause", "rate", "emphasis", "stretch"],
        "unsupported_cues": ["pitch"],
    },
}

PROTECTED_DIFFICULTIES = {
    "claim-boundary": "claim_boundary",
    "do-not-call": "do_not_call",
    "human-request": "human_handoff_exact_script",
    "scheduling-confirmation": "appointment_confirmation",
    "repeated-silence": "hangup",
}

FREEFORM_DIFFICULTIES = {
    "price-objection": "freeform_objection_handling",
    "product-detail-lookup": "freeform_bridge",
    "timing-delay": "freeform_empathy",
    "voicemail": "freeform_explanation",
}


def response_language(packet: dict[str, Any], campaign: dict[str, Any]) -> str:
    decision = packet.get("decision_snapshot", {})
    language = decision.get("response_language") or campaign.get("language") or "en"
    return "de" if str(language).lower().startswith("de") else "en"


def segment_type_for_packet(packet: dict[str, Any]) -> tuple[str, str, bool]:
    decision = packet.get("decision_snapshot", {})
    difficulty = decision.get("sales_difficulty")
    interest_state = decision.get("interest_state")
    next_action = decision.get("next_action")
    call_control = decision.get("call_control")

    if difficulty in PROTECTED_DIFFICULTIES:
        segment_type = PROTECTED_DIFFICULTIES[difficulty]
        return segment_type, "policy_or_compliance_boundary", False
    if interest_state == "do-not-call" or next_action == "suppress-contact":
        return "do_not_call", "policy_or_compliance_boundary", False
    if call_control == "schedule-and-end":
        return "appointment_confirmation", "policy_or_compliance_boundary", False
    if interest_state == "needs-human" or call_control == "transfer-or-escalate":
        return "human_handoff_exact_script", "policy_or_compliance_boundary", False
    if call_control == "end-call":
        return "hangup", "policy_or_compliance_boundary", False
    if difficulty in FREEFORM_DIFFICULTIES:
        return FREEFORM_DIFFICULTIES[difficulty], "runtime_guarded_response", True
    if next_action == "ask-follow-up":
        return "freeform_clarification", "runtime_guarded_response", True
    return "freeform_explanation", "runtime_guarded_response", True


def build_delivery_segments(packet: dict[str, Any], campaign: dict[str, Any]) -> list[dict[str, Any]]:
    segment_type, source, allow_prosody = segment_type_for_packet(packet)
    final_response = packet["final_response"]
    return [
        {
            "segment_id": "resp-002-final-response",
            "segment_type": segment_type,
            "source": source,
            "text": final_response,
            "allow_fillers": allow_prosody,
            "allow_interaction_prosody": allow_prosody,
            "allow_speech_imperfections": allow_prosody,
            "allow_prosody": allow_prosody,
            "eligible_for_prosody": allow_prosody,
            "decision_source": {
                "sales_difficulty": packet.get("decision_snapshot", {}).get("sales_difficulty"),
                "interest_state": packet.get("decision_snapshot", {}).get("interest_state"),
                "next_action": packet.get("decision_snapshot", {}).get("next_action"),
                "call_control": packet.get("decision_snapshot", {}).get("call_control"),
            },
        }
    ]


def provider_for_key(provider_key: str) -> dict[str, Any]:
    if provider_key not in PROVIDERS:
        known = ", ".join(sorted(PROVIDERS))
        raise ValueError(f"Unknown provider {provider_key!r}. Known providers: {known}")
    return deepcopy(PROVIDERS[provider_key])


def build_provider_result_shape(
    packet: dict[str, Any],
    campaign: dict[str, Any],
    prosody: dict[str, Any],
    language: str,
) -> dict[str, Any]:
    return {
        "case_id": "RESP-002-runtime-turn",
        "case_title": "Runtime guarded response voice delivery",
        "campaign_id": campaign.get("campaign_id"),
        "language": language,
        "prosody_naturalness": prosody,
        "source_response_generation_id": packet.get("response_generation_id"),
    }


def build_spoken_segments(
    segments: list[dict[str, Any]],
    spoken_text_normalization: dict[str, Any],
) -> list[dict[str, Any]]:
    spoken_segments = []
    output_by_id = {
        segment.get("segment_id"): segment
        for segment in spoken_text_normalization.get("output_segments", [])
    }
    for segment in segments:
        spoken_segment = deepcopy(segment)
        output_segment = output_by_id.get(segment.get("segment_id"))
        if output_segment is not None:
            spoken_segment["text"] = output_segment["text_after"]
            spoken_segment["spoken_text_before"] = output_segment["text_before"]
            spoken_segment["spoken_text_after"] = output_segment["text_after"]
            spoken_segment["spoken_normalizations"] = output_segment["normalizations"]
            spoken_segment["eligible_for_spoken_normalization"] = output_segment[
                "eligible_for_spoken_normalization"
            ]
            spoken_segment["spoken_protected_reason"] = output_segment["protected_reason"]
        spoken_segments.append(spoken_segment)
    return spoken_segments


def build_realistic_segments(
    segments: list[dict[str, Any]],
    speech_realism: dict[str, Any],
) -> list[dict[str, Any]]:
    realistic_segments = []
    output_by_id = {
        segment.get("segment_id"): segment
        for segment in speech_realism.get("output_segments", [])
    }
    for segment in segments:
        realistic_segment = deepcopy(segment)
        output_segment = output_by_id.get(segment.get("segment_id"))
        if output_segment is not None:
            realistic_segment["text"] = output_segment["text_after"]
            realistic_segment["speech_realism_text_before"] = output_segment["text_before"]
            realistic_segment["speech_realism_text_after"] = output_segment["text_after"]
            realistic_segment["speech_realism_bundles"] = output_segment["bundles"]
            realistic_segment["eligible_for_speech_realism"] = output_segment[
                "eligible_for_speech_realism"
            ]
            realistic_segment["speech_realism_protected_reason"] = output_segment["protected_reason"]
        realistic_segments.append(realistic_segment)
    return realistic_segments


def build_interaction_segments(
    segments: list[dict[str, Any]],
    speech_interaction: dict[str, Any],
) -> list[dict[str, Any]]:
    interaction_segments = []
    output_by_id = {
        segment.get("segment_id"): segment
        for segment in speech_interaction.get("output_segments", [])
    }
    for segment in segments:
        interaction_segment = deepcopy(segment)
        output_segment = output_by_id.get(segment.get("segment_id"))
        if output_segment is not None:
            interaction_segment["text"] = output_segment["text_after"]
            interaction_segment["speech_interaction_text_before"] = output_segment["text_before"]
            interaction_segment["speech_interaction_text_after"] = output_segment["text_after"]
            interaction_segment["speech_interaction_markers"] = output_segment["markers"]
            interaction_segment["eligible_for_speech_interaction"] = output_segment["eligible"]
            interaction_segment["speech_interaction_protected_reason"] = output_segment["protection_reason"]
        interaction_segments.append(interaction_segment)
    return interaction_segments


def build_imperfect_segments(
    segments: list[dict[str, Any]],
    speech_imperfections: dict[str, Any],
) -> list[dict[str, Any]]:
    imperfect_segments = []
    output_by_id = {
        segment.get("segment_id"): segment
        for segment in speech_imperfections.get("output_segments", [])
    }
    for segment in segments:
        imperfect_segment = deepcopy(segment)
        output_segment = output_by_id.get(segment.get("segment_id"))
        if output_segment is not None:
            imperfect_segment["text"] = output_segment["text_after"]
            imperfect_segment["speech_imperfections_text_before"] = output_segment["text_before"]
            imperfect_segment["speech_imperfections_text_after"] = output_segment["text_after"]
            imperfect_segment["speech_imperfections"] = output_segment["imperfections"]
            imperfect_segment["eligible_for_speech_imperfections"] = output_segment["eligible"]
            imperfect_segment["speech_imperfections_protected_reason"] = output_segment["protection_reason"]
        imperfect_segments.append(imperfect_segment)
    return imperfect_segments


def validate_delivery(
    packet: dict[str, Any],
    segments: list[dict[str, Any]],
    spoken_text_normalization: dict[str, Any],
    speech_realism: dict[str, Any],
    speech_interaction: dict[str, Any],
    speech_imperfections: dict[str, Any],
    prosody: dict[str, Any],
    provider_rendering: dict[str, Any],
    voice_pacing_calibration: dict[str, Any],
    voice_connected_speech: dict[str, Any],
    voice_listening_calibration: dict[str, Any],
    voice_emotion_smoothing: dict[str, Any],
    voice_semantic_emphasis: dict[str, Any],
    voice_low_pressure_focus: dict[str, Any],
) -> dict[str, Any]:
    final_response = packet["final_response"]
    final_response_unchanged = segments[0].get("text") == final_response
    tts_text_equals_final_response = prosody["tts_text"] == final_response
    protected_segment_ids = {
        segment["segment_id"]
        for segment in segments
        if segment["segment_type"]
        in {
            "claim_boundary",
            "do_not_call",
            "human_handoff_exact_script",
            "appointment_confirmation",
            "hangup",
            "required_disclosure",
            "campaign_qualification_question",
            "company_script",
        }
    }
    cue_in_protected_segment_count = sum(
        1 for cue in prosody["prosody_plan"] if cue.get("segment_id") in protected_segment_ids
    )
    provider_validation = validate_variant(provider_rendering)
    protected_segment_change_count = len(
        spoken_text_normalization["validation"].get("protected_segment_changes", [])
    )
    speech_realism_protected_segment_change_count = len(
        speech_realism["validation"].get("protected_segment_changes", [])
    )
    speech_interaction_protected_segment_change_count = len(
        speech_interaction["validation"].get("protected_segment_changes", [])
    )
    speech_interaction_protected_marker_count = len(
        speech_interaction["validation"].get("protected_marker_violations", [])
    )
    speech_imperfections_protected_segment_change_count = len(
        speech_imperfections["validation"].get("protected_segment_changes", [])
    )
    speech_imperfections_protected_violation_count = len(
        speech_imperfections["validation"].get("protected_imperfection_violations", [])
    )
    speech_imperfections_unsafe_visible_count = len(
        speech_imperfections["validation"].get("unsafe_visible_imperfections", [])
    )
    voice_pacing_calibration_passed = voice_pacing_calibration["validation"]["passed"]
    voice_connected_speech_passed = voice_connected_speech["validation"]["passed"]
    voice_listening_calibration_passed = voice_listening_calibration["validation"]["passed"]
    voice_emotion_smoothing_passed = voice_emotion_smoothing["validation"]["passed"]
    voice_semantic_emphasis_passed = voice_semantic_emphasis["validation"]["passed"]
    voice_low_pressure_focus_passed = voice_low_pressure_focus["validation"]["passed"]
    passed = (
        final_response_unchanged
        and spoken_text_normalization["validation"]["passed"]
        and speech_realism["validation"]["passed"]
        and speech_interaction["validation"]["passed"]
        and speech_imperfections["validation"]["passed"]
        and voice_pacing_calibration_passed
        and voice_connected_speech_passed
        and voice_listening_calibration_passed
        and voice_emotion_smoothing_passed
        and voice_semantic_emphasis_passed
        and voice_low_pressure_focus_passed
        and prosody["validation"]["passed"]
        and provider_validation["passed"]
        and protected_segment_change_count == 0
        and speech_realism_protected_segment_change_count == 0
        and speech_interaction_protected_segment_change_count == 0
        and speech_interaction_protected_marker_count == 0
        and speech_imperfections_protected_segment_change_count == 0
        and speech_imperfections_protected_violation_count == 0
        and speech_imperfections_unsafe_visible_count == 0
        and cue_in_protected_segment_count == 0
        and provider_rendering["api_call_made"] is False
        and provider_rendering["customer_audio_uploaded"] is False
        and provider_rendering["voice_cloning_used"] is False
    )
    return {
        "validator": "RESP-002 guarded response voice delivery check",
        "passed": passed,
        "final_response_unchanged": final_response_unchanged,
        "tts_text_equals_final_response": tts_text_equals_final_response,
        "spoken_text_normalization_passed": spoken_text_normalization["validation"]["passed"],
        "speech_realism_passed": speech_realism["validation"]["passed"],
        "speech_interaction_passed": speech_interaction["validation"]["passed"],
        "speech_imperfections_passed": speech_imperfections["validation"]["passed"],
        "voice_pacing_calibration_passed": voice_pacing_calibration_passed,
        "voice_connected_speech_passed": voice_connected_speech_passed,
        "voice_listening_calibration_passed": voice_listening_calibration_passed,
        "voice_emotion_smoothing_passed": voice_emotion_smoothing_passed,
        "voice_semantic_emphasis_passed": voice_semantic_emphasis_passed,
        "voice_low_pressure_focus_passed": voice_low_pressure_focus_passed,
        "prosody_validation_passed": prosody["validation"]["passed"],
        "provider_validation": provider_validation,
        "protected_segment_change_count": protected_segment_change_count,
        "speech_realism_protected_segment_change_count": speech_realism_protected_segment_change_count,
        "speech_interaction_protected_segment_change_count": speech_interaction_protected_segment_change_count,
        "speech_interaction_protected_marker_count": speech_interaction_protected_marker_count,
        "speech_imperfections_protected_segment_change_count": speech_imperfections_protected_segment_change_count,
        "speech_imperfections_protected_violation_count": speech_imperfections_protected_violation_count,
        "speech_imperfections_unsafe_visible_count": speech_imperfections_unsafe_visible_count,
        "voice_pacing_tuned_segment_count": voice_pacing_calibration["tuned_segment_count"],
        "voice_connected_speech_flow_join_count": voice_connected_speech["flow_join_count"],
        "voice_listening_adjustment_count": voice_listening_calibration["listening_adjustment_count"],
        "voice_emotion_transition_smoothed_count": voice_emotion_smoothing["smoothed_transition_count"],
        "voice_semantic_emphasis_rewrite_count": voice_semantic_emphasis["rewrite_count"],
        "voice_low_pressure_focus_rewrite_count": voice_low_pressure_focus["rewrite_count"],
        "cue_in_protected_segment_count": cue_in_protected_segment_count,
        "notes": (
            "Runtime voice delivery preserved guarded text and kept provider rendering offline."
            if passed
            else "Runtime voice delivery failed a guarded-text, prosody, or provider-rendering check."
        ),
    }


def build_runtime_voice_delivery(
    guarded_packet: dict[str, Any],
    campaign: dict[str, Any],
    provider_key: str = "elevenlabs",
    seed: str | None = None,
) -> dict[str, Any]:
    language = response_language(guarded_packet, campaign)
    segments = build_delivery_segments(guarded_packet, campaign)
    provider = provider_for_key(provider_key)
    seed_value = seed or f"{guarded_packet.get('response_generation_id')}:{campaign.get('campaign_id')}:{guarded_packet.get('stage')}:{guarded_packet.get('transcript')}"
    spoken_text_normalization = apply_spoken_text_normalization(
        campaign,
        segments,
        language=language,
        seed=seed_value,
    )
    spoken_segments = build_spoken_segments(segments, spoken_text_normalization)
    customer_state = guarded_packet.get("customer_state") or guarded_packet.get("turn_state") or {}
    speech_realism = apply_speech_realism(
        campaign,
        spoken_segments,
        language=language,
        seed=seed_value,
        customer_state=customer_state,
    )
    realistic_segments = build_realistic_segments(spoken_segments, speech_realism)
    speech_interaction = apply_speech_interaction(
        campaign=campaign,
        segments=realistic_segments,
        language=language,
        seed=seed_value,
        customer_state=customer_state,
    )
    interaction_segments = build_interaction_segments(realistic_segments, speech_interaction)
    speech_imperfections = apply_speech_imperfections(
        campaign=campaign,
        segments=interaction_segments,
        language=language,
        seed=seed_value,
        customer_state=customer_state,
    )
    imperfect_segments = build_imperfect_segments(interaction_segments, speech_imperfections)
    prosody = apply_prosody_naturalness(campaign, imperfect_segments, language=language, seed=seed_value)
    emphasis_guard = apply_emphasis_target_guard(campaign, prosody, language=language)
    prosody = emphasis_guard["guarded_prosody"]
    provider_result = build_provider_result_shape(guarded_packet, campaign, prosody, language)
    provider_rendering = render_provider_variant(provider_result, provider)
    voice_pacing_calibration = apply_voice_pacing_calibration(
        campaign,
        provider_rendering,
        language=language,
        seed=seed_value,
    )
    provider_rendering = voice_pacing_calibration["calibrated_provider_rendering"]
    voice_connected_speech = apply_voice_connected_speech(
        campaign,
        provider_rendering,
        language=language,
        seed=seed_value,
    )
    provider_rendering = voice_connected_speech["connected_provider_rendering"]
    voice_listening_calibration = apply_voice_listening_calibration(
        campaign,
        provider_rendering,
        emphasis_guard,
        language=language,
        seed=seed_value,
    )
    provider_rendering = voice_listening_calibration["calibrated_provider_rendering"]
    voice_emotion_smoothing = apply_voice_emotion_smoothing(
        campaign,
        provider_rendering,
        voice_context={
            "decision_snapshot": guarded_packet.get("decision_snapshot", {}),
            "speech_interaction": speech_interaction,
            "speech_imperfections": speech_imperfections,
            "prosody": prosody,
        },
        language=language,
        seed=seed_value,
    )
    provider_rendering = voice_emotion_smoothing["smoothed_provider_rendering"]
    voice_semantic_emphasis = apply_voice_semantic_emphasis(
        campaign,
        provider_rendering,
        language=language,
        seed=seed_value,
    )
    provider_rendering = voice_semantic_emphasis["semantic_provider_rendering"]
    voice_low_pressure_focus = apply_voice_low_pressure_focus(
        campaign,
        provider_rendering,
        language=language,
        seed=seed_value,
    )
    provider_rendering = voice_low_pressure_focus["focused_provider_rendering"]
    validation = validate_delivery(
        guarded_packet,
        segments,
        spoken_text_normalization,
        speech_realism,
        speech_interaction,
        speech_imperfections,
        prosody,
        provider_rendering,
        voice_pacing_calibration,
        voice_connected_speech,
        voice_listening_calibration,
        voice_emotion_smoothing,
        voice_semantic_emphasis,
        voice_low_pressure_focus,
    )

    return {
        "runtime_voice_delivery_id": RUNTIME_VOICE_DELIVERY_ID,
        "enabled": True,
        "provider_key": provider_key,
        "provider_name": provider["provider_name"],
        "language": language,
        "final_response_unchanged": validation["final_response_unchanged"],
        "provider_calls_made": False,
        "requires_api_key": False,
        "customer_audio_uploaded": False,
        "voice_cloning_used": False,
        "generated_audio_created": False,
        "segments": segments,
        "spoken_segments": spoken_segments,
        "realistic_segments": realistic_segments,
        "interaction_segments": interaction_segments,
        "imperfect_segments": imperfect_segments,
        "spoken_text_normalization": spoken_text_normalization,
        "speech_realism": speech_realism,
        "speech_interaction": speech_interaction,
        "speech_imperfections": speech_imperfections,
        "prosody": prosody,
        "voice_pacing_calibration": voice_pacing_calibration,
        "voice_connected_speech": voice_connected_speech,
        "voice_listening_calibration": voice_listening_calibration,
        "voice_emotion_smoothing": voice_emotion_smoothing,
        "voice_semantic_emphasis": voice_semantic_emphasis,
        "voice_low_pressure_focus": voice_low_pressure_focus,
        "provider_rendering": provider_rendering,
        "validation": validation,
        "runtime_boundary": {
            "position": "after RESP-001 guarded response generation and before live TTS",
            "changes_allowed": "delivery metadata, safe spoken freeform TTS wording, interaction prosody cues, opt-in controlled imperfections, pacing calibration, connected-speech flow, listening-feedback calibration, emotion-transition smoothing, semantic-emphasis wording candidates, low-pressure focus corrections, and provider-specific TTS input only",
            "changes_forbidden": [
                "changing final_response",
                "changing call_control",
                "changing selected strategy",
                "adding claims",
                "editing protected campaign or compliance text",
                "calling a provider without an explicit later live TTS checkpoint",
            ],
        },
    }


def attach_runtime_voice_delivery(
    guarded_packet: dict[str, Any],
    campaign: dict[str, Any],
    provider_key: str = "elevenlabs",
    seed: str | None = None,
) -> dict[str, Any]:
    packet = deepcopy(guarded_packet)
    packet["runtime_voice_delivery_id"] = RUNTIME_VOICE_DELIVERY_ID
    packet["voice_delivery"] = build_runtime_voice_delivery(
        guarded_packet=guarded_packet,
        campaign=campaign,
        provider_key=provider_key,
        seed=seed,
    )
    return packet
