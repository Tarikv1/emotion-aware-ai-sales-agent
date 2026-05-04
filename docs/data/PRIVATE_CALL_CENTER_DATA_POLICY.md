# Private Call-Center Data Policy

## Purpose

Define the local-only boundary for private call-center audio and other raw private call assets.

## Storage Location

Raw private call-center audio must live only in:

```text
data/private/
```

This folder is ignored by Git. The only tracked file allowed inside it is `data/private/.gitignore`, which exists to keep the folder path and local-ignore rule available after cloning.

## Hard Rules

- Do not commit raw private audio.
- Do not copy raw private audio into tracked folders.
- Do not include raw private audio in generated reports, examples, prompt packets, demos, screenshots, or thesis appendices.
- Do not upload raw private audio to ASR, TTS, LLM, analytics, or cloud storage providers unless a later explicit reviewed workflow allows it.
- Do not use private call-center data for fine-tuning until legal basis, client approval, consent/privacy review, retention rules, and minimization rules are documented.
- Private identifiers are not training signal.
- Names, addresses, phone numbers, emails, account numbers, policy numbers, payment details, dates of birth, exact locations, and comparable identifiers must not leave `data/private/`.
- Sensitive personal details, including health details, family details, financial details, and exact life circumstances, must not leave `data/private/` unless a later reviewed workflow proves they are lawful, necessary, minimized, and approved.

## Allowed Local Uses

Private call-center audio may be used locally, after approval, for:

- transcription experiments
- speech-pattern analysis
- repeated objection and phrase mining
- sales-process pattern mining
- evaluation of local-only prototypes
- creation of minimized and permissioned training examples

## Derived Data

Derived transcripts, labels, summaries, and examples must be reviewed before they are stored outside `data/private/`.

Safe derived artifacts may be committed only when they contain no raw private audio, no direct identifiers, no sensitive personal details, and no confidential client information.

## Export Review Gate

Nothing derived from private call-center audio may leave `data/private/` until it passes a local export review.

The review must confirm:

- the file contains no raw audio
- direct identifiers have been removed
- irrelevant private details have been removed
- sensitive details have been removed unless explicitly approved and necessary
- the artifact contains only sales-learning signal, such as objection type, emotion state, strategy, response pattern, turn structure, and outcome
- the artifact is safe for its destination, such as `data/processed/`, RAG, evaluation, or fine-tuning

Do not export a file when the answer to any review item is uncertain.

## Training Signal Boundary

Allowed learning signal:

- objection patterns
- sales-process stages
- emotion or interest-state transitions
- successful and unsuccessful response patterns
- handoff and escalation patterns
- call outcome patterns
- anonymized phrase templates after review

Disallowed learning signal:

- names
- phone numbers
- addresses
- emails
- dates of birth
- account, policy, or payment identifiers
- exact locations
- private health facts
- private financial facts
- any detail whose main value is identifying or profiling a person rather than improving sales behavior

## Default Assumption

If there is uncertainty, treat the file as private and keep it under `data/private/`.
