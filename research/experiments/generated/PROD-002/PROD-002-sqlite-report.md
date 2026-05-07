# PROD-002 SQLite Import Report

- Database: `research/experiments/generated/PROD-002.sqlite`
- Source records: `research/experiments/generated/PROD-002-db-records.json`
- Data source: synthetic product simulation records

## Table Counts

- `leads`: 8
- `sales_campaigns`: 1
- `call_sessions`: 8
- `qualification_answers`: 15
- `turn_decisions`: 15
- `call_outcomes`: 8
- `appointments`: 1
- `escalations`: 3

## Campaigns

- `campaign-prod-002-b2c-insurance`: Dental insurance and serious-illness protection / `insurance` / `b2c`

## Interested Leads

- `lead-prod-002-c01` (Synthetic Consumer 01): send calendar invite and notify human insurance specialist

## Do-Not-Call Leads

- `lead-prod-002-c05` (Synthetic Consumer 05): suppress future outreach for this contact according to policy

## Appointments

- `appointment-prod-002-c01` for `lead-prod-002-c01` at `Wednesday 15:00`: `confirmed`

## Escalations

- `escalation-prod-002-c03` for `lead-prod-002-c03`: coverage guarantee request outside approved AI response scope (`open`)
- `escalation-prod-002-c07` for `lead-prod-002-c07`: callback timing remains vague (`open`)
- `escalation-prod-002-c08` for `lead-prod-002-c08`: health-related policy question outside approved AI scope (`open`)

## Sample Turn Decisions For `call-prod-002-c01`

- Turn 1 `opening-permission`: `maybe-interested` / `rapport` -> `continue`
- Turn 2 `relevance-check`: `maybe-interested` / `inquiry` -> `ask-follow-up`
- Turn 3 `timing-openness-check`: `interested` / `direct-ask-or-commitment` -> `continue`
