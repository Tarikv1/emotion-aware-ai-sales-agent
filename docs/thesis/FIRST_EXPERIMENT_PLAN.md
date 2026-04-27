# First Experiment Plan

## Goal

Build the smallest believable thesis experiment that connects emotion awareness to strategy selection without requiring a full live voice agent.

## Experiment shape

Use a public-data-only baseline with this flow:

1. detect or assign a small emotion class
2. map that emotion to a persuasion strategy
3. generate or evaluate a candidate response policy

## Phase 1 datasets

- `MELD` for emotion-oriented multi-turn dialogue context
- `Persuasion for Good` for persuasion strategy patterns and outcome signals
- `IEMOCAP` only after dataset validity is confirmed for real audio experiments

## First narrow objective

Create a reduced emotion taxonomy and a reduced persuasion taxonomy.

Suggested starting emotion set:

- `positive`
- `neutral`
- `skeptical-or-negative`

Suggested starting strategy set:

- `rapport`
- `inquiry`
- `evidence-or-benefit`
- `emotional-appeal`
- `direct-ask-or-commitment`

These are not final labels. They are a practical first bridge between the emotion side and the persuasion side.

For phase 1:

- use `MELD` `Sentiment` as the primary compact emotion signal
- use the `Persuasion for Good` annotated persuader labels as the source for the compact strategy taxonomy

## Concrete deliverables

1. A label-mapping note for `MELD` emotions into the small thesis taxonomy
2. A strategy-mapping note for `Persuasion for Good` annotation labels into a compact strategy set
3. A merged experiment brief describing:
   - input
   - mapped emotion
   - chosen strategy
   - example response behavior

## Why this is the right first step

This experiment proves the thesis can connect emotional state to adaptive persuasion behavior before we spend time on speech pipelines, TTS, or real-time orchestration.

## Not yet

Do not start with:

- end-to-end live calling
- full agent training
- multilingual adaptation
- private-data tuning
- production deployment concerns
