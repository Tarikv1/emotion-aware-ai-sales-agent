# VOICE-015 Prosody Naturalness Layer

## Purpose

VOICE-015 adds a provider-neutral prosody planning layer before TTS.

The goal is to reduce robotic voice delivery without turning the sales agent into a casual character and without corrupting campaign scripts, compliance text, or call-control wording.

The default style is always:

```text
professional-human
```

This is not insurance-only and not tied to one voice provider. It belongs to the reusable voice/runtime layer and is configured per `SalesCampaign`.

## Runtime Position

```text
customer speech
  -> speech-to-text
  -> realtime sales-agent core
  -> guarded response generation
  -> speech naturalness layer
  -> prosody naturalness layer
  -> provider-specific TTS adapter
```

VOICE-015 does not decide what the agent should say. It only creates bounded delivery cues for how eligible freeform speech could be spoken.

## Cue Types

VOICE-015 can create these cue types:

- `pause`: bounded pause after a sentence or clause
- `rate`: small speed change for a target phrase
- `emphasis`: professional emphasis on a target word or phrase
- `pitch`: subtle pitch contour such as warm-soft, slight-rise, or steady-low
- `stretch`: rare thinking hold such as `Also...` in debug view

The layer stores structured cues in `prosody_plan`.

It also emits:

- `tts_text`: clean provider-safe text
- `debug_text`: human review text that may show emphasis as Markdown bold or stretch as ellipsis

Provider adapters should use `prosody_plan`, not blindly send debug markup to TTS.

## Protected Segments

VOICE-015 must not add cues inside:

- campaign qualification questions
- company-provided scripts
- approved openings
- required disclosures
- compliance statements
- legal, medical, coverage, or claim-boundary wording
- do-not-call confirmations
- hang-up lines
- appointment confirmations
- sensitive escalations

This preserves the same boundary as VOICE-012: freeform speech can sound human, but company-required text stays exact.

## Randomization Model

The layer uses seeded bounded variation, not uncontrolled randomness.

Randomized dimensions:

- pause duration
- speech-rate ratio
- pitch contour delta
- stretch hold duration

The same input and seed produce the same output. This keeps the experiment reproducible while still avoiding perfectly uniform pacing.

Current bounds:

- pause duration: `120-420 ms`
- rate ratio: `0.90-1.08`
- pitch directions: `warm-soft`, `slight-rise`, `steady-low`
- stretch: rare and short, represented as a cue first

## Why Not Raw Markdown Bold

The agent may show debug emphasis as:

```text
The **important** thing is ...
```

But raw Markdown bold is not the runtime contract. Some TTS providers may ignore it, pronounce punctuation awkwardly, or handle it inconsistently.

The runtime contract is the structured cue:

```json
{
  "type": "emphasis",
  "target": "important",
  "strength": "medium"
}
```

Each provider adapter can later decide how to render it safely.

## Validation

Run:

```powershell
python scripts\validate_voice_015_prosody_naturalness.py
```

The validator checks:

- eight bilingual cases exist
- all cases use `professional-human`
- pause, pitch, rate, emphasis, and stretch cues exist
- no cue is added to protected segments
- protected text remains unchanged
- clean TTS text contains no Markdown emphasis
- seeded output is deterministic across repeated runs
- no provider call, API key, customer audio upload, or voice cloning is involved

## Current Result

The generated VOICE-015 packet contains:

- cases: `8`
- German cases: `4`
- English cases: `4`
- total cues: `22`
- pause cues: `5`
- pitch cues: `6`
- rate cues: `5`
- emphasis cues: `5`
- stretch cues: `1`
- protected-segment cues: `0`
- validation passed: `8 / 8`

## Generated Artifacts

```text
research/experiments/generated/VOICE-015/VOICE-015-prosody-naturalness.json
research/experiments/generated/VOICE-015/VOICE-015-prosody-naturalness-report.md
```

## Product Meaning

VOICE-015 separates human-like delivery from provider-specific tricks.

This lets the product keep one reusable sales-agent core, one campaign model, and multiple possible TTS adapters. The next checkpoint should test how the strongest provider renders these cues compared with plain guarded text.
