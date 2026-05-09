# Project Navigation

Use this when you know what you want to inspect but not where it lives.

## Start Here

- `docs/thesis/ROADMAP.md`: current checkpoint, next gates, and completed evidence.
- `docs/product/COMMANDS.md`: runnable local commands.
- `docs/product/CHECKPOINT_INDEX.md`: checkpoint docs grouped by track.
- `docs/brain/README.md`: the sales-agent brain architecture, state contract, and dialogue policy.
- `research/experiments/README.md`: experiment cases and generated artifacts.
- `scripts/README.md`: runner, validator, module, and setup script groups.

## Main Areas

| Area | Use it for |
| --- | --- |
| `docs/brain/` | Runtime brain architecture, BRAIN state schema, and dialogue-policy hardening. |
| `docs/product/` | Product scope, client workflow, RAG/voice/runtime/product checkpoint docs, and command map. |
| `docs/thesis/` | Roadmap, methodology, decisions, source registry, and thesis writing support. |
| `docs/data/` | Data boundaries, private-call policy, dataset readiness, and source usage. |
| `research/experiments/cases/` | Fixed JSON case inputs for checkpoint runners. |
| `research/experiments/generated/` | Generated result/report folders, grouped by checkpoint. |
| `scripts/` | Local modules, runners, validators, setup checks, and safety guards. |
| `data/private/` | Ignored local-only private call/audio material. Do not copy raw private material elsewhere. |

## Current Work Tracks

- Brain/product decision layer: `docs/brain/`, `PROD-*`, `BRAIN-*`.
- Retrieval/RAG: `docs/product/RAG_*`, `scripts/rag_*`, `research/experiments/generated/RAG-*`.
- Voice/runtime delivery: `docs/product/VOICE_*`, `docs/product/RESP_*`, related `scripts/voice_*`, `scripts/runtime_*`, and `scripts/run_resp_*`.
- Thesis traceability: `docs/thesis/METHODOLOGY_LOG.md`, `docs/thesis/DECISION_LOG.md`, `docs/thesis/THESIS_REFERENCE_REGISTRY.md`.

## Before Moving Files

Many validators point at exact paths. Prefer adding an index or README before moving files. If a move is still useful, update:

- `scripts/check_setup.py`
- `scripts/validate_check_setup.py`
- `scripts/check_project_drift.py`
- checkpoint validators that reference the moved file
- `docs/product/COMMANDS.md`
- `docs/thesis/METHODOLOGY_LOG.md` and `docs/thesis/DECISION_LOG.md` if the move changes the evidence trail
