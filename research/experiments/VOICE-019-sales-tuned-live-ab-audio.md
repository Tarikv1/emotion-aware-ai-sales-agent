# VOICE-019 Sales-Tuned Live A/B Audio

## Question

Does the VOICE-018 professional-sales tuned input create better live audio than the previous VOICE-017-style prosody input?

VOICE-019 does not answer that yet. It creates the dry-run/live-capable A/B harness safely so the answer can be gathered through a later listening run.

## Method

The harness compares:

```text
prosody
sales_tuned
```

across:

- 2 German cases
- 2 English cases
- ElevenLabs
- Cartesia

Default execution is dry-run and no-key.

## Dry-Run Result

```text
cases: 4
German cases: 2
English cases: 2
providers: elevenlabs, cartesia
A/B variants: 16
prosody variants: 8
sales-tuned variants: 8
API calls made: 0
audio files created: 0
fallback count: 16
customer audio uploaded: false
voice cloning used: false
human ratings recorded: false
quality claim allowed: false
```

## Interpretation

The structure is ready for a live provider run, but no audio-quality claim is allowed yet.

The live listening review should compare:

- naturalness
- sales-call pacing
- pitch variation
- emotional appropriateness
- clarity
- language pronunciation
- AI-obviousness
- artifacts or muffling
- trustworthiness
- prosody vs sales-tuned preference

## Safety

The harness uses environment-only keys, redacted request previews, bounded timeouts, no customer audio upload, and no voice cloning.

Generated live audio files are ignored by Git.
