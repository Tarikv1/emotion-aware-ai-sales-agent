# Experiments Folder

This folder separates human-readable experiment notes, fixed case inputs, and generated artifacts.

## Layout

- `*.md`: human-readable experiment notes and checkpoint summaries.
- `cases/`: fixed JSON inputs used by runners and validators.
- `generated/`: result/report folders created by runners.

## Cases

Use `cases/` when you need the input fixture for a checkpoint:

- `brain-*`: brain and state-schema cases.
- `prod-*`: product decision-layer cases.
- `rag-*`: retrieval and source-processing cases.
- `resp-*`: runtime response and listening-check cases.
- `voice-*`: voice and provider-delivery cases.

## Generated Artifacts

Generated outputs are grouped by checkpoint folder, for example:

- `generated/BRAIN-002-runtime-state-schema/`
- `generated/PROD-011-dialogue-policy-hardening/`
- `generated/RAG-018-scripted-call-simulation/`
- `generated/RESP-007-german-pacing-stability-follow-up/`
- `generated/VOICE-044-baseline-delivery-polish/`

Do not put new result files directly in the `generated/` root unless a validator explicitly expects it. Use a checkpoint folder.

## Safety

Generated reports must not contain raw private audio, raw private transcripts, API keys, customer identifiers, or provider payload secrets. Private-source work stays under ignored `data/private/` until a separate export review exists.
