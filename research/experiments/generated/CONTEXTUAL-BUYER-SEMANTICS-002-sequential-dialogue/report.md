# CONTEXTUAL-BUYER-SEMANTICS-002 Sequential Dialogue Validator

- Passed: `true`
- Failure count: `0`
- Provider calls made: `false`
- Local LLM calls made: `false`

## Failures

- None

## Sequential Coverage

- Replays live-demo turn packets from an empty state.
- Appends each returned packet before the next buyer turn.
- Checks semantic frame, manager source, memory, call control, final_response, and tts_input_text.
- Keeps provider calls, live TTS, local LLMs, and PROD-102 disabled.