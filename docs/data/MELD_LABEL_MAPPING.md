# MELD Label Mapping

## Purpose

Define how `MELD` labels should be used in the first thesis baseline.

## Local data inspected

- Source file: `data/public/meld/MELD-master/data/MELD/train_sent_emo.csv`
- Observed train rows: 9,989

## Available label fields

- `Emotion`
- `Sentiment`

Observed `Emotion` labels:

- `neutral`
- `joy`
- `surprise`
- `anger`
- `sadness`
- `disgust`
- `fear`

Observed `Sentiment` labels:

- `positive`
- `neutral`
- `negative`

## Working decision

Use `Sentiment` as the primary phase-1 label source.
Treat `Emotion` as a secondary analysis field for later experiments.

## Why

- `Sentiment` already gives a compact 3-way label space.
- It matches the first thesis baseline more naturally than the raw seven-way emotion set.
- It avoids forcing an arbitrary interpretation of `surprise`, which can be positive, neutral, or negative depending on context.
- It lets the first experiment stay simple while still being emotion-aware in a broad sense.

## Phase-1 mapping

Use this thesis-facing interpretation:

- `positive` -> `positive`
- `neutral` -> `neutral`
- `negative` -> `skeptical-or-negative`

## Secondary interpretation of raw emotion labels

If a later experiment uses the `Emotion` column directly, use this tentative collapsed mapping as a starting point:

- `joy` -> `positive`
- `neutral` -> `neutral`
- `anger` -> `skeptical-or-negative`
- `sadness` -> `skeptical-or-negative`
- `disgust` -> `skeptical-or-negative`
- `fear` -> `skeptical-or-negative`
- `surprise` -> do not force into the phase-1 baseline without an additional rule or contextual check

## Notes for the thesis

This is a pragmatic reduction for the first baseline, not a claim that sentiment and customer emotion are identical.
In the written thesis, describe this as an operational simplification used to make the first adaptive pipeline testable.
