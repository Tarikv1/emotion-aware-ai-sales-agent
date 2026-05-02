# VOICE-016 Provider Prosody Rendering

## Purpose

VOICE-016 renders the provider-neutral `VOICE-015` prosody plan into provider-specific offline previews.

It does not call Cartesia, ElevenLabs, OpenAI, or any other provider. It does not require an API key and does not generate audio.

The goal is to inspect exactly what would be sent to each TTS provider before running a live audio comparison.

## Source Artifact

```text
research/experiments/generated/VOICE-015-prosody-naturalness.json
```

## Providers

VOICE-016 renders previews for:

- Cartesia Sonic 3
- ElevenLabs Flash v2.5

Provider docs referenced:

- https://docs.cartesia.ai/build-with-cartesia/sonic-3/ssml-tags
- https://docs.cartesia.ai/build-with-cartesia/sonic-3/volume-speed-emotion
- https://elevenlabs.io/docs/product/prompting/pacing-and-emotion
- https://help.elevenlabs.io/hc/en-us/articles/24352686926609-Do-pauses-and-SSML-phoneme-tags-work-with-the-API

## Mapping Rules

### Cartesia

Mapped in this checkpoint:

- `pause` -> `<break time="...ms"/>`
- `rate` -> `<speed ratio="..."/>target<speed ratio="1.000"/>`
- `emphasis` -> `<volume ratio="1.080"/>target<volume ratio="1.000"/>`
- `stretch` -> merged with nearby break or rendered as a short break

Recorded as unsupported:

- `pitch`

Pitch is not forced through emotion tags because that could make a professional sales call sound theatrical or change meaning.

### ElevenLabs

Mapped in this checkpoint:

- `pause` -> `<break time="...s" />`
- `rate` -> request-level `voice_settings.speed`
- `stretch` -> covered by a nearby break or rendered as a conservative ellipsis variant

Recorded as unsupported:

- `pitch`
- `emphasis`

Raw Markdown bold is not sent. Descriptive emotion text is also not injected because it may be spoken aloud or produce inconsistent results.

## Segment Safety

Rendering is done per segment, not by rewriting one combined text blob.

This prevents a target word from being accidentally modified inside a protected segment.

Protected segments remain unchanged:

- campaign qualification questions
- company scripts
- required disclosures
- compliance statements
- legal, medical, coverage, or claim-boundary text
- do-not-call confirmations
- hang-up lines
- appointment confirmations

## Current Result

Generated summary:

```text
cases: 8
German: 4
English: 4
providers: cartesia, elevenlabs
protected-segment provider tags: 0
validation passed: 8 / 8
provider calls made: false
requires API key: false
customer audio uploaded: false
```

Mapped cue counts:

```text
Cartesia: pause 5, rate 5, emphasis 5, stretch 1, pitch 0
ElevenLabs: pause 5, rate 5, stretch 1, emphasis 0, pitch 0
```

Unsupported cue counts:

```text
Cartesia: pitch 6
ElevenLabs: pitch 6, emphasis 5
```

## Validation

Run:

```powershell
python scripts\validate_voice_016_provider_prosody_rendering.py
```

The validator checks:

- eight cases are rendered
- two provider variants exist for each case
- no provider calls are made
- no API key is required
- clean rendered text contains no Markdown bold
- provider tags are not inserted into protected segments
- Cartesia pause, speed, and volume tags appear when applicable
- ElevenLabs break tags and request-level speed settings appear when applicable
- output is deterministic for the same VOICE-015 source artifact

## Generated Artifacts

```text
research/experiments/generated/VOICE-016-provider-prosody-rendering.json
research/experiments/generated/VOICE-016-provider-prosody-rendering-report.md
```

## Product Meaning

VOICE-016 turns prosody from a nice idea into an auditable provider adapter boundary.

The next live checkpoint should not invent new prosody behavior. It should take the VOICE-016 rendered provider input and synthesize plain vs prosody-shaped audio so the difference can be rated.
