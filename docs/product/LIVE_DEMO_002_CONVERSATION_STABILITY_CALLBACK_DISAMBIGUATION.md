# LIVE-DEMO-002 Conversation Stability Callback Disambiguation

`LIVE-DEMO-002-conversation-stability-callback-disambiguation` is a narrow live-demo stability checkpoint. It does not open `PROD-102`, promote production use, add payment collection, create a provider-hosted agent, enable voice cloning, or make LLM/retrieval behavior production-default.

## Goal

Make the supervised live demo more stable across many turns while preserving the runtime-owned spoken path:

- distinguish callback workflow gaps from callback scheduling requests
- preserve useful session memory without a database
- reduce repeated final responses and repeated diagnostic question types
- reduce customer sentence echoing before speech/TTS
- keep the agent seller-led: answer, clarify, or steer toward a sale-adjacent next step
- keep LLM enrichment optional, asynchronous, and unable to mutate final speech or protected route fields

## Active Runtime Path

The active spoken demo path is:

`scripts/run_live_demo_001_agent_voice_call.py::build_turn_packet(...)`

That path calls runtime-owned policy helpers in:

- `runtime/core/live_voice_session_policy.py`
- `runtime/speech/asr_quality_gate.py`
- `runtime/contracts/voice_turn_state_contract.py`
- `runtime/core/dialogue_reasoner.py`
- `runtime/core/dialogue_reasoner_async_enrichment.py`

Legacy duplicate helper functions still exist inside the live-demo runner, but this checkpoint does not patch them as the active behavior source. The live HTTP session handler now preserves full in-memory turns for the session instead of truncating to the last 8 turns.

## Behavior Changes

Intentional behavior changes:

- `callback_workflow_gap`: bare `callback`/`callbacks`, missed callbacks, callback reminders, missed follow-ups, and callback-definition questions are treated as workflow/product gaps, not scheduling.
- `callback_scheduling_request`: explicit later-call requests such as `call me back later`, `can you call me tomorrow`, and `not now, call me later` ask for a callback time.
- `callback_time_confirmation`: concrete callback times such as `tomorrow at 3 works` confirm scheduling and end safely.
- `conversation_memory`: private packets now expose compact `demo_conversation_memory` with active topic/stage, selected gap, callback semantic, question counts, answered/rejected topics, response hashes, and last sales progression step.
- `pre_speech_conversation_stability_guard`: final candidate speech is checked before voice delivery for duplicate responses, generic menu reopening, repeated question type, callback semantic mismatch, and leading customer echo.
- `DIALOGUE-REASONER-004` completion now records provider latency while treating timeout/provider/schema failures as ignored enrichment, not failed live turns.
- OpenAI-compatible reasoner temperature defaults to `1.0`, matching the working provider path that required non-zero temperature; it remains configurable.

## Evidence

Generated evidence:

- `research/experiments/generated/LIVE-DEMO-002-conversation-stability-callback-disambiguation/result.json`
- `research/experiments/generated/LIVE-DEMO-002-conversation-stability-callback-disambiguation/report.md`
- `research/experiments/generated/LIVE-DEMO-002-conversation-stability-callback-disambiguation/llm_enrichment_benchmark.json`

Validator:

```powershell
python scripts\validate_live_demo_002_conversation_stability.py
```

Optional benchmark scaffold:

```powershell
python scripts\run_live_demo_002_llm_enrichment_benchmark.py
```

The validator runs provider-off by default. It uses fixed 12-turn and 27-turn scenarios as samples only; they are not runtime caps.

## Acceptance

This checkpoint passes only if:

- bare callback terms no longer trigger scheduling
- workflow callback mentions map to workflow value or callback explanation
- explicit later-call requests still schedule
- concrete callback times still confirm and end
- multi-turn samples do not replay final responses or generic focus menus
- customer phrase echoing is suppressed before speech
- seller-led responses keep moving toward a workflow review, written summary, specialist handoff where required, or later callback where requested
- async LLM enrichment does not block the customer response, mutate final text, override protected route labels, override call control, override safety boundaries, or alter voice delivery
- provider calls remain disabled by default in validation
