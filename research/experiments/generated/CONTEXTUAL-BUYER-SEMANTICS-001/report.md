# CONTEXTUAL-BUYER-SEMANTICS-001 Validator

- Passed: `true`
- Failure count: `0`
- Provider calls made: `false`
- Local LLM calls made: `false`

## Failures

- None

## Matrix

- Replays the same buyer phrases against different previous-agent-question contexts.
- Requires contextual semantics in the dialogue manager trace.
- Checks both final_response and tts_input_text where TTS dry-run metadata exists.
- Keeps provider and local LLM calls disabled.