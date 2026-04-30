# PROD-003: Mixed Campaign Simulation

## Status

Ready for simulation

## Source Label

`product-synthetic`

## Date

2026-04-30

## Campaigns

- `campaign-prod-003-windows-home-improvement`: `Replacement windows consultation` / `home-improvement` / `b2c` / `DE`
- `campaign-prod-003-glasses-eyewear`: `Glasses and eyewear options` / `health-or-wellness` / `b2c` / `DE`
- `campaign-prod-003-sdcards-consumer-electronics`: `SD cards and storage accessories` / `consumer-electronics` / `b2c` / `DE`
- `campaign-prod-003-b2b-workflow-software`: `Workflow automation software` / `software-b2b` / `b2b` / `DE`

## Question

Can the same reusable sales-agent core handle a mixed product set with several campaign profiles, including lower-risk consumer products and one B2B workflow campaign, without baking the vertical into the agent core?

## Scope

This set is intentionally broader than the insurance campaign.

It tests whether campaign-specific guardrails can live in the campaign wrapper while the core still handles:

- permission to continue
- interest classification
- strategy selection
- scheduling or escalation
- structured logging

## Dataset

- Name: PROD-003 mixed campaign cases
- Source: project-authored synthetic product scenarios
- License/usage notes: internal research/product planning artifact
- Size: 8 cases
- Campaign count: 4
- Language: German-oriented synthetic call dialogue

## Categories Covered

- home-improvement
- health-or-wellness
- consumer-electronics
- software-b2b

## Results

Packet generation completed:

- `research/experiments/generated/PROD-003-evaluation-packet.md`

Database-shaped export completed:

- `research/experiments/generated/PROD-003-db-records.json`

SQLite import completed:

- `research/experiments/generated/PROD-003.sqlite`
- `research/experiments/generated/PROD-003-sqlite-report.md`

Validation completed:

- `scripts/validate_prod_003_campaigns.py`

Observed table counts:

- Leads: 8
- Sales campaigns: 4
- Call sessions: 8
- Qualification answers: 19
- Turn decisions: 19
- Call outcomes: 8
- Appointments: 3
- Escalations: 2

## Notes

This case set includes:

- windows replacement interest and no-need closure
- eyewear information-first and prescription escalation
- SD card interest and no-need closure
- B2B software scheduling and integration escalation

## Decision

Keep.

Reason:

This is the clearest proof so far that the product is campaign-driven and not vertical-specific.

## Next Step

Use the same campaign-wrapper pattern for future product sets rather than embedding campaign facts directly into the reusable agent core.
