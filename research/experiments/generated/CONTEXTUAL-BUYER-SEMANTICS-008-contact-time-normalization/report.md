# CONTEXTUAL-BUYER-SEMANTICS-008 Contact Time Normalization

- Passed: `true`
- Failure count: `0`
- Provider calls made: `false`
- Local LLM calls made: `false`
- Sends email: `false`
- Creates calendar event: `false`
- Writes CRM: `false`
- Raw synthetic email stored in public evidence: `false`

## Failures

- None

## Coverage

- Verifies email-only, callback-only, email+callback, vague callback, ASR-spelled email, invalid email-like text, workflow-review appointment time, and ordinary callback outside send-info.
- Enforces lead_followup_state with contact, callback normalization, appointment, and safety sections.
- Keeps synthetic email redacted from generated public evidence.