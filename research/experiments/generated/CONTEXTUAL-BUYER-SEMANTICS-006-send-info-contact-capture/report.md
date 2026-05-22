# CONTEXTUAL-BUYER-SEMANTICS-006 Send Info Contact Capture

- Passed: `true`
- Failure count: `0`
- Provider calls made: `false`
- Local LLM calls made: `false`
- Raw synthetic email stored in public evidence: `false`

## Failures

- None

## Coverage

- Replays send-info request, email capture, callback-time capture, vague acknowledgement, refusal, confirmed-pain send-info, combined contact details, and invalid email-like text.
- Enforces durable send_info_state in memory without provider, email, calendar, CRM, local LLM, or PROD-102 calls.
- Redacts synthetic emails from generated public evidence.