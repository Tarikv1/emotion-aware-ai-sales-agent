#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import os
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from runtime.providers.tts_provider_clients import (
    call_cartesia_websocket,
    call_elevenlabs_stream,
    fallback_reason,
    maybe_remove,
    normalize_language,
    redacted_request_preview,
    resolve_voice_id,
)


ROOT = Path(__file__).resolve().parents[2]
RUNTIME_TTS_DELIVERY_ID = "RESP-003-runtime-live-tts"
LIVE_DEMO_STABLE_ELEVENLABS_VOICE_SETTINGS = {
    "stability": 0.56,
    "similarity_boost": 0.75,
    "style": 0.0,
    "use_speaker_boost": True,
    "speed": 1.11,
}

PROVIDERS = {
    "elevenlabs": {
        "provider_key": "elevenlabs",
        "provider_id": "elevenlabs-stream",
        "provider_name": "ElevenLabs",
        "endpoint_type": "tts-http-stream",
        "endpoint_url_template": "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream",
        "model_id": "eleven_flash_v2_5",
        "api_key_env_var": "ELEVENLABS_API_KEY",
        "default_voice_id_env_var": "ELEVENLABS_VOICE_ID",
        "language_voice_id_env_vars": {
            "de": "ELEVENLABS_VOICE_ID_DE",
            "en": "ELEVENLABS_VOICE_ID_EN",
        },
        "default_output_format": "mp3_44100_128",
        "audio_extension": "mp3",
        "enable_logging": False,
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
        "provider_id": "cartesia-sonic-3-websocket",
        "provider_name": "Cartesia",
        "endpoint_type": "tts-websocket",
        "endpoint_url": "wss://api.cartesia.ai/tts/websocket",
        "api_version": "2026-03-01",
        "model_id": "sonic-3",
        "api_key_env_var": "CARTESIA_API_KEY",
        "default_voice_id_env_var": "CARTESIA_VOICE_ID",
        "language_voice_id_env_vars": {
            "de": "CARTESIA_VOICE_ID_DE",
            "en": "CARTESIA_VOICE_ID_EN",
        },
        "default_output_format": {
            "container": "raw",
            "encoding": "pcm_s16le",
            "sample_rate": 16000,
        },
        "audio_extension": "wav",
        "add_timestamps": True,
    },
}


def provider_for_key(provider_key: str) -> dict[str, Any]:
    if provider_key not in PROVIDERS:
        known = ", ".join(sorted(PROVIDERS))
        raise ValueError(f"Unknown provider {provider_key!r}. Known providers: {known}")
    return deepcopy(PROVIDERS[provider_key])


def safe_filename_part(value: str | None, fallback: str) -> str:
    text = value or fallback
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", text).strip("-")
    return cleaned[:80] or fallback


def audio_filename(packet: dict[str, Any], provider_key: str, language: str, extension: str) -> str:
    campaign = packet.get("campaign", {})
    source = "|".join(
        [
            str(campaign.get("campaign_id", "")),
            str(packet.get("stage", "")),
            str(packet.get("transcript", "")),
            provider_key,
            language,
        ]
    )
    digest = hashlib.sha1(source.encode("utf-8")).hexdigest()[:8]
    campaign_part = safe_filename_part(campaign.get("campaign_id"), "campaign")
    return f"RESP-003-{campaign_part}-{language}-{provider_key}-{digest}.{extension}"


def redacted_voice_id_diagnostics(voice_id: str | None, source: str | None) -> dict[str, Any]:
    present = bool(voice_id)
    return {
        "source": source,
        "present": present,
        "length": len(voice_id) if voice_id else 0,
        "sha256_8": hashlib.sha256(voice_id.encode("utf-8")).hexdigest()[:8] if voice_id else None,
        "raw_value_logged": False,
    }


def offline_provider_result(reason: str, audio_path: Path) -> dict[str, Any]:
    maybe_remove(audio_path)
    return {
        "api_call_made": False,
        "fallback_used": True,
        "fallback_reason": reason,
        "audio_file_created": False,
        "audio_output_path": None,
        "audio_byte_size": 0,
        "http_status": None,
        "response_content_type": None,
        "request_id_present": False,
        "time_to_first_audio_ms": None,
        "total_provider_latency_ms": 0,
        "provider_error": None,
        "provider_error_summary": {"type": None, "code": None, "message": None},
    }


