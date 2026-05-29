from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

from runtime.action_selector.action_selector_contract import normalize_text


SHADOW_CONTRACT_VERSION = "NON-LLM-ACTION-SELECTOR-SHADOW-CONTRACT-001"
SHADOW_CONFIG_PATH = Path(__file__).resolve().parent / "shadow_mode_config.json"

SHADOW_INPUT_FIELDS: tuple[str, ...] = (
    "turn_id",
    "campaign_id",
    "buyer_utterance_text",
    "normalized_buyer_text",
    "existing_runtime_action_id",
    "existing_runtime_response_text",
    "memory_summary",
    "known_context",
    "safety_boundary_detected",
    "previous_action_id",
    "previous_answered_topic",
    "evidence_source",
)

SHADOW_OUTPUT_FIELDS: tuple[str, ...] = (
    "selector_action_id",
    "selector_confidence",
    "selector_reasons",
    "selector_matched_features",
    "agreement_with_runtime",
    "disagreement_type",
    "safety_status",
    "side_effects_allowed",
    "buyer_facing_text_generated",
    "live_runtime_wiring_allowed",
    "should_not_change_runtime",
)

DISAGREEMENT_TYPES: tuple[str, ...] = (
    "same_action",
    "compatible_action",
    "selector_more_specific",
    "runtime_more_specific",
    "selector_possible_improvement",
    "selector_possible_regression",
    "unsafe_selector",
    "unknown",
)


def load_shadow_config() -> dict[str, Any]:
    payload = json.loads(SHADOW_CONFIG_PATH.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _string(value: Any) -> str:
    return str(value or "").strip()


@dataclass(frozen=True)
class ShadowModeInput:
    turn_id: str
    campaign_id: str
    buyer_utterance_text: str
    normalized_buyer_text: str = ""
    existing_runtime_action_id: str = ""
    existing_runtime_response_text: str = ""
    memory_summary: str = ""
    known_context: dict[str, Any] = field(default_factory=dict)
    safety_boundary_detected: bool = False
    previous_action_id: str = ""
    previous_answered_topic: str = ""
    evidence_source: str = ""

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "ShadowModeInput":
        buyer_text = _string(payload.get("buyer_utterance_text"))
        known_context = payload.get("known_context") if isinstance(payload.get("known_context"), dict) else {}
        return cls(
            turn_id=_string(payload.get("turn_id")),
            campaign_id=_string(payload.get("campaign_id")),
            buyer_utterance_text=buyer_text,
            normalized_buyer_text=_string(payload.get("normalized_buyer_text")) or normalize_text(buyer_text),
            existing_runtime_action_id=_string(payload.get("existing_runtime_action_id")),
            existing_runtime_response_text=_string(payload.get("existing_runtime_response_text")),
            memory_summary=_string(payload.get("memory_summary")),
            known_context=known_context,
            safety_boundary_detected=payload.get("safety_boundary_detected") is True,
            previous_action_id=_string(payload.get("previous_action_id")),
            previous_answered_topic=_string(payload.get("previous_answered_topic")),
            evidence_source=_string(payload.get("evidence_source")),
        )

    def to_selector_payload(self) -> dict[str, Any]:
        context = dict(self.known_context)
        return {
            "buyer_utterance_text": self.buyer_utterance_text,
            "context": {
                "buyer_utterance_text": self.buyer_utterance_text,
                "normalized_buyer_text": self.normalized_buyer_text,
                "memory_summary": self.memory_summary,
                "known_use_case": context.get("known_use_case") or [],
                "known_tools": context.get("known_tools") or [],
                "known_plan_interest": context.get("known_plan_interest") or "",
                "known_team_status": context.get("known_team_status") or "",
                "buyer_emotion": context.get("buyer_emotion") or "",
                "buyer_confusion_level": context.get("buyer_confusion_level") or "",
                "buyer_skepticism_level": context.get("buyer_skepticism_level") or "",
                "buyer_engagement_level": context.get("buyer_engagement_level") or "",
                "last_action_id": self.previous_action_id,
                "last_answered_topic": self.previous_answered_topic,
                "safety_boundary_detected": self.safety_boundary_detected,
            },
        }

    def to_dict(self) -> dict[str, Any]:
        return {field_name: getattr(self, field_name) for field_name in SHADOW_INPUT_FIELDS}


@dataclass(frozen=True)
class ShadowModeOutput:
    selector_action_id: str
    selector_confidence: float
    selector_reasons: list[str]
    selector_matched_features: list[str]
    agreement_with_runtime: bool
    disagreement_type: str
    safety_status: str
    side_effects_allowed: bool = False
    buyer_facing_text_generated: bool = False
    live_runtime_wiring_allowed: bool = False
    should_not_change_runtime: bool = True
    fallback_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "selector_action_id": self.selector_action_id,
            "selector_confidence": round(max(0.0, min(1.0, float(self.selector_confidence))), 4),
            "selector_reasons": list(self.selector_reasons),
            "selector_matched_features": list(self.selector_matched_features),
            "agreement_with_runtime": bool(self.agreement_with_runtime),
            "disagreement_type": self.disagreement_type,
            "safety_status": self.safety_status,
            "side_effects_allowed": False,
            "buyer_facing_text_generated": False,
            "live_runtime_wiring_allowed": False,
            "should_not_change_runtime": True,
            "fallback_required": bool(self.fallback_required),
        }
