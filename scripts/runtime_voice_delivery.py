#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
from typing import Any

from prosody_naturalness import apply_prosody_naturalness
from provider_prosody_rendering import render_provider_variant, validate_variant
from speech_realism import apply_speech_realism
from spoken_text_normalization import apply_spoken_text_normalization


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


def validate_delivery(
    packet: dict[str, Any],
    segments: list[dict[str, Any]],
    spoken_text_normalization: dict[str, Any],
    speech_realism: dict[str, Any],
    prosody: dict[str, Any],
    provider_rendering: dict[str, Any],
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
    passed = (
        final_response_unchanged
        and spoken_text_normalization["validation"]["passed"]
        and speech_realism["validation"]["passed"]
        and prosody["validation"]["passed"]
        and provider_validation["passed"]
        and protected_segment_change_count == 0
        and speech_realism_protected_segment_change_count == 0
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
        "prosody_validation_passed": prosody["validation"]["passed"],
        "provider_validation": provider_validation,
        "protected_segment_change_count": protected_segment_change_count,
        "speech_realism_protected_segment_change_count": speech_realism_protected_segment_change_count,
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
    prosody = apply_prosody_naturalness(campaign, realistic_segments, language=language, seed=seed_value)
    provider_result = build_provider_result_shape(guarded_packet, campaign, prosody, language)
    provider_rendering = render_provider_variant(provider_result, provider)
    validation = validate_delivery(
        guarded_packet,
        segments,
        spoken_text_normalization,
        speech_realism,
        prosody,
        provider_rendering,
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
        "spoken_text_normalization": spoken_text_normalization,
        "speech_realism": speech_realism,
        "prosody": prosody,
        "provider_rendering": provider_rendering,
        "validation": validation,
        "runtime_boundary": {
            "position": "after RESP-001 guarded response generation and before live TTS",
            "changes_allowed": "delivery metadata, safe spoken freeform TTS wording, and provider-specific TTS input only",
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
