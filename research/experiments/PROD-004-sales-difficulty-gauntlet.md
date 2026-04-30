# PROD-004: Sales Difficulty Gauntlet

## Status

Ready for simulation

## Source Label

`product-synthetic`

## Date

2026-04-30

## Purpose

Test universal sales difficulties before broadening the campaign library further.

The goal is to make the reusable sales-agent core better at sales behavior that appears across many industries:

- price resistance
- information brush-offs
- status quo resistance
- timing delays
- authority gaps
- trust and credibility concerns
- competitor comparisons
- fit or risk concerns
- vague interest
- angry or annoyed customers
- human requests
- claim boundaries

## Public Grounding

The difficulty categories are grounded in public sales-objection patterns from Apollo, Salesgenie, Proposify, and B2B Vic.

The cases themselves are synthetic and rewritten for this project.

No real customer conversations or copied call transcripts are stored in the repository.

## Campaigns

- `campaign-prod-004-b2c-energy-switch`: household energy tariff review
- `campaign-prod-004-b2c-telecom-plan`: internet and mobile plan review
- `campaign-prod-004-b2c-education-course`: online language course consultation
- `campaign-prod-004-b2b-hr-software`: HR onboarding software
- `campaign-prod-004-b2b-staffing-service`: recruiting and staffing support

## Dataset

- Name: PROD-004 sales difficulty gauntlet
- Source: project-authored synthetic product scenarios
- License/usage notes: internal research/product planning artifact
- Size: 14 cases
- Campaign count: 5
- Language: German-oriented synthetic call dialogue

## Results

Packet generation completed:

- `research/experiments/generated/PROD-004-evaluation-packet.md`

Database-shaped export completed:

- `research/experiments/generated/PROD-004-db-records.json`

SQLite import completed:

- `research/experiments/generated/PROD-004.sqlite`
- `research/experiments/generated/PROD-004-sqlite-report.md`

Validation completed:

- `scripts/validate_prod_004_difficulty_gauntlet.py`

Observed table counts:

- Leads: 14
- Sales campaigns: 5
- Call sessions: 14
- Qualification answers: 20
- Turn decisions: 20
- Call outcomes: 14
- Appointments: 0
- Escalations: 7

## Interpretation

This set is intentionally harder than the earlier campaign-breadth set.

It should test whether the agent:

- stays curious under resistance
- avoids pressure
- does not over-read weak signals
- does not invent claims
- knows when to route to a human
- keeps scheduling tied to explicit commitment

## Decision

Keep.

Reason:

This creates a difficulty-first evaluation layer that should improve the agent's transferable sales behavior before expanding into many more industries.

## Next Step

Use `PROD-004` as the main challenge set for evaluating rule-based and LLM-based agent behavior before adding a much broader campaign-category library.
