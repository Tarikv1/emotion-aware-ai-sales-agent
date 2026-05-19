from __future__ import annotations

from runtime.contracts.voice_turn_state_contract import (
    VOICE_TURN_STATE_AGENT_SPEAKING,
    VOICE_TURN_STATE_AGENT_THINKING,
)
from runtime.speech.asr_quality_gate import ASR_LOW_CONFIDENCE_THRESHOLD, looks_like_asr_fragment, normalize_transcript

CHECKPOINT_ID = "LIVE-DEMO-004-realtime-turn-taking-asr-vad"

FINAL_TRANSCRIPT_SUBMIT_DELAY_MS = 2200
MIN_LISTENING_WINDOW_BEFORE_SUBMIT_MS = 1600
INTERIM_RESULT_STABILITY_MS = 900
REQUIRES_FINAL_RESULT_FOR_AUTO_SUBMIT = True
SUBMIT_ON_INTERIM_RESULTS = False
CANCEL_PENDING_SUBMIT_ON_INTERIM_CHANGE = True


def realtime_turn_taking_policy() -> dict:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "policy_version": 1,
        "browser_asr_is_true_vad": False,
        "browser_asr_role": "browser_transcription_only",
        "raw_audio_uploaded_to_python_server": False,
        "customer_audio_uploaded_to_provider_by_python": False,
        "requires_final_result_for_auto_submit": REQUIRES_FINAL_RESULT_FOR_AUTO_SUBMIT,
        "submit_on_interim_results": SUBMIT_ON_INTERIM_RESULTS,
        "cancel_pending_submit_on_interim_change": CANCEL_PENDING_SUBMIT_ON_INTERIM_CHANGE,
        "final_transcript_submit_delay_ms": FINAL_TRANSCRIPT_SUBMIT_DELAY_MS,
        "min_listening_window_before_submit_ms": MIN_LISTENING_WINDOW_BEFORE_SUBMIT_MS,
        "interim_result_stability_ms": INTERIM_RESULT_STABILITY_MS,
        "reject_while_agent_speaks": True,
        "reject_while_turn_in_flight": True,
        "low_confidence_threshold": ASR_LOW_CONFIDENCE_THRESHOLD,
        "manual_send_allowed": True,
        "known_limitations": [
            "browser SpeechRecognition final events are not true VAD",
            "thinking pauses can still end browser recognition",
            "provider or local streaming ASR/VAD is a future checkpoint",
        ],
    }


def browser_asr_acceptance_policy() -> dict:
    policy = realtime_turn_taking_policy()
    return {
        "low_confidence_threshold": ASR_LOW_CONFIDENCE_THRESHOLD,
        "final_transcript_submit_delay_ms": policy["final_transcript_submit_delay_ms"],
        "min_listening_window_before_submit_ms": policy["min_listening_window_before_submit_ms"],
        "requires_final_result_for_auto_submit": policy["requires_final_result_for_auto_submit"],
        "submit_on_interim_results": policy["submit_on_interim_results"],
        "cancel_pending_submit_on_interim_change": policy["cancel_pending_submit_on_interim_change"],
        "reject_empty_transcript": True,
        "reject_obvious_fragments": True,
        "reject_while_agent_speaks": True,
        "reject_while_turn_in_flight": True,
    }


def should_auto_submit_browser_asr(
    *,
    transcript: str,
    confidence: float | None,
    voice_turn_state: str | None,
    turn_in_flight: bool,
    has_final_result: bool,
    listening_elapsed_ms: int | float,
    selected_focus: str | None = None,
) -> dict:
    normalized = normalize_transcript(transcript)
    policy = realtime_turn_taking_policy()
    if not normalized:
        return {"accepted": False, "reason": "empty_transcript"}
    if voice_turn_state in {VOICE_TURN_STATE_AGENT_SPEAKING, VOICE_TURN_STATE_AGENT_THINKING}:
        return {"accepted": False, "reason": "agent_not_listening"}
    if turn_in_flight:
        return {"accepted": False, "reason": "turn_in_flight"}
    if policy["requires_final_result_for_auto_submit"] and not has_final_result:
        return {"accepted": False, "reason": "wait_for_final_result"}
    if float(listening_elapsed_ms or 0) < policy["min_listening_window_before_submit_ms"]:
        return {
            "accepted": False,
            "reason": "minimum_listening_window",
            "retry_after_ms": policy["min_listening_window_before_submit_ms"] - int(listening_elapsed_ms or 0),
        }
    if looks_like_asr_fragment(normalized, selected_focus):
        return {"accepted": False, "reason": "fragment"}
    if confidence is not None and confidence < ASR_LOW_CONFIDENCE_THRESHOLD:
        return {"accepted": False, "reason": "low_confidence"}
    return {"accepted": True, "reason": "accepted"}
