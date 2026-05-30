from __future__ import annotations

import os
from typing import Any

from runtime.action_selector.shadow_runtime_logger import run_shadow_selector_read_only


ENV_GATE = "ACTION_SELECTOR_SHADOW_LOGGING_ENABLED"


def should_run_action_selector_shadow_logging(env: dict | None = None) -> bool:
    source = os.environ if env is None else env
    return str(source.get(ENV_GATE) or "") == "1"


def maybe_log_action_selector_shadow_turn(turn_context: dict) -> dict:
    if not should_run_action_selector_shadow_logging():
        return {
            "enabled": False,
            "reason": "ACTION_SELECTOR_SHADOW_LOGGING_ENABLED_not_set",
            "record": None,
            "runtime_metadata_extraction_supported": True,
            "side_effects_allowed": False,
            "buyer_facing_text_generated": False,
            "live_runtime_wiring_allowed": False,
            "response_text_changed": False,
            "runtime_behavior_changed": False,
            "memory_mutation_allowed": False,
            "provider_calls_made": False,
            "openai_api_calls_made": False,
            "ultravox_calls_made": False,
            "elevenlabs_calls_made": False,
            "local_llm_calls_made": False,
            "ollama_calls_made": False,
            "tts_calls_made": False,
        }
    record = run_shadow_selector_read_only(
        dict(turn_context),
        expected_action_id=str(turn_context.get("expected_action_id") or ""),
        mode="disabled_runtime_hook",
    )
    return {
        "enabled": True,
        "reason": "read_only_shadow_record_built_in_memory_only",
        "record": record,
        "runtime_metadata_extraction_supported": True,
        "side_effects_allowed": False,
        "buyer_facing_text_generated": False,
        "live_runtime_wiring_allowed": False,
        "response_text_changed": False,
        "runtime_behavior_changed": False,
        "memory_mutation_allowed": False,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "ultravox_calls_made": False,
        "elevenlabs_calls_made": False,
        "local_llm_calls_made": False,
        "ollama_calls_made": False,
        "tts_calls_made": False,
    }
