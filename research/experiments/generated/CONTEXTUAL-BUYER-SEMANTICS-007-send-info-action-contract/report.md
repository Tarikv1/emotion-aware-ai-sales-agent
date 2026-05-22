# CONTEXTUAL-BUYER-SEMANTICS-007 Send Info Action Contract

- Passed: `true`
- Failure count: `0`
- Provider calls made: `false`
- Local LLM calls made: `false`
- Raw synthetic email stored in public evidence: `false`

## Failures

- None

## Coverage

- Verifies send-info request, email capture, callback-time capture, vague acknowledgement, refusal, confirmed-pain send-info, combined contact capture, and unclear contact all use explicit send-info action/template IDs.
- Verifies ordinary callback outside send-info does not get forced into send-info action IDs.
- Keeps synthetic email redacted from generated public evidence.