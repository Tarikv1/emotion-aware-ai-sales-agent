from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from runtime.core import campaign_registry
from runtime.core import campaign_playbook_adapter
from runtime.core import dialogue_manager
from runtime.core import universal_sales_knowledge
from runtime.core import vertical_sales_playbooks
from runtime.entrypoints.generate_guarded_response import build_guarded_response_packet
from runtime.speech.asr_quality_gate import evaluate_asr_quality
from runtime.voice.runtime_tts_delivery import attach_runtime_tts_delivery
from runtime.voice.runtime_voice_delivery import attach_runtime_voice_delivery


ENTRYPOINT_ID = "GENERIC-CAMPAIGN-TURN-001"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PRIVATE_OUT = ROOT / ".tmp" / "generic-campaign-turn"
ROUTESIGNAL_PLAYBOOK_ID = "ROUTESIGNAL-DIAGNOSTIC-PLAYBOOK-001"
SAFETY_FLAGS = {
    "provider_calls_made": False,
    "local_llm_calls_made": False,
    "sends_email": False,
    "creates_calendar_event": False,
    "writes_crm": False,
    "opens_prod_102": False,
}


class GenericCampaignConfigError(ValueError):
    """Raised when a generic campaign config cannot be used safely."""


def _elapsed_ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item or "")]
    return [str(value)] if str(value or "") else []


