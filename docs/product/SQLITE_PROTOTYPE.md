# SQLite Prototype

## Purpose

Define the first local persistence layer for the product MVP prototype.

SQLite is the first implementation target because it requires no infrastructure and can store the same entities defined in `LEAD_DATABASE_DESIGN.md`.

## Files

- `db/sqlite_schema.sql`: local SQLite schema for the MVP entities
- `scripts/import_simulation_records.py`: imports database-shaped simulation JSON into SQLite
- `research/experiments/generated/PROD-001/PROD-001-db-records.json`: synthetic source records
- `research/experiments/generated/PROD-001/PROD-001.sqlite`: generated local SQLite database
- `research/experiments/generated/PROD-001/PROD-001-sqlite-report.md`: generated query report

## Import Command

```text
python scripts/import_simulation_records.py \
  --records research/experiments/generated/PROD-001/PROD-001-db-records.json \
  --db research/experiments/generated/PROD-001/PROD-001.sqlite \
  --report-out research/experiments/generated/PROD-001/PROD-001-sqlite-report.md \
  --reset
```

## What The Report Proves

The report checks that the prototype can retrieve:

- interested leads
- do-not-call leads
- confirmed appointments
- escalations
- turn-level decisions for one call
- call-control decisions such as `continue-call`, `end-call`, and `transfer-or-escalate`

## Boundary

This database is synthetic and local.

Do not store real customer data in generated experiment files. A production database needs access control, retention rules, deletion/suppression workflows, and explicit handling for personal data.

## Next Step

Use SQLite as the first backend for local prototype work. Move to Postgres only when the product needs a production-like service boundary or multi-user deployment.
