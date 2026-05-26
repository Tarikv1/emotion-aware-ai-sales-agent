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
    return LocalConversationBrainConfig(model_id=PRIMARY_MODEL_ID)


def local_llm_experiment_enabled() -> bool:
    return os.getenv(EXPERIMENT_ENV_VAR) == "1"


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
    if not local_llm_experiment_enabled():
        return ConversationBrainResult(
            status="skipped_env_disabled",
            config=resolved_config.redacted_dict(),
            prompt_rendered=bool(prompt),
            inference_attempted=False,
            local_model_calls_made=False,
            provider_calls_made=False,
            planner_output=None,
            errors=[f"{EXPERIMENT_ENV_VAR}=1 is required before local model inference"],
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
