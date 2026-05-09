# VOICE-015 Prosody Naturalness

## Objective

Add a controlled prosody layer that makes voice output less robotic by planning pause, rate, emphasis, pitch, and rare stretch cues for eligible freeform speech.

## Scope

VOICE-015 is provider-neutral and text-only.

It does not call Cartesia, ElevenLabs, OpenAI, or any other provider. It does not require an API key, upload customer audio, or use voice cloning.

## Method

The experiment uses eight synthetic bilingual cases:

- four English cases
- four German cases
- freeform objection handling
- freeform transitions and explanations
- protected campaign questions
- protected disclosures
- protected do-not-call and hangup text
- strict insurance boundary text
- disabled clean-script profile

The renderer creates a clean `tts_text`, a review-only `debug_text`, and a structured `prosody_plan`.

## Result

Generated summary:

```text
cases: 8
German: 4
English: 4
total cues: 22
pause cues: 5
pitch cues: 6
rate cues: 5
emphasis cues: 5
stretch cues: 1
protected-segment cues: 0
validation passed: 8 / 8
```

## Interpretation

The project now has a controllable layer for the issues noticed during listening:

- overly stable pace
- flat pitch
- uniform spacing
- lack of human thinking pauses
- no emphasis on important words
- no bounded word-end hesitation or stretching

The important methodological choice is that randomness is seeded and bounded. The output can vary in a human-like way without becoming impossible to reproduce or audit.

## Limitations

VOICE-015 does not prove that the audio sounds better yet.

It only proves that the project can create safe provider-neutral cues. A later provider test must synthesize these cues through ElevenLabs or Cartesia and compare them against plain guarded text.

## Artifacts

```text
scripts/prosody_naturalness.py
scripts/run_voice_015_prosody_naturalness.py
scripts/validate_voice_015_prosody_naturalness.py
research/experiments/cases/voice-015-prosody-naturalness.json
research/experiments/generated/VOICE-015/VOICE-015-prosody-naturalness.json
research/experiments/generated/VOICE-015/VOICE-015-prosody-naturalness-report.md
docs/product/VOICE_015_PROSODY_NATURALNESS_LAYER.md
```

## Next Step

Create a provider-specific rendering checkpoint that compares plain text against VOICE-015 prosody-shaped text using the strongest available TTS provider.
