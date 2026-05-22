# CONTEXTUAL-BUYER-SEMANTICS-005 Outgoing Question State

- Passed: `true`
- Failure count: `0`
- Provider calls made: `false`
- Local LLM calls made: `false`

## Failures

- None

## Coverage

- Replays permission acknowledgement into the standard three-gap diagnostic from empty state.
- Enforces outgoing_question_type, outgoing_active_gap_scope, and outgoing_candidate_gaps in memory.
- Verifies the next buyer turn uses the outgoing diagnostic scope for all-clear, specific-clear, and mixed responses.
- Checks final_response and tts_input_text for matching diagnostic or appointment focus.