# PROD-003 SQLite Import Report

- Database: `research/experiments/generated/PROD-003/PROD-003.sqlite`
- Source records: `research/experiments/generated/PROD-003/PROD-003-db-records.json`
- Data source: synthetic product simulation records

## Table Counts

- `leads`: 8
- `sales_campaigns`: 4
- `call_sessions`: 8
- `qualification_answers`: 19
- `turn_decisions`: 19
- `call_outcomes`: 8
- `appointments`: 3
- `escalations`: 2

## Campaigns

- `campaign-prod-003-b2b-workflow-software`: Workflow automation software / `software-b2b` / `b2b`
- `campaign-prod-003-glasses-eyewear`: Glasses and eyewear options / `health-or-wellness` / `b2c`
- `campaign-prod-003-sdcards-consumer-electronics`: SD cards and storage accessories / `consumer-electronics` / `b2c`
- `campaign-prod-003-windows-home-improvement`: Replacement windows consultation / `home-improvement` / `b2c`

## Interested Leads

- `lead-prod-003-c01` (Synthetic Consumer 11): send calendar invite and notify human home-improvement specialist
- `lead-prod-003-c05` (Synthetic Consumer 31): send calendar invite and notify human product specialist
- `lead-prod-003-c07` (Operations Director): send calendar invite and notify human solutions consultant

## Do-Not-Call Leads


## Appointments

- `appointment-prod-003-c01` for `lead-prod-003-c01` at `Tuesday 14:00`: `confirmed`
- `appointment-prod-003-c05` for `lead-prod-003-c05` at `Tuesday 10:00`: `confirmed`
- `appointment-prod-003-c07` for `lead-prod-003-c07` at `Monday 11:00`: `confirmed`

## Escalations

- `escalation-prod-003-c04` for `lead-prod-003-c04`: prescription or vision-health question outside approved AI scope (`open`)
- `escalation-prod-003-c08` for `lead-prod-003-c08`: integration or security question outside approved AI scope (`open`)

## Sample Turn Decisions For `call-prod-003-c01`

- Turn 1 `opening-permission`: `maybe-interested` / `rapport` -> `continue`
- Turn 2 `relevance-check`: `maybe-interested` / `inquiry` -> `ask-follow-up`
- Turn 3 `scheduling`: `interested` / `direct-ask-or-commitment` -> `confirm-scheduling`
