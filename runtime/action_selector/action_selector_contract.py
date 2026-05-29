from __future__ import annotations

from dataclasses import dataclass, field
import json
import re
from pathlib import Path
from typing import Any


CONTRACT_VERSION = "NON-LLM-ACTION-SELECTOR-CONTRACT-001"
LABELS_PATH = Path(__file__).resolve().parent / "action_selector_labels.json"

INPUT_FIELDS: tuple[str, ...] = (
    "buyer_utterance_text",
    "normalized_buyer_text",
    "memory_summary",
    "known_use_case",
    "known_tools",
    "known_plan_interest",
    "known_team_status",
    "buyer_emotion",
    "buyer_confusion_level",
    "buyer_skepticism_level",
    "buyer_engagement_level",
    "last_action_id",
    "last_answered_topic",
    "safety_boundary_detected",
)

OUTPUT_FIELDS: tuple[str, ...] = (
    "action_id",
    "confidence",
    "reasons",
    "matched_features",
    "requires_clarification",
    "safety_block",
    "fallback_required",
    "side_effects_allowed",
    "live_runtime_wiring_allowed",
)


def normalize_text(value: Any) -> str:
    text = re.sub(r"[^a-z0-9+/#.]+", " ", str(value or "").casefold())
    return " ".join(text.split())


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item or "").strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


@dataclass(frozen=True)
class ActionSelectorInput:
    buyer_utterance_text: str
    normalized_buyer_text: str = ""
    memory_summary: str = ""
    known_use_case: list[str] = field(default_factory=list)
    known_tools: list[str] = field(default_factory=list)
    known_plan_interest: str = ""
    known_team_status: str = ""
    buyer_emotion: str = ""
    buyer_confusion_level: str = ""
    buyer_skepticism_level: str = ""
    buyer_engagement_level: str = ""
    last_action_id: str = ""
    last_answered_topic: str = ""
    safety_boundary_detected: bool = False

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "ActionSelectorInput":
        buyer_text = str(payload.get("buyer_utterance_text") or "")
        normalized = str(payload.get("normalized_buyer_text") or "").strip() or normalize_text(buyer_text)
        return cls(
            buyer_utterance_text=buyer_text,
            normalized_buyer_text=normalized,
            memory_summary=str(payload.get("memory_summary") or ""),
            known_use_case=_string_list(payload.get("known_use_case")),
            known_tools=_string_list(payload.get("known_tools")),
            known_plan_interest=str(payload.get("known_plan_interest") or ""),
            known_team_status=str(payload.get("known_team_status") or ""),
            buyer_emotion=str(payload.get("buyer_emotion") or ""),
            buyer_confusion_level=str(payload.get("buyer_confusion_level") or ""),
            buyer_skepticism_level=str(payload.get("buyer_skepticism_level") or ""),
            buyer_engagement_level=str(payload.get("buyer_engagement_level") or ""),
            last_action_id=str(payload.get("last_action_id") or ""),
            last_answered_topic=str(payload.get("last_answered_topic") or ""),
            safety_boundary_detected=payload.get("safety_boundary_detected") is True,
        )

    def feature_text(self) -> str:
        parts = [
            self.normalized_buyer_text,
            self.memory_summary,
            " ".join(self.known_use_case),
            " ".join(self.known_tools),
            self.known_plan_interest,
            self.known_team_status,
            self.buyer_emotion,
            self.buyer_confusion_level,
            self.buyer_skepticism_level,
            self.buyer_engagement_level,
            self.last_action_id,
            self.last_answered_topic,
            "safety_boundary_detected" if self.safety_boundary_detected else "",
        ]
        return " ".join(part for part in parts if part).strip()

    def to_dict(self) -> dict[str, Any]:
        return {field_name: getattr(self, field_name) for field_name in INPUT_FIELDS}


@dataclass(frozen=True)
class ActionSelectorOutput:
    action_id: str
    confidence: float
    reasons: list[str] = field(default_factory=list)
    matched_features: list[str] = field(default_factory=list)
    requires_clarification: bool = False
    safety_block: bool = False
    fallback_required: bool = False
    side_effects_allowed: bool = False
    live_runtime_wiring_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "confidence": round(max(0.0, min(1.0, float(self.confidence))), 4),
            "reasons": list(self.reasons),
            "matched_features": list(self.matched_features),
            "requires_clarification": bool(self.requires_clarification),
            "safety_block": bool(self.safety_block),
            "fallback_required": bool(self.fallback_required),
            "side_effects_allowed": False,
            "live_runtime_wiring_allowed": False,
        }


def load_action_label_payload() -> dict[str, Any]:
    payload = json.loads(LABELS_PATH.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def action_labels() -> dict[str, dict[str, Any]]:
    labels = load_action_label_payload().get("labels")
    if not isinstance(labels, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for item in labels:
        if isinstance(item, dict) and isinstance(item.get("action_id"), str):
            result[item["action_id"]] = item
    return result


def allowed_action_ids() -> tuple[str, ...]:
    return tuple(action_labels())


def validate_selector_output(output: ActionSelectorOutput | dict[str, Any]) -> list[str]:
    payload = output.to_dict() if isinstance(output, ActionSelectorOutput) else dict(output)
    failures: list[str] = []
    action_id = payload.get("action_id")
    if action_id not in action_labels():
        failures.append(f"action_id_not_controlled:{action_id}")
    for key in ("side_effects_allowed", "live_runtime_wiring_allowed"):
        if payload.get(key) is not False:
            failures.append(f"{key}_must_be_false")
    forbidden_text_keys = {"say", "response_text", "buyer_facing_response", "draft_response"}
    extra_text_keys = sorted(forbidden_text_keys & set(payload))
    if extra_text_keys:
        failures.append(f"selector_output_contains_buyer_facing_text:{extra_text_keys}")
    return failures
