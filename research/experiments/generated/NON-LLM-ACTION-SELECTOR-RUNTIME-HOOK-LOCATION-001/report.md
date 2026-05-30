# NON-LLM-ACTION-SELECTOR-RUNTIME-HOOK-LOCATION-001

- Status: pass
- Selected file/function: runtime/campaigns/public_openai_chatgpt_plans_dialogue.py::_frame
- Selected call site: _observe_action_selector_shadow_frame(frame) inside _frame after final frame construction
- Default env-disabled behavior: Fast no-op: no selector run, no file write, no record, no runtime output change.
- Safety blockers: 0
- Runtime behavior changed: false
- Response text changed: false
- Selector control allowed: false
- Live wiring allowed: false

## Why Selected

- The campaign _frame helper is reached only after the campaign response frame has been selected.
- It has buyer utterance metadata, normalized text, semantic family, action_id, candidate_response, dialogue focus, and campaign id.
- The hook result can be ignored without changing response text, memory, call control, TTS, provider calls, or side effects.

## Alternatives

- runtime/core/contextual_buyer_semantics.py::classify_contextual_buyer_semantics: rejected - broader cross-campaign semantic router; higher blast radius than the public OpenAI campaign adapter.
- runtime/core/realtime_turns.py::build_runtime_decision: rejected - runtime harness includes background-module/call-control decisions and side-effect labels; not the narrow campaign post-decision location.
- runtime/action_selector/shadow_runtime_hook.py::maybe_log_action_selector_shadow_turn: supporting hook only - safe import target, but not a runtime observation point by itself.
- runtime/action_selector/runtime_action_metadata_extractor.py::extract_runtime_action_metadata: supporting extractor only - extracts metadata from a supplied runtime result but should not decide where runtime observation occurs.
