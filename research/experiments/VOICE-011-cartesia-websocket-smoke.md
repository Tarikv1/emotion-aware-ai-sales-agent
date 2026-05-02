# VOICE-011 Cartesia WebSocket Smoke

## Objective

Prepare the first Cartesia WebSocket TTS smoke test for longer German and English samples while preserving the no-key/no-provider-call default.

## Motivation

VOICE-010 showed that the Cartesia bytes endpoint can generate audio, but German first-audio timing stayed above the `500 ms` TTS-start target and the longer-term German quality question remains open.

Cartesia's WebSocket endpoint is closer to a live voice-agent setup because it can keep one connection open and receive text in chunks.

## Design

- Four synthetic quality samples:
  - two German
  - two English
  - objection-handling and bridge/handoff language
- Dry-run by default.
- Live mode requires:
  - `--live`
  - `CARTESIA_API_KEY`
  - either language-specific voice IDs or one generic voice ID
- Optional language-specific voice variables:
  - `CARTESIA_VOICE_ID_DE`
  - `CARTESIA_VOICE_ID_EN`
- Fallback:
  - `text-only-tts-packet`
- Max timeout:
  - `10 seconds`

## Validation

Run:

```powershell
python scripts\validate_voice_011_cartesia_websocket_smoke.py
```

The validator confirms:

- the script and case file exist
- the default path makes no WebSocket connection
- simulated live mode with missing keys falls back
- no audio is created during validation
- no key or voice ID value is logged
- request previews are redacted
- human quality review remains required

## Dry-Run Result

Generated artifacts:

```text
research/experiments/generated/VOICE-011-cartesia-websocket-smoke.json
research/experiments/generated/VOICE-011-cartesia-websocket-smoke-report.md
```

Dry-run summary:

- cases: `4`
- German cases: `2`
- English cases: `2`
- WebSocket connections attempted: `0`
- API calls made: `0`
- audio files created: `0`
- fallback count: `4`
- human audio-quality ratings recorded: `false`

## Live-Test Interpretation

When provider credentials are available, the live run should answer:

- Does WebSocket reduce first-audio timing compared with the bytes endpoint?
- Do longer German samples still sound muffled?
- Does using language-specific voice IDs improve quality?
- Are English samples natural enough for sales-call pacing?
- Should Cartesia remain the first provider candidate, or should ElevenLabs be compared next?

## Safety Notes

- Do not paste API keys into chat.
- Do not commit generated WAV files.
- Do not use cloned voices.
- Do not upload customer audio.
- Do not claim audio quality until a human listens to the generated files.
