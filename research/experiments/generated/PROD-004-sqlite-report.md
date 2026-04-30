# PROD-004 SQLite Import Report

- Database: `research/experiments/generated/PROD-004.sqlite`
- Source records: `research/experiments/generated/PROD-004-db-records.json`
- Data source: synthetic product simulation records

## Table Counts

- `leads`: 14
- `sales_campaigns`: 5
- `call_sessions`: 14
- `qualification_answers`: 20
- `turn_decisions`: 20
- `call_outcomes`: 14
- `appointments`: 0
- `escalations`: 7

## Campaigns

- `campaign-prod-004-b2b-hr-software`: HR onboarding software / `software-b2b` / `b2b`
- `campaign-prod-004-b2b-staffing-service`: Recruiting and staffing support / `professional-services` / `b2b`
- `campaign-prod-004-b2c-education-course`: Online language course consultation / `education-services` / `b2c`
- `campaign-prod-004-b2c-energy-switch`: Household energy tariff review / `energy` / `b2c`
- `campaign-prod-004-b2c-telecom-plan`: Internet and mobile plan review / `telecom` / `b2c`

## Interested Leads

- `lead-prod-004-c14` (Operations Lead): offer available appointment windows for human staffing specialist (`continue-call`)

## Do-Not-Call Leads


## Appointments


## Escalations

- `escalation-prod-004-c03` for `lead-prod-004-c03`: status quo resistance requires later nurturing (`open`)
- `escalation-prod-004-c04` for `lead-prod-004-c04`: callback timing remains broad rather than a confirmed appointment (`open`)
- `escalation-prod-004-c07` for `lead-prod-004-c07`: competitor comparison outside approved AI response scope (`open`)
- `escalation-prod-004-c08` for `lead-prod-004-c08`: coverage or speed guarantee request outside approved AI scope (`open`)
- `escalation-prod-004-c11` for `lead-prod-004-c11`: lead requested human contact (`open`)
- `escalation-prod-004-c12` for `lead-prod-004-c12`: learning outcome guarantee request outside approved AI scope (`open`)
- `escalation-prod-004-c13` for `lead-prod-004-c13`: wrong contact with decision-owner referral path (`open`)

## Sample Turn Decisions For `call-prod-004-c01`

- Turn 1 `opening-permission`: `maybe-interested` / `rapport` -> `ask-follow-up` (`continue-call`)
- Turn 2 `relevance-check`: `maybe-interested` / `inquiry` -> `ask-follow-up` (`continue-call`)
