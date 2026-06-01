# Internal Architecture Mapping Reference

This file is not uploadable.

## Mapping

4O2 internal fulfillment modes still exist.

4O2A only changes buyer-facing render wording. It does not change live behavior, runtime behavior, provider behavior, or tool availability.

manual_human_followup_allowed maps to natural future follow-up language such as:

- "We can send the mockup over."
- "What email should we use?"
- "We'll be in touch."
- "I can call back."

Completed-action claims still require actual completion.

Internal 4O2 wording:

- `manual_human_followup_allowed`
- `tool_success`
- `planned_future`

Buyer-facing 4O2A wording:

- The agency can follow up manually after the call.
- Do not say something has already been sent, booked, created, updated, or paid unless it has actually happened.
- You can discuss the next step and collect the right details, but do not pretend an email, appointment, record update, payment, or mockup has already happened.

No tools are enabled by this phase. No email, calendar, CRM, payment, provider, model, TTS, API, account, or autonomous outbound path was called or enabled.
