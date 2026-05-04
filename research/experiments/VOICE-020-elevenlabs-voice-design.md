# VOICE-020 ElevenLabs Voice Design

## Objective

Prepare a reproducible ElevenLabs-first voice design checkpoint after `VOICE-019` showed that sales-tuned audio is better than prosody-only audio, but still sounds too robotic at the opening and not emotionally alive enough for real leads.

## Method

This checkpoint is offline and no-key.

It creates a design packet containing:

- English and German voice-design prompts
- synthetic preview text
- Voice Design UI candidates for loudness and guidance scale
- Voice Remixing prompts for English and German provider-side naturalization
- realtime and quality settings candidates
- emotional delivery bundles
- protected-text locks
- private-data boundaries
- dashboard steps for the next live ElevenLabs iteration

## Input Evidence

- `VOICE-018` created professional-sales delivery metadata.
- `VOICE-019` produced live ElevenLabs A/B audio.
- Human listening feedback preferred sales-tuned variants for both English and German.
- Remaining issues were rigid openings, flat pitch, insufficient emotion, and a prepared-script feel.
- ElevenLabs Voice Design generated voices sounded too robotic, too slow, and too telephone-filtered/muffled for the desired product voice.
- ElevenLabs Voice Remixing can iteratively adjust owned voices for pacing, style/emotion, pitch/timbre, and audio quality before runtime TTS.

## Safety Boundary

No private call-center audio is used as input.

No provider calls are made.

No API key is required.

No generated audio is created.

No voice cloning is used.

Private call-center audio may later inform only local abstract tuning notes, after review.

Voice IDs can be stored in ignored local config for repeat testing, but API keys remain environment-only.

## Output

The generated packet is:

```text
research/experiments/generated/VOICE-020-elevenlabs-voice-design.json
```

The generated report is:

```text
research/experiments/generated/VOICE-020-elevenlabs-voice-design-report.md
```

## Expected Next Step

Create or select English and German ElevenLabs voice candidates from the `VOICE-020` prompts, then run a live listening test on synthetic sales-agent text using the settings candidates.

Before the live test, remix both voices with the `VOICE-020` remix prompts at `Medium` prompt strength. If the change is too subtle, test `High`.

The next checkpoint should record human listening ratings before making any quality claim.
