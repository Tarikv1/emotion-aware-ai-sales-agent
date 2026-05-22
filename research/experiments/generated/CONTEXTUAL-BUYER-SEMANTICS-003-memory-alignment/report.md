# CONTEXTUAL-BUYER-SEMANTICS-003 Memory Alignment Validator

- Passed: `true`
- Failure count: `0`
- Provider calls made: `false`
- Local LLM calls made: `false`

## Failures

- None

## Coverage

- Replays real live-demo turn packets from empty state.
- Checks semantic frame, manager source, memory, call control, final_response, and tts_input_text.
- Guards contextual semantics against older callback/workflow memory pollution.
- Adds multi-gap diagnostic scope expectations for the broad fit-check question.