def select_tts_input(packet: dict[str, Any]) -> dict[str, Any]:
    delivery = packet["voice_delivery"]
    provider_rendering = delivery["provider_rendering"]
    provider_validation = delivery["validation"].get("provider_validation", {})
    all_segments_eligible = all(segment.get("eligible_for_prosody") is True for segment in delivery["segments"])
    rendered_text = provider_rendering.get("rendered_text") or ""
    final_response = packet["final_response"]
    provider_rendering_used = (
        all_segments_eligible
        and provider_validation.get("passed") is True
        and bool(rendered_text.strip())
        and rendered_text != final_response
    )
    if provider_rendering_used:
        return {
            "tts_input_source": "provider_rendered_text",
            "tts_input_text": rendered_text,
            "provider_rendering_used": True,
        }
    return {
        "tts_input_source": "final_response",
        "tts_input_text": final_response,
        "provider_rendering_used": False,
    }


def voice_settings_for_provider(provider: dict[str, Any], packet: dict[str, Any], provider_key: str) -> dict[str, Any]:
    if provider_key != "elevenlabs":
        return {}
    rendered_settings = packet["voice_delivery"]["provider_rendering"].get("voice_settings") or {}
    if rendered_settings:
        return dict(rendered_settings)
    return dict(provider.get("base_voice_settings", {}))


def stable_voice_settings_for_provider(provider_key: str, voice_consistency_mode: str | None) -> dict[str, Any] | None:
    if provider_key == "elevenlabs" and voice_consistency_mode == "live-demo-stable":
        return dict(LIVE_DEMO_STABLE_ELEVENLABS_VOICE_SETTINGS)
    return None


def build_asset_log(
    packet: dict[str, Any],
    provider: dict[str, Any],
    provider_key: str,
    language: str,
    voice_env_var: str,
    timeout_seconds: float,
    tts_input: dict[str, Any],
    provider_result: dict[str, Any],
    command_name: str,
) -> dict[str, Any]:
    audio_output_path = provider_result.get("audio_output_path")
    status = "needs review" if provider_result.get("audio_file_created") else "not created"
    return {
        "asset_log_id": "RESP-003-generated-audio-asset-log",
        "experiment_id": RUNTIME_TTS_DELIVERY_ID,
        "asset_id": audio_output_path or "no-audio-created",
        "output_path": audio_output_path or "",
        "audio_format": provider["audio_extension"],
        "provider": provider_key,
        "provider_model": provider["model_id"],
        "provider_voice_env_var": voice_env_var,
        "language": language,
        "campaign_id": packet.get("campaign", {}).get("campaign_id"),
        "status": status,
        "inputs": {
            "source_text": packet["final_response"],
            "source_text_path": "runtime guarded response packet",
            "provider_rendered_text": tts_input["tts_input_text"] if tts_input["provider_rendering_used"] else "",
            "synthetic_prompt": True,
            "customer_audio_uploaded": False,
            "source_audio_used": False,
            "source_audio_rights": "not applicable",
            "person_or_voice_likeness_involved": False,
            "voice_cloning_used": False,
            "consent_note": "No customer audio or voice cloning used by RESP-003.",
        },
        "run_boundary": {
            "network_used": provider_result["api_call_made"],
            "upload_used": False,
            "cost": "provider API call" if provider_result["api_call_made"] else "none",
            "api_key_location": "environment-only",
            "environment_variables_used": [provider["api_key_env_var"], voice_env_var],
            "command": command_name,
            "timeout_seconds": timeout_seconds,
            "fallback_used": provider_result["fallback_used"],
            "provider_error": provider_result.get("provider_error"),
        },
        "review": {
            "human_listening_review": False,
            "naturalness": None,
            "clarity": None,
            "language_pronunciation": None,
            "pacing": None,
            "muffling_or_artifacts": None,
            "emotional_appropriateness": None,
            "trustworthiness": None,
            "sales_usefulness": None,
            "compliance_concern": False,
            "decision": "needs review",
            "follow_up": "Listen to generated audio before making quality claims." if audio_output_path else "",
        },
    }