def _normalized_campaign(campaign: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(campaign)
    offer = normalized.get("offer_name") or normalized.get("product_or_offer_name") or normalized.get("product_name")
    if offer:
        normalized.setdefault("offer_name", offer)
        normalized.setdefault("product_or_offer_name", offer)
        normalized.setdefault("product_name", offer)
    return normalized


def validate_generic_campaign_config(campaign: dict[str, Any] | None) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(campaign, dict):
        return {"valid": False, "failures": ["campaign must be a dict"], "campaign_id": None}

    normalized = _normalized_campaign(campaign)
    campaign_id = str(normalized.get("campaign_id") or "")
    vertical_id = str(normalized.get("vertical_id") or "")
    if not campaign_id:
        failures.append("campaign_id is required")
    if not vertical_id:
        failures.append("vertical_id is required")
    elif vertical_id not in set(vertical_sales_playbooks.all_vertical_ids()):
        failures.append(f"unsupported vertical_id: {vertical_id}")

    if not isinstance(normalized.get("diagnostic_gaps"), dict) or not normalized.get("diagnostic_gaps"):
        failures.append("diagnostic_gaps must be a populated dict")
    if "allowed_claims" not in normalized:
        failures.append("allowed_claims is required")
    elif not isinstance(normalized.get("allowed_claims"), list):
        failures.append("allowed_claims must be a list")
    if not _string_list(normalized.get("blocked_claims")):
        failures.append("blocked_claims must be populated")
    if not str(normalized.get("human_followup_owner") or ""):
        failures.append("human_followup_owner is required")
    if not str(normalized.get("appointment_target") or ""):
        failures.append("appointment_target is required")
    if not (normalized.get("offer_name") or normalized.get("product_or_offer_name") or normalized.get("product_name")):
        failures.append("offer_name or product_or_offer_name is required")

    if not failures:
        playbook = campaign_playbook_adapter.resolve_campaign_playbook(normalized)
        playbook_validation = campaign_playbook_adapter.validate_campaign_playbook(playbook)
        if playbook.get("campaign_playbook_id") == ROUTESIGNAL_PLAYBOOK_ID:
            failures.append("generic campaign resolved to the default playbook")
        failures.extend(str(item) for item in playbook_validation.get("failures") or [])
    else:
        playbook = {}
        playbook_validation = {"valid": False, "failures": list(failures)}

    return {
        "valid": not failures,
        "entrypoint_id": ENTRYPOINT_ID,
        "campaign_id": campaign_id or None,
        "vertical_id": vertical_id or None,
        "campaign_playbook_id": playbook.get("campaign_playbook_id"),
        "failures": failures,
        "playbook_validation": playbook_validation,
    }


def _raise_if_invalid(campaign: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    normalized = _normalized_campaign(campaign)
    validation = validate_generic_campaign_config(normalized)
    if validation.get("valid") is not True:
        raise GenericCampaignConfigError("invalid generic campaign config: " + "; ".join(validation.get("failures") or []))
    playbook = campaign_playbook_adapter.resolve_campaign_playbook(normalized)
    return normalized, playbook, validation


def _summary(packet: dict[str, Any]) -> dict[str, Any]:
    decision = packet.get("decision_snapshot") or {}
    tts = packet.get("tts_delivery") or {}
    retrieval = packet.get("retrieval") or {}
    composer_hooks = packet.get("composer_hooks") or {}
    return {
        "sales_difficulty": decision.get("sales_difficulty"),
        "detected_emotion": decision.get("detected_emotion"),
        "interest_state": decision.get("interest_state"),
        "selected_strategy": decision.get("selected_strategy"),
        "next_action": decision.get("next_action"),
        "call_control": decision.get("call_control"),
        "final_response": packet.get("final_response"),
        "candidate_response": packet.get("candidate_response"),
        "tts_input_source": tts.get("tts_input_source"),
        "tts_input_text": tts.get("tts_input_text"),
        "tts_provider_rendering_used": tts.get("provider_rendering_used"),
        "retrieval_status": retrieval.get("status"),
        "retrieval_used_in_runtime": retrieval.get("retrieval_used_in_runtime"),
        "composer_hooks_status": composer_hooks.get("status"),
        "composer_hooks_applied": composer_hooks.get("applied"),
        "tts_provider_calls_made": bool(tts.get("provider_calls_made")),
        "tts_audio_file_created": bool(tts.get("audio_file_created")),
        "tts_fallback_reason": tts.get("fallback_reason"),
    }


def _external_flags(packet: dict[str, Any], dialogue_trace: dict[str, Any], conversation_memory: dict[str, Any]) -> dict[str, bool]:
    tts = packet.get("tts_delivery") or {}
    voice = packet.get("voice_delivery") or {}
    lead = conversation_memory.get("lead_followup_state") or {}
    safety = lead.get("safety") or {}
    return {
        "provider_calls_made": bool(tts.get("provider_calls_made") or voice.get("provider_calls_made") or packet.get("api_calls_made")),
        "local_llm_calls_made": bool(dialogue_trace.get("local_llm_calls_made") or packet.get("llm_used")),
        "sends_email": bool(safety.get("sends_email")),
        "creates_calendar_event": bool(safety.get("creates_calendar_event")),
        "writes_crm": bool(safety.get("writes_crm")),
        "opens_prod_102": bool(dialogue_trace.get("opens_prod_102") or packet.get("opens_prod_102")),
    }


def build_generic_campaign_turn_packet(
    *,
    transcript: str,
    campaign: dict,
    stage: str = "relevance-check",
    input_type: str = "speech-final",
    silence_count: int = 0,
    session_id: str | None = None,
    session_state: dict | None = None,
    asr_confidence: float | None = 0.94,
    voice_turn_state: str | None = "listening",
    private_out: Path | None = None,
    live_tts: bool = False,
    force_key_missing: bool = False,
    timeout_seconds: float = 8.0,
) -> dict:
    start = time.perf_counter()
    campaign_config, playbook, validation = _raise_if_invalid(campaign)
    state = session_state if isinstance(session_state, dict) else {"turns": []}
    effective_input_type = "agent-open" if transcript == "__agent_open__" and input_type == "speech-final" else input_type
    output_root = private_out or DEFAULT_PRIVATE_OUT
    quality_gate = evaluate_asr_quality(transcript, asr_confidence)

    dialogue_action = dialogue_manager.plan_dialogue_action(
        transcript=transcript,
        session_state=state,
        campaign=campaign_config,
        quality_gate=quality_gate,
        dialogue_reasoning={
            "entrypoint_id": ENTRYPOINT_ID,
            "provider_calls_made": False,
            "local_llm_calls_made": False,
        },
    )

    def guarded_packet_for_action(action: dict[str, Any]) -> dict[str, Any]:
        return build_guarded_response_packet(
            campaign=campaign_config,
            stage=stage,
            input_type=effective_input_type,
            transcript=transcript,
            silence_count=silence_count,
            candidate_response_override=dialogue_manager.candidate_response(action),
            retrieval_enabled=False,
            composer_hooks_enabled=False,
            align_decision_trace=True,
        )

    guarded = guarded_packet_for_action(dialogue_action)
    updated_action = dialogue_manager.apply_anti_loop_if_needed(
        action=dialogue_action,
        transcript=transcript,
        session_state=state,
        campaign=campaign_config,
        generated_response=str(guarded.get("final_response") or ""),
    )
    if updated_action is not dialogue_action:
        dialogue_action = updated_action
        guarded = guarded_packet_for_action(dialogue_action)

    updated_action = dialogue_manager.apply_duplicate_repair_if_needed(
        action=dialogue_action,
        transcript=transcript,
        session_state=state,
        campaign=campaign_config,
        generated_response=str(guarded.get("final_response") or ""),
    )
    if updated_action is not dialogue_action:
        dialogue_action = updated_action
        guarded = guarded_packet_for_action(dialogue_action)

    continuity = dialogue_manager.continuity(dialogue_action)
    conversation_memory = dialogue_manager.build_conversation_memory(
        action=dialogue_action,
        session_state=state,
        transcript=transcript,
        final_response=str(guarded.get("final_response") or ""),
        campaign=campaign_config,
    )
    updated_action, stability_guard = dialogue_manager.apply_stability_guard_if_needed(
        action=dialogue_action,
        transcript=transcript,
        session_state=state,
        campaign=campaign_config,
        generated_response=str(guarded.get("final_response") or ""),
        conversation_memory=conversation_memory,
    )
    if updated_action is not dialogue_action:
        dialogue_action = updated_action
        guarded = guarded_packet_for_action(dialogue_action)
        continuity = dialogue_manager.continuity(dialogue_action)
        conversation_memory = dialogue_manager.build_conversation_memory(
            action=dialogue_action,
            session_state=state,
            transcript=transcript,
            final_response=str(guarded.get("final_response") or ""),
            campaign=campaign_config,
        )

    guarded = dialogue_manager.apply_decision_override(guarded, dialogue_action)
    voice_packet = attach_runtime_voice_delivery(guarded, campaign_config, provider_key="elevenlabs")
    tts_packet = attach_runtime_tts_delivery(
        voice_packet,
        provider_key="elevenlabs",
        live=bool(live_tts),
        force_key_missing=force_key_missing,
        audio_dir=output_root / "audio",
        timeout_seconds=timeout_seconds,
        command_name="runtime/entrypoints/generic_campaign_turn.py",
        voice_consistency_mode="generic-campaign-stable",
    )
    dialogue_trace = dialogue_manager.finalize_trace(
        action=dialogue_action,
        packet=tts_packet,
        conversation_memory=conversation_memory,
        stability_guard=stability_guard,
    )
    summary = _summary(tts_packet)
    external_flags = _external_flags(tts_packet, dialogue_trace, conversation_memory)
    audio_output = (tts_packet.get("tts_delivery") or {}).get("audio_output_path")
    dry_run_audio_url = None if not live_tts else audio_output

    return {
        "entrypoint_id": ENTRYPOINT_ID,
        "mode": "live-tts" if live_tts else "dry-run",
        "campaign_id": campaign_config.get("campaign_id"),
        "campaign_playbook_id": playbook.get("campaign_playbook_id"),
        "session_id": session_id,
        "session_turn_index": len(state.get("turns") or []) + 1,
        "stage": stage,
        "input_type": effective_input_type,
        "transcript": transcript,
        "asr": {
            "provider": "browser-speech-recognition-or-synthetic-transcript",
            "audio_uploaded_to_python_server": False,
            "transcript_sent_to_python_server": True,
            "confidence": asr_confidence,
            "quality_gate": quality_gate,
        },
        "turn_taking": {
            "voice_turn_state": voice_turn_state,
            "silence_count": silence_count,
        },
        "provider_agent_used": False,
        "durable_provider_agent_created": False,
        "voice_cloning_used": False,
        "runtime_behavior_changed": False,
        "opens_prod_102": external_flags["opens_prod_102"],
        "provider_calls_made": external_flags["provider_calls_made"],
        "local_llm_calls_made": external_flags["local_llm_calls_made"],
        "sends_email": external_flags["sends_email"],
        "creates_calendar_event": external_flags["creates_calendar_event"],
        "writes_crm": external_flags["writes_crm"],
        "conversation_continuity": continuity,
        "conversation_memory": conversation_memory,
        "conversation_stability_guard": stability_guard,
        "demo_session_continuity": continuity,
        "demo_conversation_memory": conversation_memory,
        "demo_conversation_stability_guard": stability_guard,
        "dialogue_manager": dialogue_trace,
        "dialogue_pragmatics": dialogue_trace.get("pragmatic_move") or {},
        "campaign_validation": validation,
        "packet": tts_packet,
        "summary": summary,
        "audio_url": dry_run_audio_url,
        "latency": {
            "server_total_ms": _elapsed_ms(start),
            "browser_asr_ms": None,
        },
        "safety": dict(SAFETY_FLAGS),
    }


def build_generic_campaign_turn_packet_from_config_path(
    *,
    transcript: str,
    campaign_config_path: str | Path,
    stage: str = "relevance-check",
    input_type: str = "speech-final",
    silence_count: int = 0,
    session_id: str | None = None,
    session_state: dict | None = None,
    asr_confidence: float | None = 0.94,
    voice_turn_state: str | None = "listening",
    private_out: Path | None = None,
    live_tts: bool = False,
    force_key_missing: bool = False,
    timeout_seconds: float = 8.0,
) -> dict:
    campaign_config = campaign_registry.load_campaign_config(campaign_config_path)
    return build_generic_campaign_turn_packet(
        transcript=transcript,
        campaign=campaign_config,
        stage=stage,
        input_type=input_type,
        silence_count=silence_count,
        session_id=session_id,
        session_state=session_state,
        asr_confidence=asr_confidence,
        voice_turn_state=voice_turn_state,
        private_out=private_out,
        live_tts=live_tts,
        force_key_missing=force_key_missing,
        timeout_seconds=timeout_seconds,
    )


__all__ = [
    "ENTRYPOINT_ID",
    "GenericCampaignConfigError",
    "build_generic_campaign_turn_packet_from_config_path",
    "build_generic_campaign_turn_packet",
    "validate_generic_campaign_config",
]
