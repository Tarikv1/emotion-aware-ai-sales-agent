# NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-POINTS-001

- Status: pass
- Safest current output: an unwired disabled hook stub in `runtime/action_selector/shadow_runtime_hook.py`.
- Safest existing observation point for offline/replay comparison: `runtime/core/realtime_turns.py::run_case`.
- Richest future runtime observation point: after `runtime/core/contextual_buyer_semantics.py::classify_contextual_buyer_semantics` returns a semantic frame.
- Live runtime wiring allowed: false
- Runtime behavior changed: false
- Response text changed: false
- Provider/local model calls: false

## Recommendation

Implement design-only and disabled-by-default instrumentation in this phase. Do not import the hook into live runtime yet. Before real runtime comparison, add explicit runtime action metadata extraction so `existing_runtime_action_id` is available without deriving it from response text.

## Candidate Points

- `runtime/core/realtime_turns.py::run_case`: low risk, replay-only, has `runtime_decision` and expected runtime data. Best for offline evidence.
- `runtime/core/realtime_turns.py::build_runtime_decision`: medium risk, has response/action metadata after the runtime decision is built. Future read-only hook only.
- `runtime/core/contextual_buyer_semantics.py::classify_contextual_buyer_semantics`: high information, high risk. It sees transcript, session turns, campaign, semantic `action_id`, and `candidate_response`; only consider after disabled import validation.
- `runtime/campaigns/public_openai_chatgpt_plans_dialogue.py::classify_turn`: campaign-specific and useful, but not generic enough as the first hook point.
- `runtime/core/live_voice_session_policy.py`: not recommended. It is response-generation-adjacent and lacks one stable turn context.
