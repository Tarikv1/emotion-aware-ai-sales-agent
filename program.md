# Research Program

This file defines how Codex should help run thesis experiments for the Emotion Aware AI Sales Agent project.

## Mission

Build and evaluate a thesis-feasible AI sales agent that adapts its response strategy based on detected customer emotion.

The project should progress through small, reviewable experiments rather than large speculative builds.

## Current Research Posture

Treat the thesis proposal as directional, not final.
Use public datasets first.
Keep private call-center data optional and restricted until it is actually available and its usage conditions are clear.
Prioritize measurable slices of the system over full agent polish.

## Experiment Loop

For each experiment:

1. Define one narrow hypothesis.
2. Choose one dataset or dataset slice.
3. Set one primary metric and one or two secondary metrics.
4. Define the allowed edit scope before coding.
5. Run the smallest useful implementation.
6. Record results in `research/experiments/`.
7. Decide whether to keep, revise, or discard the approach.

Avoid changing multiple major variables at once.
If an experiment changes the model, dataset, preprocessing, and evaluation all together, split it.

## First Phase Focus

Start with public-data-first emotion recognition.

Preferred first experiments:

- audit candidate public datasets
- normalize a small emotion taxonomy
- build a simple emotion-classification baseline
- measure classifier quality and latency
- map detected emotions to a first persuasion-strategy table

Do not start with full real-time calling, full TTS, or autonomous agent orchestration.

## Experiment Rules

Each experiment must declare:

- source label: `public-only`, `private-restricted`, or `mixed-source`
- dataset
- hypothesis
- editable files or modules
- fixed budget
- metrics
- result
- decision

Use `research/experiments/EXPERIMENT_TEMPLATE.md` for new experiment notes.

## Data Rules

Follow `docs/data/DATA_USAGE_POLICY.md`.

Do not commit private raw audio, transcripts, exports, or derived identifying artifacts.
If private data influences a result, disclose that in the experiment note and thesis materials.

## Engineering Rules

Keep implementations simple until the data path is proven.
Prefer scripts and notebooks for discovery, then promote stable code into `services/` or `packages/`.
Preserve a clear split between research artifacts and product code.
Update docs when an experiment changes the thesis direction.

## Decision Standard

An experiment is useful if it makes the next decision clearer.
It does not need to be impressive, complete, or production-like.
