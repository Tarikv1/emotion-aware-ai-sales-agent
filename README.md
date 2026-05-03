# Emotion Aware AI Sales Agent

This project is both a thesis-driven research workspace and a product workspace for building an emotion-aware AI sales agent intended for real client use. The structure stays flexible on architecture while giving research, product, data, and implementation their own clear homes.

## Layout

```text
emotion-aware-ai-sales-agent/
  program.md
  apps/
    web/
    dashboard/
  services/
    sales-agent-api/
    emotion-engine/
  packages/
    shared/
  data/
    public/
    private-restricted/
    processed/
  research/
    notes/
    experiments/
  docs/
    thesis/
    product/
    data/
  scripts/
```

## Folder Guide

- `apps/`: user-facing demos or internal interfaces if the thesis grows into a demo app.
- `program.md`: lightweight research instructions for running focused thesis experiments.
- `services/`: implementation modules for the pipeline once architecture choices become concrete.
- `packages/shared/`: shared types, prompts, schemas, and helper code.
- `data/public/`: public datasets and public-data metadata.
- `data/private-restricted/`: placeholders and manifests for restricted local data. Do not commit sensitive raw data.
- `data/processed/`: cleaned, derived, or intermediate data safe to keep under project rules.
- `research/notes/`: evolving thinking, open questions, and working notes.
- `research/experiments/`: experiment logs and exploratory work.
- `docs/thesis/`: thesis framing, scope, and planning documents.
- `docs/product/`: product positioning, MVP scope, client-facing assumptions, and launch considerations.
- `docs/data/`: data policy, data readiness, and source documentation.
- `scripts/`: setup, local dev, and automation scripts.

## Current Focus

The immediate focus is not full agent implementation. It is:

1. keep the roadmap current
2. make the prompt-comparison workflow repeatable
3. expand from seed cases to larger dataset-grounded experiments
4. keep thesis evidence documented as work happens
5. preserve a product path toward a client-usable MVP

## Thesis Writing Support

The project keeps reusable thesis-writing material under `docs/thesis/`.
Use that folder to record decisions, methodology changes, and experiment rationale while building, so the final thesis can be drafted from project evidence instead of memory.

The main steering document is `docs/thesis/ROADMAP.md`.
The product-facing brief is `docs/product/PRODUCT_BRIEF.md`.
Use `docs/product-review-gates.md` before larger product/runtime changes, provider work, or customer setup changes.
