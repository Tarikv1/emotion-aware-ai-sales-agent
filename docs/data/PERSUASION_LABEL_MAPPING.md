# Persuasion For Good Label Mapping

## Purpose

Define a compact persuasion-strategy taxonomy for the first thesis baseline using the annotated subset of `Persuasion for Good`.

## Local data inspected

- Source workbook: `data/public/persuasion-for-good/persuasionforgood-master/data/AnnotatedData/300_dialog.xlsx`
- Primary persuader label column: `er_label_1`
- Secondary persuader label column: `er_label_2`

The first baseline should rely primarily on `er_label_1`.
The `ee_*` labels are useful later for analyzing user reactions, but they are not the primary source for the agent strategy taxonomy.

## Working decision

Use a five-part strategy taxonomy for phase 1:

- `rapport`
- `inquiry`
- `evidence-or-benefit`
- `emotional-appeal`
- `direct-ask-or-commitment`

## Why

- The raw persuader labels are too granular for a first thesis baseline.
- A compact taxonomy is easier to map from emotional state to adaptive behavior.
- The dataset contains explicit appeal and ask behaviors, so compressing them into a few interpretable buckets keeps the first experiment grounded without overfitting to annotation detail.
- The earlier idea of using `reassurance` as a core category is not well supported by the dataset labels, so it should not be forced into phase 1.

## Phase-1 mapping table

### `rapport`

- `greeting`
- `acknowledgement`
- `thank`
- `praise-user`
- `personal-related-inquiry`
- `comment-partner`
- `you-are-welcome`
- `closing`
- `off-task`

### `inquiry`

- `task-related-inquiry`
- `source-related-inquiry`
- `ask-not-donate-reason`
- `positive-to-inquiry`
- `neutral-to-inquiry`
- `negative-to-inquiry`

### `evidence-or-benefit`

- `credibility-appeal`
- `donation-information`
- `logical-appeal`
- `self-modeling`

### `emotional-appeal`

- `emotion-appeal`
- `personal-story`

### `direct-ask-or-commitment`

- `proposition-of-donation`
- `foot-in-the-door`
- `ask-donation-amount`
- `confirm-donation`
- `ask-donate-more`

### `other`

- `other`

For phase 1, keep `other` out of the core strategy set when possible and treat it as overflow or non-core behavior.

## High-frequency persuader labels observed

The most common `er_label_1` labels in the inspected local data were:

- `credibility-appeal`
- `other`
- `donation-information`
- `logical-appeal`
- `emotion-appeal`
- `greeting`
- `proposition-of-donation`
- `acknowledgement`
- `thank`

This supports a strategy taxonomy that includes evidence-oriented behavior, emotional appeal, rapport, and direct asks.

## Notes for the thesis

Describe this as a controlled abstraction from the dataset's annotation scheme.
The thesis should make clear that the compact strategy taxonomy was designed for the first adaptive baseline and does not replace the full richness of the original annotation space.
