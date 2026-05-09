# VOICE-012 Speech Naturalness

## Objective

Test whether the sales-agent voice path can become more human-like by adding rare mid-utterance fillers while preserving scripted and compliance-sensitive text exactly.

## Motivation

VOICE-011 showed that the provider audio was usable but still sounded obviously AI-generated. A human sales agent does not usually convert thoughts into perfectly smooth speech. They may occasionally say `um`, `uh`, `hm`, `Ã¤hm`, or short discourse markers.

However, a real call-center agent also reads certain material cleanly:

- campaign qualification questions
- company-provided scripts
- required disclosures
- compliance statements
- appointment confirmations
- do-not-call and hang-up lines

VOICE-012 tests that distinction.

## Method

The experiment uses a text-only deterministic renderer:

```text
approved speech segments
  -> protect scripted and compliance segments
  -> insert rare fillers in eligible freeform segments
  -> validate protected segments stayed unchanged
  -> produce TTS text
```

No TTS provider is called. No API key is required. No customer audio is uploaded.

## Cases

The case file is:

```text
research/experiments/cases/voice-012-speech-naturalness.json
```

It includes:

- English freeform objection handling
- German freeform objection handling
- mixed English freeform plus campaign qualification question
- mixed German freeform plus qualification question and disclosure
- strict German insurance boundary
- German do-not-call and hang-up lines
- disabled English clean-script profile
- protected appointment confirmation

## Current Result

Generated artifacts:

```text
research/experiments/generated/VOICE-012/VOICE-012-speech-naturalness.json
research/experiments/generated/VOICE-012/VOICE-012-speech-naturalness-report.md
```

Current summary:

- cases: `8`
- German cases: `4`
- English cases: `4`
- fillers inserted: `5`
- eligible freeform segments: `7`
- protected segments: `9`
- validation passed: `8 / 8`
- provider calls made: `false`
- customer audio uploaded: `false`

## Interpretation

The experiment supports the segment-aware design:

- freeform objection handling and transitions can receive rare mid-utterance fillers
- campaign qualification questions remain exact
- required disclosures remain exact
- strict insurance boundary wording remains clean
- do-not-call, hang-up, and appointment confirmation wording remain clean
- naturalness is campaign-configurable rather than hard-coded across the product

## Limitation

VOICE-012 is still text-only. It proves the wording contract, not audio quality.

The next audio step should synthesize VOICE-012 naturalized text through the selected TTS provider and compare:

- naturalness
- trustworthiness
- professional tone
- German pronunciation
- filler timing
- whether the agent becomes more human without sounding sloppy
