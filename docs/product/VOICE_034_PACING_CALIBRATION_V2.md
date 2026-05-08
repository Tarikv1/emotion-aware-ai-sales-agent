# VOICE-034 Pacing Calibration V2

VOICE-034 tunes the provider-facing pacing layer after `RESP-002` has already produced guarded text, speech realism, interaction prosody, imperfections, provider-neutral prosody, and provider rendering.

It does not rewrite the agent answer. It only calibrates provider-rendered break tags and ElevenLabs speed settings for eligible freeform segments.

## Purpose

Recent listening feedback:

- English and German voices are improving.
- The agent still sounds too evenly paced.
- The German output had too much gap between words.
- The voice should be a bit faster and more sales-call-like without becoming rushed.
- Later RESP-003 A/B listening found the current shaped German runtime too fast, so German now uses a slower provider speed profile than English.
- The next RESP-003 listening pass with a better German voice found German roboticness mostly resolved, with only a tiny speed lift needed.
- The English trust-repair sample exposed a swallowed transition, but lowering the speed too far made the voice flatter and more robotic. Trust repair now keeps a lively bounded pace while VOICE-035 fixes the brittle transition text.

VOICE-034 focuses on pacing only. It intentionally does not add more fillers or new emotional wording.

## Behavior

For eligible freeform segments:

- increases ElevenLabs speed slightly
- compresses provider break tags
- applies a tighter German gap profile
- keeps variation deterministic for the same input

For protected segments:

- no speed calibration
- no break-tag calibration
- no text change

Protected text includes campaign questions, disclosures, claim boundaries, human handoff, appointment confirmation, do-not-call, and hangup responses.

## Bounds

English:

- speed: `1.07` to `1.15`
- trust-repair reassurance cap: `1.13` to `1.14`
- break bounds: `80` to `240` ms

German:

- speed: `0.975` to `1.04`
- break bounds: `110` to `280` ms
- German word-gap reduction remains bounded, but no longer accelerates the voice above normal sales-call pace

## Command

```powershell
python scripts\run_voice_034_pacing_calibration.py
```

Default output:

```text
research\experiments\generated\VOICE-034-pacing-calibration-v2\
```

## Runtime Position

VOICE-034 is wired into `RESP-002` after provider rendering and before `RESP-003` selects the TTS input.

That means later dry-run/live TTS can use:

- calibrated provider-rendered text
- calibrated ElevenLabs speed settings

Later listening-feedback layers may still make narrower provider-facing adjustments. For German, VOICE-036 can relax the final provider speed after VOICE-034/VOICE-035 when a connected phrase sounds too compressed; VOICE-034 validation therefore checks the VOICE-034 calibration packet separately from the final downstream provider packet.

## Boundary

- No provider calls.
- No generated audio.
- No customer/private audio.
- No transcription.
- No voice cloning.
- No protected text rewriting.
- No final-response rewriting.

## Validation

```powershell
python scripts\validate_voice_034_pacing_calibration.py
```

## Listening Result

The short RESP-003 live listening check with local improved ElevenLabs voice IDs confirmed that VOICE-034 should remain unchanged for now.

Observed result:

- German pacing and word gaps sounded good.
- English pacing and pause timing sounded good.
- On second listen, German also still had some robotic quality.
- The remaining roboticness is not primarily a pause-length problem.
- VOICE-035 now handles the next target: bilingual connected speech, word-to-word flow, phrase rhythm, and reducing isolated-word delivery while keeping the agent clear and professional in English and German.

Review artifact:

```text
research/experiments/generated/RESP-003/voice-034-listening-check/human-listening-review.md
```
