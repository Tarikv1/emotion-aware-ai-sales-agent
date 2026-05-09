# VOICE-018 Sales Voice Tuning

## Purpose

VOICE-018 responds to the first bilingual RESP-003 listening feedback: the voice was clear, but still too slow, flat, and obviously AI-generated for real sales leads.

This checkpoint stays offline and no-key. It does not claim live audio quality. It creates a professional-sales delivery preview on top of VOICE-016 provider previews so the next live TTS test has a safer, more intentional input.

## Source Artifact

VOICE-018 reads:

```text
research/experiments/generated/VOICE-016/VOICE-016-provider-prosody-rendering.json
```

It uses all eight VOICE-015/VOICE-016 cases across German and English.

## Tuning Profile

Profile: `professional-sales-v1`

The profile targets:

- faster professional sales-call pacing
- less flat emotional contour
- low-pressure confidence
- clearer empathy
- no casual overacting
- no filler words inside protected text

Speed is bounded:

- minimum speed ratio: `1.0`
- maximum speed ratio: `1.16`
- observed average eligible speed ratio in the generated artifact: `1.11`
- observed max speed ratio in the generated artifact: `1.142`

Emotion intents:

- `confident-low-pressure`
- `confident-practical`
- `curious-efficient`
- `warm-reassuring`

Pitch intents:

- `slight-rise`
- `steady-confident`
- `warm-soft`

## Protected Text

Protected text remains exact:

- campaign qualification questions
- required disclosures
- compliance statements
- do-not-call and hang-up lines
- coverage, health, legal, payout, or claim-boundary wording
- sensitive escalation and human handoff text

VOICE-018 keeps protected segment speed neutral and records `neutral-clear` / `steady-neutral` delivery intent.

## Provider Handling

Cartesia preview:

- eligible segments can receive outer professional-sales speed tags
- existing break tags are compressed into a faster rhythm
- inner careful-phrase speed tags may remain slightly slower for clarity, then return to the segment sales speed
- protected segments are not changed

ElevenLabs preview:

- eligible responses receive faster request-level `voice_settings.speed`
- existing break tags are compressed
- protected text stays exact
- pitch and emotion remain metadata until live provider tests prove a safe mapping

## Current Result

Generated summary:

```text
cases: 8
German cases: 4
English cases: 4
providers: cartesia, elevenlabs
sales-tuned variants: 16
tuned segments: 12
protected segments: 14
pause compressions: 10
average eligible speed ratio: 1.11
max speed ratio: 1.142
protected text changes: 0
validation passed: 16 / 16
provider calls made: false
requires API key: false
customer audio uploaded: false
voice cloning used: false
quality claim allowed: false
```

## Commands

Run:

```powershell
python scripts\run_voice_018_sales_voice_tuning.py
```

Validate:

```powershell
python scripts\validate_voice_018_sales_voice_tuning.py
```

## Generated Artifacts

- `research/experiments/cases/voice-018-sales-voice-tuning.json`
- `research/experiments/generated/VOICE-018/VOICE-018-sales-voice-tuning.json`
- `research/experiments/generated/VOICE-018/VOICE-018-sales-voice-tuning-report.md`

## Product Meaning

VOICE-018 moves the voice layer from "prosody is better than plain" toward "professional sales delivery is intentionally tuned." The next useful step is a live A/B listening run comparing VOICE-017 style prosody against VOICE-018 sales-tuned provider input.
