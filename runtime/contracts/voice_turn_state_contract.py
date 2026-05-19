from __future__ import annotations

TURN_TAKING_CONTROLLER = "voice-turn-state-machine"

VOICE_TURN_STATE_IDLE = "idle"
VOICE_TURN_STATE_LISTENING = "listening"
VOICE_TURN_STATE_AGENT_THINKING = "agent_thinking"
VOICE_TURN_STATE_AGENT_SPEAKING = "agent_speaking"
VOICE_TURN_STATE_PAUSED = "paused"

VOICE_TURN_STATE_VALUES = [
    VOICE_TURN_STATE_IDLE,
    VOICE_TURN_STATE_LISTENING,
    VOICE_TURN_STATE_AGENT_THINKING,
    VOICE_TURN_STATE_AGENT_SPEAKING,
    VOICE_TURN_STATE_PAUSED,
]

RESTART_AFTER_AGENT_OUTPUT_MS = 750


def voice_turn_state_metadata() -> dict:
    return {
        "controller": TURN_TAKING_CONTROLLER,
        "states": list(VOICE_TURN_STATE_VALUES),
        "listen_while_agent_speaks": False,
        "listen_while_turn_in_flight": False,
        "agent_talks_after": "accepted final transcript and local runtime response",
        "restart_after_agent_output_ms": RESTART_AFTER_AGENT_OUTPUT_MS,
        "server_policy": "reject low-confidence ASR before demo response selection",
    }


def turn_taking_packet(voice_turn_state: str | None) -> dict:
    return {
        "voice_turn_state_received": voice_turn_state,
        "server_policy": "answer_only_after_final_accepted_transcript",
        "listen_while_agent_speaks": False,
        "restart_after_agent_output_ms": RESTART_AFTER_AGENT_OUTPUT_MS,
    }
