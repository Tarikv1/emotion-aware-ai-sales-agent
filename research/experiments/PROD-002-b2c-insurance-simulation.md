# PROD-002: B2C Insurance Campaign Simulation

## Status

Ready for simulation

## Source Label

`product-synthetic`

## Date

2026-04-30

## Campaign

- Campaign ID: `campaign-prod-002-b2c-insurance`
- Client: `Synthetic German Call Center`
- Product: `Dental insurance and serious-illness protection`
- Category: `insurance`
- Customer type: `b2c`
- Country or region: `DE`
- Language: `de`

## Question

Can the reusable sales-agent core handle a strict German B2C insurance campaign through the same turn-based simulation pipeline used for the earlier B2B-leaning set?

## Scope

This case set focuses on the first real vertical context without changing the product boundary.

The reusable core stays the same:

- permission to continue
- interest detection
- strategy selection
- scheduling or escalation
- structured logging

The campaign layer changes:

- approved opening
- qualification questions
- guardrails
- escalation triggers
- human handoff role

## Dataset

- Name: PROD-002 B2C insurance campaign cases
- Source: project-authored synthetic product scenarios
- License/usage notes: internal research/product planning artifact
- Size: 8 cases
- Language: German-oriented synthetic call dialogue
- Labels: compact emotion label, expected interest state, compact strategy label, expected `CallOutcome`

## Guardrail Focus

The campaign enforces stricter insurance rules:

- no fear pressure
- no coverage, payout, or savings promises
- no medical or legal advice
- no unnecessary sensitive data collection
- detailed policy or health questions go to a human specialist

## Results

Packet generation completed:

- `research/experiments/generated/PROD-002-evaluation-packet.md`

Database-shaped export completed:

- `research/experiments/generated/PROD-002-db-records.json`

SQLite import completed:

- `research/experiments/generated/PROD-002.sqlite`
- `research/experiments/generated/PROD-002-sqlite-report.md`

Validation completed:

- `scripts/validate_prod_002_campaign.py`

Observed table counts:

- Leads: 8
- Call sessions: 8
- Qualification answers: 15
- Turn decisions: 15
- Call outcomes: 8
- Appointments: 1
- Escalations: 3

## Notes

This set intentionally mixes:

- clear dental insurance interest
- existing coverage and disinterest
- coverage-guarantee escalation
- serious-illness discomfort
- explicit do-not-call
- information-first interest
- vague callback timing
- health-related policy escalation

## Decision

Keep.

Reason:

This proves the campaign-wrapper path works and keeps the insurance case set isolated from the reusable product core.

## Next Step

Use the same campaign-wrapper pattern for a broader `PROD-003` set covering more generic consumer products and at least one B2B campaign.
