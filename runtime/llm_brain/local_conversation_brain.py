from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any

from runtime.llm_brain.conversation_brain_prompts import render_conversation_brain_prompt
from runtime.llm_brain.conversation_brain_schema import (
    LocalConversationBrainConfig,
    PRIMARY_MODEL_ID,
    validate_conversation_brain_output,
    validate_local_conversation_brain_config,
)


EXPERIMENT_ENV_VAR = "ENABLE_LOCAL_LLM_BRAIN_EXPERIMENT"
LOCAL_LLM_ENABLED_ENV_VAR = "LOCAL_LLM_ENABLED"
LOCAL_LLM_MODEL_ID_ENV_VAR = "LOCAL_LLM_MODEL_ID"
LOCAL_LLM_MODEL_PATH_ENV_VAR = "LOCAL_LLM_MODEL_PATH"
LOCAL_LLM_CACHE_DIR_ENV_VAR = "LOCAL_LLM_CACHE_DIR"
LOCAL_LLM_QUANTIZATION_ENV_VAR = "LOCAL_LLM_QUANTIZATION"
LOCAL_LLM_DEVICE_ENV_VAR = "LOCAL_LLM_DEVICE"


def _env_flag(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class ConversationBrainRequest:
    normalized_transcript: str
    prior_state: dict[str, Any]
    approved_campaign_fact_ids: list[str]
    last_agent_question: str = ""
    campaign_id: str = ""

    def prompt_context(self) -> dict[str, Any]:
        return {
            "normalized_transcript": self.normalized_transcript,
            "prior_state": self.prior_state,
            "approved_campaign_fact_ids": self.approved_campaign_fact_ids,
            "last_agent_question": self.last_agent_question,
            "campaign_id": self.campaign_id,
        }


@dataclass(frozen=True)
class ConversationBrainResult:
    status: str
    config: dict[str, Any]
    prompt_rendered: bool
    inference_attempted: bool
    local_model_calls_made: bool
    provider_calls_made: bool
    planner_output: dict[str, Any] | None
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "config": self.config,
            "prompt_rendered": self.prompt_rendered,
            "inference_attempted": self.inference_attempted,
            "local_model_calls_made": self.local_model_calls_made,
            "provider_calls_made": self.provider_calls_made,
            "planner_output": self.planner_output,
            "errors": self.errors,
        }


def default_local_conversation_brain_config() -> LocalConversationBrainConfig:
    return LocalConversationBrainConfig()


def local_conversation_brain_config_from_env(
    env: dict[str, str] | os._Environ[str] | None = None,
) -> LocalConversationBrainConfig:
    source = env if env is not None else os.environ
    defaults = default_local_conversation_brain_config()
    return LocalConversationBrainConfig(
        provider="local_transformers",
        model_id=source.get(LOCAL_LLM_MODEL_ID_ENV_VAR, defaults.model_id),
        model_path=source.get(LOCAL_LLM_MODEL_PATH_ENV_VAR, defaults.model_path),
        cache_dir=source.get(LOCAL_LLM_CACHE_DIR_ENV_VAR, defaults.cache_dir),
        device=source.get(LOCAL_LLM_DEVICE_ENV_VAR, defaults.device),
        quantization_mode=source.get(LOCAL_LLM_QUANTIZATION_ENV_VAR, defaults.quantization_mode),
        max_input_tokens=defaults.max_input_tokens,
        max_output_tokens=defaults.max_output_tokens,
        timeout_ms=defaults.timeout_ms,
        structured_output_required=defaults.structured_output_required,
        enabled=_env_flag(source.get(LOCAL_LLM_ENABLED_ENV_VAR)),
    )


def local_llm_experiment_enabled() -> bool:
    return _env_flag(os.getenv(EXPERIMENT_ENV_VAR))


def local_llm_enabled() -> bool:
    return _env_flag(os.getenv(LOCAL_LLM_ENABLED_ENV_VAR))


def plan_with_local_conversation_brain(
    request: ConversationBrainRequest,
    *,
    config: LocalConversationBrainConfig | None = None,
    fixture_output: dict[str, Any] | None = None,
) -> ConversationBrainResult:
    resolved_config = config or default_local_conversation_brain_config()
    config_errors = validate_local_conversation_brain_config(resolved_config)
    if config_errors:
        return ConversationBrainResult(
            status="invalid_config",
            config=resolved_config.redacted_dict(),
            prompt_rendered=False,
            inference_attempted=False,
            local_model_calls_made=False,
            provider_calls_made=False,
            planner_output=None,
            errors=config_errors,
        )

    if fixture_output is not None:
        return ConversationBrainResult(
            status="fixture_output",
            config=resolved_config.redacted_dict(),
            prompt_rendered=False,
            inference_attempted=False,
            local_model_calls_made=False,
            provider_calls_made=False,
            planner_output=fixture_output,
            errors=validate_conversation_brain_output(fixture_output),
        )

    if not resolved_config.enabled or resolved_config.provider == "none":
        return ConversationBrainResult(
            status="disabled",
            config=resolved_config.redacted_dict(),
            prompt_rendered=False,
            inference_attempted=False,
            local_model_calls_made=False,
            provider_calls_made=False,
            planner_output=None,
            errors=[],
        )

    prompt = render_conversation_brain_prompt(request.prompt_context())
    if not local_llm_experiment_enabled() or not local_llm_enabled():
        return ConversationBrainResult(
            status="skipped_env_disabled",
            config=resolved_config.redacted_dict(),
            prompt_rendered=bool(prompt),
            inference_attempted=False,
            local_model_calls_made=False,
            provider_calls_made=False,
            planner_output=None,
            errors=[
                f"{EXPERIMENT_ENV_VAR}=1 and {LOCAL_LLM_ENABLED_ENV_VAR}=true are required before local model inference"
            ],
        )

    if resolved_config.provider == "local_transformers":
        from runtime.llm_brain.local_transformers_runner import run_single_conversation_brain_case

        run_result = run_single_conversation_brain_case(
            config=resolved_config,
            request_context=request.prompt_context(),
            case={"sanitized_buyer_text": request.normalized_transcript},
            allow_model_download=False,
        )
        errors = [*run_result.errors, *run_result.schema_errors, *run_result.verifier_errors]
        return ConversationBrainResult(
            status=run_result.status,
            config=resolved_config.redacted_dict(),
            prompt_rendered=run_result.prompt_rendered,
            inference_attempted=run_result.inference_attempted,
            local_model_calls_made=run_result.local_model_calls_made,
            provider_calls_made=False,
            planner_output=run_result.planner_output,
            errors=errors,
        )

    return ConversationBrainResult(
        status="skipped_provider_placeholder",
        config=resolved_config.redacted_dict(),
        prompt_rendered=bool(prompt),
        inference_attempted=False,
        local_model_calls_made=False,
        provider_calls_made=False,
        planner_output=None,
        errors=[
            "local_transformers and local_llama_cpp are placeholder providers in this phase; "
            "run scripts/run_local_llm_conversation_brain_smoke_001.py for explicit local-only smoke tests"
        ],
    )
