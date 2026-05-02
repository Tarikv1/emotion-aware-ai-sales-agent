# VOICE-017 Live A/B Audio

## Objective

Prepare a guarded live-capable A/B audio experiment comparing plain guarded text against VOICE-016 prosody-shaped text.

## Scope

Default mode is dry-run.

The generated checkpoint does not call providers, require API keys, upload customer audio, clone voices, or create audio files.

Live mode is available only with explicit `--live`, provider selection, environment-only keys, and bounded timeout.

## Method

The runner reads:

```text
research/experiments/generated/VOICE-016-provider-prosody-rendering.json
```

It selects four cases:

- two German
- two English
- two pure freeform objection-handling cases
- two mixed cases that include protected campaign/disclosure text

For each case, it prepares:

- plain ElevenLabs input
- prosody ElevenLabs input
- plain Cartesia input
- prosody Cartesia input

## Current Live Result

The first live run used ElevenLabs only with `--limit 2`.

```text
cases: 2
German: 1
English: 1
providers: elevenlabs
A/B variants: 4
plain variants: 2
prosody variants: 2
live call requested: true
API calls made: 4
audio files created: 4
fallback count: 0
customer audio uploaded: false
voice cloning used: false
human ratings recorded: true
quality claim allowed: true, scoped to this two-case ElevenLabs run
```

The project owner listened to the generated plain/prosody pairs and strongly preferred the prosody variants.

Allowed claim:

```text
In the VOICE-017 two-case ElevenLabs live A/B run, prosody-shaped speech was strongly preferred over plain speech by the human listener.
```

This should not yet be generalized to all providers, voices, scripts, languages, or customers.

## Dry-Run Baseline Result

```text
cases: 4
German: 2
English: 2
providers: elevenlabs, cartesia
A/B variants: 16
plain variants: 8
prosody variants: 8
live call requested: false
API calls made: 0
audio files created: 0
fallback count: 16
customer audio uploaded: false
voice cloning used: false
quality claim allowed: false
```

## Validation

The validator checks:

- dry-run creates all expected A/B entries
- forced-missing-key live mode makes no provider calls for ElevenLabs
- forced-missing-key live mode makes no provider calls for Cartesia
- request previews are redacted
- plain variants contain no provider prosody tags
- prosody variants contain expected provider-safe break tags
- generated artifacts contain no API keys or voice IDs
- no quality claim is allowed without human listening ratings

## Interpretation

VOICE-017 has now produced live ElevenLabs audio and a first bounded human listening result.

The early result supports keeping the VOICE-015/VOICE-016 prosody stack. The next question is how much prosody is optimal, not whether prosody matters at all.

## Artifacts

```text
scripts/run_voice_017_live_ab_audio.py
scripts/validate_voice_017_live_ab_audio.py
research/experiments/cases/voice-017-live-ab-audio.json
research/experiments/generated/VOICE-017-live-ab-audio.json
research/experiments/generated/VOICE-017-live-ab-audio-report.md
docs/product/VOICE_017_LIVE_AB_AUDIO.md
```

## Next Step

Expand the live A/B to the remaining selected cases or record a second listener before treating the result as stronger evaluation evidence.
