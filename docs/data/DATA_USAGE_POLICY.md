# Data Usage Policy

## Purpose

Define how public and private conversation data may be used in this thesis project. Keep the project academically honest, operationally practical, and easy to explain to supervisors.

## Principles

Use only data that you are permitted to access and process.
Disclose private-data usage truthfully in the thesis whenever it influences training, tuning, retrieval, evaluation, or qualitative findings.
Do not claim that a result came only from public datasets if private call-center data materially influenced the system.
Prefer reproducible public-data experiments for the main baseline whenever possible.
Treat private call-center recordings as restricted local assets, not general project files.

## Approved Data Categories

### 1. Public datasets

Use for:

- baseline experiments
- reproducible evaluation
- early prototyping
- methodology demonstrations in the thesis

Keep these under project-managed public data folders.

### 2. Private call-center data

Use for:

- local-only exploratory analysis
- domain adaptation
- prompt and strategy refinement
- supplementary model tuning
- restricted qualitative comparisons

Do not commit raw private data, transcripts, exports, or derived identifying artifacts into the repo.

## Disclosure Rules

If private data affects the system, disclose that clearly.
Use wording such as:

`In addition to public datasets, proprietary call-center conversation data was used locally under restricted access conditions. The private data is not redistributed due to confidentiality constraints.`

If an experiment uses only public data, label it explicitly as public-only.
If an experiment uses mixed data sources, label it explicitly as mixed-source.
If a figure, table, or result depends on private data, do not present it as fully reproducible from public artifacts alone.

## Storage Rules

Store only metadata, schemas, manifests, and safe summaries in the repo.
Store private raw data outside the repo or in a clearly restricted local path that is excluded from version control.
Keep a manifest of what exists, where it lives, and what can be used for which purpose.
Anonymize or pseudonymize working copies whenever practical before downstream processing.

## Experiment Labels

Every experiment should declare one of these source labels:

- `public-only`
- `private-restricted`
- `mixed-source`

Record that label in experiment notes, evaluation docs, and any result tables.

## Thesis Reporting Policy

The thesis should separate:

- what is reproducible from public data
- what is supported by restricted private data
- what claims are limited by data-access constraints

This project may benefit from private call-center data, but that usage must remain visible in the written methodology and limitations.

## Immediate Rule Of Thumb

If a future version of the system becomes better because of private call-center data, say so.
