# CONTEXTUAL-BUYER-SEMANTICS-009 Right Person Handoff

- Passed: `true`
- Failure count: `0`
- Provider calls made: `false`
- Local LLM calls made: `false`
- Sends email: `false`
- Creates calendar event: `false`
- Writes CRM: `false`
- Raw synthetic emails stored in public evidence: `false`

## Failures

- None

## Coverage

- Verifies wrong-person, department, named person, right-person email, department plus email, right-person callback time, refusal, explicit stop, send-info to manager, and contact-vs-product-routing separation.
- Verifies the outgoing diagnostic trace exposes callbacks, manual tracking, and handoffs when the spoken response asks all three.
- Keeps synthetic right-person contact details redacted from generated public evidence.