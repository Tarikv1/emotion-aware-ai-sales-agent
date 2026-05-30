from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


RUNTIME_ACTION_METADATA_CONTRACT_VERSION = "RUNTIME-ACTION-METADATA-CONTRACT-001"

RUNTIME_ACTION_METADATA_FIELDS: tuple[str, ...] = (
    "runtime_metadata_available",
    "campaign_id",
    "turn_id",
    "runtime_response_text_available",
    "runtime_response_text_hash",
    "runtime_call_control",
    "runtime_decision_stage",
    "runtime_sales_move",
    "runtime_response_strategy",
    "runtime_recommended_path",
    "runtime_active_decision_frame",
    "runtime_safety_boundary",
    "runtime_terminal_state",
    "runtime_no_fit_state",
    "runtime_repair_state",
    "runtime_source_grounding_state",
    "runtime_action_id",
    "runtime_action_confidence",
    "runtime_action_reason",
    "extraction_warnings",
    "extraction_source",
    "side_effects_allowed",
    "live_runtime_wiring_allowed",
    "memory_mutation_allowed",
    "provider_calls_made",
    "openai_api_calls_made",
    "ultravox_calls_made",
    "elevenlabs_calls_made",
    "local_llm_calls_made",
    "ollama_calls_made",
    "tts_calls_made",
    "response_text_changed",
    "runtime_behavior_changed",
    "raw_private_data",
)


FALSE_BOUNDARY_FIELDS: tuple[str, ...] = (
    "side_effects_allowed",
    "live_runtime_wiring_allowed",
    "memory_mutation_allowed",
    "provider_calls_made",
    "openai_api_calls_made",
    "ultravox_calls_made",
    "elevenlabs_calls_made",
    "local_llm_calls_made",
    "ollama_calls_made",
    "tts_calls_made",
    "response_text_changed",
    "runtime_behavior_changed",
    "raw_private_data",
)


@dataclass(frozen=True)
class RuntimeActionMetadata:
    runtime_metadata_available: bool
    campaign_id: str = ""
    turn_id: str = ""
    runtime_response_text_available: bool = False
    runtime_response_text_hash: str = ""
    runtime_call_control: str = ""
    runtime_decision_stage: str = ""
    runtime_sales_move: str = ""
    runtime_response_strategy: str = ""
    runtime_recommended_path: str = ""
    runtime_active_decision_frame: str = ""
    runtime_safety_boundary: bool = False
    runtime_terminal_state: bool = False
    runtime_no_fit_state: bool = False
    runtime_repair_state: str = ""
    runtime_source_grounding_state: str = ""
    runtime_action_id: str = ""
    runtime_action_confidence: float = 0.0
    runtime_action_reason: str = ""
    extraction_warnings: list[str] = field(default_factory=list)
    extraction_source: str = "runtime_action_metadata_extractor"

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "runtime_metadata_available": bool(self.runtime_metadata_available),
            "campaign_id": self.campaign_id,
            "turn_id": self.turn_id,
            "runtime_response_text_available": bool(self.runtime_response_text_available),
            "runtime_response_text_hash": self.runtime_response_text_hash,
            "runtime_call_control": self.runtime_call_control,
            "runtime_decision_stage": self.runtime_decision_stage,
            "runtime_sales_move": self.runtime_sales_move,
            "runtime_response_strategy": self.runtime_response_strategy,
            "runtime_recommended_path": self.runtime_recommended_path,
            "runtime_active_decision_frame": self.runtime_active_decision_frame,
            "runtime_safety_boundary": bool(self.runtime_safety_boundary),
            "runtime_terminal_state": bool(self.runtime_terminal_state),
            "runtime_no_fit_state": bool(self.runtime_no_fit_state),
            "runtime_repair_state": self.runtime_repair_state,
            "runtime_source_grounding_state": self.runtime_source_grounding_state,
            "runtime_action_id": self.runtime_action_id,
            "runtime_action_confidence": round(max(0.0, min(1.0, float(self.runtime_action_confidence))), 4),
            "runtime_action_reason": self.runtime_action_reason,
            "extraction_warnings": list(self.extraction_warnings),
            "extraction_source": self.extraction_source,
        }
        for key in FALSE_BOUNDARY_FIELDS:
            payload[key] = False
        return payload