def validate_tts_delivery(packet: dict[str, Any], delivery: dict[str, Any]) -> dict[str, Any]:
    request_preview_text = str(delivery.get("request_preview", {}))
    passed = (
        delivery["source_runtime_voice_delivery_id"] == "RESP-002-runtime-voice-delivery"
        and delivery["api_key_value_logged"] is False
        and delivery["voice_id_value_logged"] is False
        and delivery["customer_audio_uploaded"] is False
        and delivery["voice_cloning_used"] is False
        and delivery["synthetic_prompt_only"] is True
        and 0 < delivery["timeout_seconds"] <= 10
        and "<redacted>" in request_preview_text
        and delivery["asset_log"]["run_boundary"]["api_key_location"] == "environment-only"
        and delivery["asset_log"]["inputs"]["customer_audio_uploaded"] is False
        and delivery["asset_log"]["inputs"]["voice_cloning_used"] is False
        and (
            delivery["live_call_requested"]
            or (
                delivery["provider_calls_made"] is False
                and delivery["generated_text_sent_to_provider"] is False
                and delivery["audio_file_created"] is False
            )
        )
        and packet["final_response"] == delivery["asset_log"]["inputs"]["source_text"]
    )
    return {
        "validator": "RESP-003 runtime live TTS safety check",
        "passed": passed,
        "final_response_unchanged": packet["final_response"] == delivery["asset_log"]["inputs"]["source_text"],
        "redacted_request_preview": "<redacted>" in request_preview_text,
        "provider_calls_made": delivery["provider_calls_made"],
        "customer_audio_uploaded": delivery["customer_audio_uploaded"],
        "voice_cloning_used": delivery["voice_cloning_used"],
        "timeout_within_limit": 0 < delivery["timeout_seconds"] <= 10,
        "notes": (
            "RESP-003 respected provider boundary and audio asset logging rules."
            if passed
            else "RESP-003 failed a provider boundary or asset logging check."
        ),
    }


