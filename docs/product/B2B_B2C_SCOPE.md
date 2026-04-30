# B2B And B2C Product Scope

## Purpose

Clarify that the emotion-aware AI sales agent is not limited to selling to companies.

The product should support both:

- `B2B`: selling to business contacts, teams, departments, or company decision-makers
- `B2C`: selling directly to individual consumers

The first simulation set is B2B-leaning, but that is a starting slice, not the full product definition.

The product is also not limited to one vertical such as insurance. Insurance is the first known client example; the product should be configurable for many call-center sales campaigns.

## Shared Core

Both B2B and B2C versions need the same core loop:

```text
customer or lead context
  -> consent / permission to continue
  -> relevance or need check
  -> pain point / motivation check
  -> interest and readiness estimate
  -> strategy selection
  -> schedule, close politely, escalate, or suppress contact
  -> structured outcome logging
```

The same compact states still apply:

- `interested`
- `maybe-interested`
- `not-interested`
- `needs-human`
- `do-not-call`

The same compact emotion labels still apply:

- `positive`
- `neutral`
- `skeptical-or-negative`

## B2B Differences

B2B conversations often involve:

- company role and decision authority
- team workflow
- budget and timing
- integration or procurement questions
- wrong-contact and referral paths
- scheduling with a human sales specialist

Example B2B question:

`Are you currently involved in handling follow-up for incoming leads or customer inquiries?`

## B2C Differences

B2C conversations often involve:

- personal need or preference
- household or individual budget
- urgency or life situation
- trust, privacy, and pressure sensitivity
- product fit for one person rather than a team
- scheduling a consultation, callback, demo, or service appointment

Example B2C question:

`Is this something you were personally looking into, or would it be more of a future consideration?`

First known B2C vertical:

- German outbound insurance sales through a call center
- examples: dental insurance and cancer-related or serious-illness insurance
- this should be treated as a sensitive B2C context with stronger compliance and pressure-avoidance guardrails

Other possible B2C verticals include home improvement products, glasses, consumer electronics, service subscriptions, or retail products such as SD cards.

## B2C Guardrails

B2C selling can be more sensitive because the agent may be speaking to individual consumers rather than professional buyers.

The agent should:

- avoid pressure tactics
- avoid exploiting anxiety, urgency, or vulnerability
- avoid unsupported savings, health, legal, or financial claims
- make it easy to decline
- respect do-not-call requests immediately
- escalate when the customer sounds confused, distressed, angry, or asks for a human
- follow stricter privacy and consent rules for personal information

## Simulation Implication

`PROD-001` should remain the first B2B-leaning qualification and appointment-setting simulation.

The next harder product case set should be mixed:

- B2B lead qualification cases
- B2C direct-customer qualification cases
- ambiguous cases where it is not initially clear whether the caller is a business or individual consumer

Suggested next case set:

`PROD-002-mixed-b2b-b2c-insurance.json`

After that, add a generic mixed-vertical set so the product does not overfit to insurance:

`PROD-003-mixed-consumer-products.json`

## Database Implication

Lead records should include a `customer_type` field:

- `b2b`
- `b2c`
- `unknown`

B2B records may use company and role fields.

B2C records may leave company and role empty and instead rely on:

- full name
- phone number
- region
- language
- consent status
- qualification answers
- call outcome

## Product Positioning

A better product description is:

`An emotion-aware autonomous sales agent that qualifies potential customers, adapts to their conversational state, and either schedules an appropriate human follow-up or records a safe outcome.`

This keeps both B2B and B2C paths open.
