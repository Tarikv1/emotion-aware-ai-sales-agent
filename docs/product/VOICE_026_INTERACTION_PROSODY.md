# VOICE-026 Interaction Prosody

## Purpose

VOICE-026 separates interaction cues from filler words.

The agent should not become "more human" by randomly adding `um`, `aehm`, or casual words. It should decide whether a moment needs:

- a short lookup acknowledgement
- a neutral backchannel
- a bounded sales-pace cue
- no visible marker because the text is protected

This keeps the voice more realistic while protecting trust, compliance, and campaign-exact wording.

## Why This Exists

VOICE-024 and VOICE-025 showed that filler placement matters, but filler placement alone does not solve robotic voice behavior.

The deeper speech review separated four concerns:

- speaker fillers: planning or repair sounds
- listener backchannels: short signs of understanding
- discourse markers: turn-shaping words
- provider prosody: pace, pause, pitch, and emotional delivery

VOICE-026 implements the backchannel and interaction-prosody part before the next live ElevenLabs comparison.

## Runtime Position

Current voice delivery order:

```text
RESP-001 guarded response
  -> VOICE-022 spoken-text normalization
  -> VOICE-023/025 speech realism and filler placement
  -> VOICE-026 interaction prosody
  -> VOICE-015/016 provider-neutral prosody/rendering
  -> future live TTS provider
```

`final_response` still stays unchanged. VOICE-026 may only shape provider-facing TTS text for eligible freeform segments.

## Rules

Eligible freeform segments may receive:

- `latency_acknowledgement` when lookup or processing may take more than about one second
- `neutral_backchannel` for concern, confusion, or unsafe-claim contexts
- `sales_pace_variation` as provider-neutral metadata for bounded rhythm changes

Protected segments receive no markers:

- campaign qualification questions
- required disclosures
- exact company scripts
- legal, medical, insurance, coverage, payout, or savings boundaries
- appointment confirmations
- human handoff scripts
- do-not-call or hangup lines

Unsafe claim contexts must not receive agreement-style markers.

Examples to avoid:

```text
yes
exactly
that's right
ja
genau
```

Safe neutral examples:

```text
I understand.
Das pruefe ich kurz.
Ich verstehe.
```

## Language Behavior

English and German use separate marker pools.

English examples:

- `Let me check that.`
- `I can check that.`
- `I understand.`
- `That makes sense.`

German examples:

- `Das pruefe ich kurz.`
- `Ich schaue kurz nach.`
- `Ich verstehe.`
- `Das verstehe ich.`

German is not treated as translated English. The layer avoids German agreement tokens such as `ja` and `genau` around risky claims because they can accidentally validate what the agent must not promise.

## Listening Rubric

VOICE-026 stores a listening rubric with every run:

- naturalness
- trust
- confidence
- warmth
- pace
- interruption safety
- sales usefulness
- protected-text safety

This lets future listening reviews be more specific than "sounds robotic" or "sounds better."

## Experiment

Run:

```powershell
python scripts\run_voice_026_interaction_prosody.py
```

Validate:

```powershell
python scripts\validate_voice_026_interaction_prosody.py
```

Generated outputs:

```text
research/experiments/generated/VOICE-026-interaction-prosody/results.json
research/experiments/generated/VOICE-026-interaction-prosody/report.md
```

## Current Result

The initial offline packet covers six cases:

- English lookup acknowledgement
- German lookup acknowledgement
- English unsafe-agreement guard
- German unsafe-agreement guard
- German protected campaign question lock
- English stop-intent suppression

Current validation status:

- cases: `6`
- English cases: `3`
- German cases: `3`
- provider calls: `false`
- customer audio upload: `false`
- voice cloning: `false`
- protected segment changes: `0`
- unsafe agreement markers: `0`

## Thesis Relevance

VOICE-026 turns the speech-realism research into a testable interaction layer:

- the implementation distinguishes filler words from backchannels
- it keeps German and English behavior separate
- it models pace variation without requiring a provider API call
- it protects regulated or campaign-exact text
- it gives the next live audio comparison a clearer listening rubric
