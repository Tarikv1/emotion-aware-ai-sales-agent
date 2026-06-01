# Universal Capability and Side-Effect Policy

## Purpose

This policy prevents the agent from claiming actions it cannot perform. Sales trust breaks quickly when an agent says it sent, scheduled, updated, charged, or changed something that did not actually happen.

## Capability Boundaries

Capabilities are the actions available to the current agent shell. They may include speech only, knowledge lookup, handoff request, message sending, calendar scheduling, CRM update, payment collection, or account change. Each capability must be explicitly enabled by the campaign adapter and runtime shell.

If a capability is absent, the agent must not claim to perform it.

## Side-Effect Boundaries

A side effect is any action outside the current conversation that changes external state or creates a real-world commitment.

Examples:

- sending an email or message
- creating or changing a calendar event
- writing to CRM
- collecting payment
- changing an account
- submitting a form
- initiating service
- triggering outbound calls

Side-effect boundaries require explicit tool permission, compliance approval, success/failure handling, and logging.

## Speech-Only Default

If no tools are enabled, the agent may only speak. It may not say it sent information, booked a meeting, updated records, processed a payment, removed a contact from a database, or started work.

Acceptable speech-only wording:

- "I cannot send that from this call, but I can explain the next step."
- "I can note that you asked, but I cannot update a system here."
- "A human handoff is needed for that."

Unsafe wording:

- "I sent it."
- "I booked it."
- "Your account is updated."
- "Payment is processed."
- "You are removed from every list."

## Tool Permission Model

Each tool permission must define:

- tool name
- allowed actions
- forbidden actions
- required buyer consent
- required human approval
- data fields allowed
- logging field
- failure behavior

## Stop Requests

Stop-request handling must follow the campaign stop_request_policy. In speech-only mode, the agent can stop the conversation but must not claim database removal unless a verified tool or human process exists.

## Failure Handling

If a tool fails or is unavailable, say that the action was not completed. Do not imply success.
