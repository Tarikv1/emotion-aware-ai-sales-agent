from __future__ import annotations

from dataclasses import dataclass
from typing import Any


PROVIDERS = ("none", "local_transformers", "local_llama_cpp")
MODEL_CANDIDATES = (
    "Qwen/Qwen2.5-7B-Instruct",
    "Qwen/Qwen3-8B",
    "mistralai/Mistral-7B-Instruct-v0.3",
)
PRIMARY_MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
DEFAULT_LOCAL_LLM_MODEL_PATH = "local_artifacts/models/qwen2.5-7b-instruct"
DEFAULT_LOCAL_LLM_CACHE_DIR = "local_artifacts/cache/huggingface"
DEFAULT_LOCAL_LLM_QUANTIZATION = "4bit"
DEFAULT_LOCAL_LLM_DEVICE = "cuda"
FALLBACK_MODEL_CANDIDATES = (
    "Qwen/Qwen3-8B",
    "mistralai/Mistral-7B-Instruct-v0.3",
)
ACTIVE_MODEL_COMPARISON_THIS_PHASE = False

REQUIRED_TOP_LEVEL_FIELDS = (
    "semantic_frame",
    "state_update",
    "sales_strategy",
    "response_plan",
    "draft_response",
    "safety_flags",
    "confidence",
    "reasons",
)

REQUIRED_SEMANTIC_FRAME_FIELDS = (
    "semantic_family",
    "speech_act",
    "sub_intent",
    "object_type",
    "object_mentions",
    "conjunction_relation",
    "negation_scope",
    "buyer_state",
    "buyer_emotion_hint",
    "commercial_intent",
    "current_utterance_fidelity_notes",
)

REQUIRED_STATE_UPDATE_FIELDS = (
    "should_update_adoption_state",
    "should_update_use_case",
    "use_case_values",
    "should_update_usage_intensity",
    "usage_intensity",
    "should_update_team_state",
    "should_update_recommendation",
    "should_update_close_readiness",
    "blocked_updates",
    "reason",
)

REQUIRED_SALES_STRATEGY_FIELDS = (
    "next_action",
    "should_answer_directly",
    "should_ask_question",
    "should_recommend",
    "should_reframe_objection",
    "should_close",
    "should_disqualify",
    "persuasion_strategy",
    "one_next_step",
)

REQUIRED_RESPONSE_PLAN_FIELDS = (
    "must_include",
    "must_not_include",
    "campaign_facts_needed",
    "buyer_words_to_preserve",
    "response_tone",
    "max_sentence_count",
)

REQUIRED_SAFETY_FLAG_FIELDS = (
    "needs_fact_check",
    "unsupported_product_claim_risk",
    "side_effect_claim_risk",
    "affiliation_claim_risk",
    "internal_policy_language_risk",
    "raw_url_risk",
    "campaign_leakage_risk",
)

_LIST_FIELDS = {
    "semantic_frame.object_mentions",
    "state_update.use_case_values",
    "state_update.blocked_updates",
    "response_plan.must_include",
    "response_plan.must_not_include",
    "response_plan.campaign_facts_needed",
    "response_plan.buyer_words_to_preserve",
    "reasons",
}

_BOOL_FIELDS = {
    "state_update.should_update_adoption_state",
    "state_update.should_update_use_case",
    "state_update.should_update_usage_intensity",
    "state_update.should_update_team_state",
    "state_update.should_update_recommendation",
    "state_update.should_update_close_readiness",
    "sales_strategy.should_answer_directly",
    "sales_strategy.should_ask_question",
    "sales_strategy.should_recommend",
    "sales_strategy.should_reframe_objection",
    "sales_strategy.should_close",
    "sales_strategy.should_disqualify",
    "safety_flags.needs_fact_check",
    "safety_flags.unsupported_product_claim_risk",
    "safety_flags.side_effect_claim_risk",
    "safety_flags.affiliation_claim_risk",
    "safety_flags.internal_policy_language_risk",
    "safety_flags.raw_url_risk",
    "safety_flags.campaign_leakage_risk",
}


@dataclass(frozen=True)
class LocalConversationBrainConfig:
    provider: str = "local_transformers"
    model_id: str = PRIMARY_MODEL_ID
    model_path: str = DEFAULT_LOCAL_LLM_MODEL_PATH
    cache_dir: str = DEFAULT_LOCAL_LLM_CACHE_DIR
    device: str = DEFAULT_LOCAL_LLM_DEVICE
    quantization_mode: str = DEFAULT_LOCAL_LLM_QUANTIZATION
    max_input_tokens: int = 4096
    max_output_tokens: int = 768
    timeout_ms: int = 30000
    structured_output_required: bool = True
    enabled: bool = False

    def redacted_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model_id": self.model_id,
            "model_path": self.model_path,
            "cache_dir": self.cache_dir,
            "device": self.device,
            "quantization_mode": self.quantization_mode,
            "max_input_tokens": self.max_input_tokens,
            "max_output_tokens": self.max_output_tokens,
            "timeout_ms": self.timeout_ms,
            "structured_output_required": self.structured_output_required,
            "enabled": self.enabled,
            "requires_provider_secret": False,
            "provider_secret_logged": False,
        }


