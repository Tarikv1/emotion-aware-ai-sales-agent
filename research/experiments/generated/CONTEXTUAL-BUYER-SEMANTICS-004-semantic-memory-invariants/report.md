# CONTEXTUAL-BUYER-SEMANTICS-004 Semantic Memory Invariants

- Passed: `true`
- Failure count: `0`
- Provider calls made: `false`
- Local LLM calls made: `false`

## Failures

- None

## Coverage

- Replays mixed, pain, multi-gap-clear, and specific-clear turns from empty state.
- Enforces that applied contextual semantics own memory intent, selected gap, callback semantic, and active topic.
- Checks final_response and tts_input_text for the same semantic focus.