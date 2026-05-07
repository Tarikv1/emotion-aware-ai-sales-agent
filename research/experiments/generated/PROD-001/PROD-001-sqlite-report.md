# PROD-001 SQLite Import Report

- Database: `research/experiments/generated/PROD-001.sqlite`
- Source records: `research/experiments/generated/PROD-001-db-records.json`
- Data source: synthetic product simulation records

## Table Counts

- `leads`: 12
- `sales_campaigns`: 1
- `call_sessions`: 12
- `qualification_answers`: 32
- `turn_decisions`: 32
- `call_outcomes`: 12
- `appointments`: 1
- `escalations`: 5

## Campaigns

- `campaign-prod-001-b2b-lead-qualification`: Lead follow-up solution / `software-b2b` / `b2b`

## Interested Leads

- `lead-prod-001-c01` (Head of Sales Operations): send calendar invite and notify human sales specialist
- `lead-prod-001-c06` (Sales Team Lead): offer available appointment windows focused on callback tracking use case
- `lead-prod-001-c08` (Customer Success Manager): create scheduling follow-up task or route to human scheduler

## Do-Not-Call Leads

- `lead-prod-001-c04` (Business Owner): suppress future outreach for this contact according to policy

## Appointments

- `appointment-prod-001-c01` for `lead-prod-001-c01` at `Wednesday 14:30`: `confirmed`

## Escalations

- `escalation-prod-001-c05` for `lead-prod-001-c05`: complex integration question outside approved AI response scope (`open`)
- `escalation-prod-001-c07` for `lead-prod-001-c07`: wrong contact with named referral path (`open`)
- `escalation-prod-001-c08` for `lead-prod-001-c08`: scheduling window too vague to confirm appointment (`open`)
- `escalation-prod-001-c11` for `lead-prod-001-c11`: lead requested human contact (`open`)
- `escalation-prod-001-c12` for `lead-prod-001-c12`: privacy or compliance-sensitive topic (`open`)

## Sample Turn Decisions For `call-prod-001-c01`

- Turn 1 `opening-permission`: `maybe-interested` / `rapport` -> `continue`
- Turn 2 `relevance-check`: `maybe-interested` / `inquiry` -> `ask-follow-up`
- Turn 3 `pain-point-check`: `maybe-interested` / `inquiry` -> `continue`
- Turn 4 `timing-openness-check`: `interested` / `direct-ask-or-commitment` -> `continue`
- Turn 5 `scheduling`: `interested` / `direct-ask-or-commitment` -> `confirm-scheduling`