def build_runtime_tts_delivery(
    packet: dict[str, Any],
    provider_key: str = "elevenlabs",
    live: bool = False,
    force_key_missing: bool = False,
    audio_dir: Path | None = None,
    timeout_seconds: float = 8.0,
    command_name: str = "scripts/generate_runtime_tts_delivery.py",
    voice_consistency_mode: str | None = None,
) -> dict[str, Any]:
    if timeout_seconds <= 0 or timeout_seconds > 10:
        raise ValueError("timeout_seconds must be greater than 0 and no more than 10.")
    if packet.get("runtime_voice_delivery_id") != "RESP-002-runtime-voice-delivery":
        raise ValueError("RESP-003 requires a RESP-002 runtime voice delivery packet.")
    if packet["voice_delivery"]["validation"]["passed"] is not True:
        raise ValueError("RESP-003 requires a validated RESP-002 voice delivery packet.")

    provider = provider_for_key(provider_key)
    language = normalize_language(packet["voice_delivery"].get("language"))
    audio_root = audio_dir or ROOT / "research" / "experiments" / "generated"
    audio_path = audio_root / audio_filename(packet, provider_key, language, provider["audio_extension"])
    voice_id, voice_env_var = resolve_voice_id(provider, language, force_key_missing)
    voice_diagnostics = redacted_voice_id_diagnostics(voice_id, voice_env_var)
    api_key = None if force_key_missing else os.environ.get(provider["api_key_env_var"])
    can_call_live = live and bool(api_key) and bool(voice_id)
    tts_input = select_tts_input(packet)
    dynamic_voice_settings = voice_settings_for_provider(provider, packet, provider_key)
    stable_voice_settings = stable_voice_settings_for_provider(provider_key, voice_consistency_mode)
    voice_settings = stable_voice_settings or dynamic_voice_settings
    voice_settings_source = "live_demo_stable_profile" if stable_voice_settings else "runtime_provider_rendering"
    request_preview = redacted_request_preview(
        provider=provider,
        provider_key=provider_key,
        language=language,
        text=tts_input["tts_input_text"],
        voice_settings=voice_settings,
        voice_env_var=voice_env_var,
    )

    if can_call_live and provider_key == "elevenlabs":
        provider_result = call_elevenlabs_stream(
            provider=provider,
            text=tts_input["tts_input_text"],
            language=language,
            voice_settings=voice_settings,
            audio_path=audio_path,
            api_key=api_key or "",
            voice_id=voice_id or "",
            timeout_seconds=timeout_seconds,
        )
    elif can_call_live and provider_key == "cartesia":
        provider_result = call_cartesia_websocket(
            provider=provider,
            text=tts_input["tts_input_text"],
            language=language,
            audio_path=audio_path,
            api_key=api_key or "",
            voice_id=voice_id or "",
            timeout_seconds=timeout_seconds,
        )
    else:
        provider_result = offline_provider_result(
            fallback_reason(live, force_key_missing, api_key, voice_id, provider_key),
            audio_path,
        )

    asset_log = build_asset_log(
        packet=packet,
        provider=provider,
        provider_key=provider_key,
        language=language,
        voice_env_var=voice_env_var,
        timeout_seconds=timeout_seconds,
        tts_input=tts_input,
        provider_result=provider_result,
        command_name=command_name,
    )
    delivery = {
        "runtime_tts_delivery_id": RUNTIME_TTS_DELIVERY_ID,
        "source_runtime_voice_delivery_id": packet["runtime_voice_delivery_id"],
        "provider_key": provider_key,
        "provider_id": provider["provider_id"],
        "provider_name": provider["provider_name"],
        "endpoint_type": provider["endpoint_type"],
        "model_id": provider["model_id"],
        "language": language,
        "live_call_requested": live,
        "requires_api_key": live and not force_key_missing,
        "api_key_env_var": provider["api_key_env_var"],
        "selected_voice_id_env_var": voice_env_var,
        "selected_voice_id_source": voice_env_var,
        "voice_id_diagnostics": voice_diagnostics,
        "api_key_present": bool(api_key),
        "voice_id_present": bool(voice_id),
        "api_key_value_logged": False,
        "voice_id_value_logged": False,
        "customer_audio_uploaded": False,
        "generated_text_sent_to_provider": provider_result["api_call_made"],
        "synthetic_prompt_only": True,
        "voice_cloning_used": False,
        "custom_voice_used": False,
        "timeout_seconds": timeout_seconds,
        "tts_input_source": tts_input["tts_input_source"],
        "tts_input_text": tts_input["tts_input_text"],
        "provider_rendering_used": tts_input["provider_rendering_used"],
        "voice_consistency_mode": voice_consistency_mode or "runtime-dynamic",
        "voice_settings_source": voice_settings_source,
        "voice_settings": voice_settings,
        "request_preview": request_preview,
        "provider_calls_made": provider_result["api_call_made"],
        "audio_file_created": provider_result["audio_file_created"],
        "audio_output_path": provider_result["audio_output_path"],
        "audio_byte_size": provider_result["audio_byte_size"],
        "fallback_used": provider_result["fallback_used"],
        "fallback_reason": provider_result["fallback_reason"],
        "http_status": provider_result["http_status"],
        "response_content_type": provider_result["response_content_type"],
        "request_id_present": provider_result["request_id_present"],
        "time_to_first_audio_ms": provider_result.get("time_to_first_audio_ms"),
        "total_provider_latency_ms": provider_result["total_provider_latency_ms"],
        "provider_error": provider_result.get("provider_error"),
        "provider_error_summary": provider_result.get("provider_error_summary"),
        "asset_log": asset_log,
        "runtime_boundary": {
            "position": "after RESP-002 runtime voice delivery and before playback",
            "default_mode": "dry-run-no-provider-call",
            "live_call_requires": ["--live", provider["api_key_env_var"], voice_env_var],
            "changes_allowed": "audio generation from approved TTS input only",
            "changes_forbidden": [
                "changing final_response",
                "changing sales policy decisions",
                "writing API keys or voice IDs to files",
                "uploading customer audio",
                "using voice cloning",
                "running without a bounded timeout",
                "making audio quality claims without human listening review",
            ],
        },
    }
    delivery["validation"] = validate_tts_delivery(packet, delivery)
    return delivery


def attach_runtime_tts_delivery(
    packet: dict[str, Any],
    provider_key: str = "elevenlabs",
    live: bool = False,
    force_key_missing: bool = False,
    audio_dir: Path | None = None,
    timeout_seconds: float = 8.0,
    command_name: str = "scripts/generate_runtime_tts_delivery.py",
    voice_consistency_mode: str | None = None,
) -> dict[str, Any]:
    enriched = deepcopy(packet)
    enriched["runtime_tts_delivery_id"] = RUNTIME_TTS_DELIVERY_ID
    enriched["tts_delivery"] = build_runtime_tts_delivery(
        packet=packet,
        provider_key=provider_key,
        live=live,
        force_key_missing=force_key_missing,
        audio_dir=audio_dir,
        timeout_seconds=timeout_seconds,
        command_name=command_name,
        voice_consistency_mode=voice_consistency_mode,
    )
    return enriched