def validate_local_conversation_brain_config(config: LocalConversationBrainConfig) -> list[str]:
    errors: list[str] = []
    if config.provider not in PROVIDERS:
        errors.append(f"provider must be one of {list(PROVIDERS)}, got {config.provider!r}")
    if config.enabled and config.provider == "none":
        errors.append("enabled local conversation brain cannot use provider='none'")
    if config.model_id != PRIMARY_MODEL_ID:
        errors.append(f"this phase only supports primary model {PRIMARY_MODEL_ID!r}")
    for field_name in ("model_path", "cache_dir"):
        value = getattr(config, field_name)
        if not isinstance(value, str) or not value:
            errors.append(f"{field_name} must be a non-empty project-relative path")
            continue
        normalized = value.replace("\\", "/")
        if normalized.startswith("/") or ":" in normalized or ".." in normalized.split("/"):
            errors.append(f"{field_name} must be project-relative and not absolute: {value!r}")
    if config.quantization_mode not in {"4bit", "8bit", "none"}:
        errors.append("quantization_mode must be one of '4bit', '8bit', or 'none'")
    if config.device not in {"cuda", "cpu", "auto"}:
        errors.append("device must be one of 'cuda', 'cpu', or 'auto'")
    if config.max_input_tokens <= 0:
        errors.append("max_input_tokens must be positive")
    if config.max_output_tokens <= 0:
        errors.append("max_output_tokens must be positive")
    if config.timeout_ms <= 0:
        errors.append("timeout_ms must be positive")
    if not isinstance(config.structured_output_required, bool):
        errors.append("structured_output_required must be boolean")
    if not isinstance(config.enabled, bool):
        errors.append("enabled must be boolean")
    return errors


def _section_errors(
    payload: dict[str, Any],
    section_name: str,
    required_fields: tuple[str, ...],
) -> list[str]:
    errors: list[str] = []
    section = payload.get(section_name)
    if not isinstance(section, dict):
        return [f"{section_name} must be an object"]
    actual = set(section)
    required = set(required_fields)
    missing = sorted(required - actual)
    extra = sorted(actual - required)
    if missing:
        errors.append(f"{section_name} missing required field(s): {missing}")
    if extra:
        errors.append(f"{section_name} has unsupported field(s): {extra}")
    for key, value in section.items():
        dotted = f"{section_name}.{key}"
        if dotted in _LIST_FIELDS:
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                errors.append(f"{dotted} must be a list of strings")
        elif dotted in _BOOL_FIELDS:
            if not isinstance(value, bool):
                errors.append(f"{dotted} must be boolean")
        elif dotted == "response_plan.max_sentence_count":
            if not isinstance(value, int) or value < 1:
                errors.append("response_plan.max_sentence_count must be a positive integer")
        elif not isinstance(value, str):
            errors.append(f"{dotted} must be a string")
    return errors


def validate_conversation_brain_output(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["planner output must be an object"]

    actual = set(payload)
    required = set(REQUIRED_TOP_LEVEL_FIELDS)
    missing = sorted(required - actual)
    extra = sorted(actual - required)
    if missing:
        errors.append(f"missing required top-level field(s): {missing}")
    if extra:
        errors.append(f"unsupported top-level field(s): {extra}")

    errors.extend(_section_errors(payload, "semantic_frame", REQUIRED_SEMANTIC_FRAME_FIELDS))
    errors.extend(_section_errors(payload, "state_update", REQUIRED_STATE_UPDATE_FIELDS))
    errors.extend(_section_errors(payload, "sales_strategy", REQUIRED_SALES_STRATEGY_FIELDS))
    errors.extend(_section_errors(payload, "response_plan", REQUIRED_RESPONSE_PLAN_FIELDS))
    errors.extend(_section_errors(payload, "safety_flags", REQUIRED_SAFETY_FLAG_FIELDS))

    draft_response = payload.get("draft_response")
    if not isinstance(draft_response, str) or not draft_response.strip():
        errors.append("draft_response must be a non-empty string")

    reasons = payload.get("reasons")
    if not isinstance(reasons, list) or not reasons or not all(isinstance(item, str) and item for item in reasons):
        errors.append("reasons must be a non-empty list of strings")

    confidence = payload.get("confidence")
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
        errors.append("confidence must be a number")
    elif confidence < 0.0 or confidence > 1.0:
        errors.append("confidence must be between 0.0 and 1.0")

    return errors
