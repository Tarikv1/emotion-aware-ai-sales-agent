# VOICE-016 Provider Prosody Rendering

## Objective

Render the VOICE-015 provider-neutral prosody plan into concrete provider-specific text/request previews for Cartesia and ElevenLabs.

## Scope

VOICE-016 is offline.

It does not call providers, require keys, upload customer audio, clone voices, or create audio files.

## Method

The runner reads:

```text
research/experiments/generated/VOICE-015-prosody-naturalness.json
```

For each case, it creates:

- plain text baseline
- Cartesia rendered text
- ElevenLabs rendered text
- mapped cue counts
- unsupported cue counts
- per-segment rendering records

Rendering happens per segment so protected campaign and compliance segments cannot receive accidental provider tags.

## Result

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

Provider mapping:

```text
Cartesia mapped: pause 5, rate 5, emphasis 5, stretch 1
Cartesia unsupported: pitch 6
ElevenLabs mapped: pause 5, rate 5, stretch 1
ElevenLabs unsupported: pitch 6, emphasis 5
```

## Interpretation

Cartesia currently receives richer direct markup because Sonic 3 documents break, speed, and volume-style controls.

ElevenLabs receives a more conservative rendering: break tags, request-level speed, and no fake pitch or emphasis markup. This is intentional. Unsupported cues are recorded rather than forced through unreliable text tricks.

## Limitations

VOICE-016 still does not prove which provider sounds better.

It only proves that the project can create provider-specific inputs safely and inspect them before live synthesis.

## Artifacts

```text
scripts/provider_prosody_rendering.py
scripts/run_voice_016_provider_prosody_rendering.py
scripts/validate_voice_016_provider_prosody_rendering.py
research/experiments/cases/voice-016-provider-prosody-rendering.json
research/experiments/generated/VOICE-016-provider-prosody-rendering.json
research/experiments/generated/VOICE-016-provider-prosody-rendering-report.md
docs/product/VOICE_016_PROVIDER_PROSODY_RENDERING.md
```

## Next Step

Create `VOICE-017`: a live audio A/B harness that compares plain text against VOICE-016 prosody-shaped text for the strongest available provider.
