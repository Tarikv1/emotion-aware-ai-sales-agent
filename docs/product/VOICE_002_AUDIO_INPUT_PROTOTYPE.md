# VOICE-002 Audio Input Prototype

## Purpose

VOICE-002 is the first recorded-audio input checkpoint for the vertical-agnostic sales agent.

It proves this flow:

```text
recorded audio file
-> transcript adapter
-> realtime sales-agent decision
-> VOICE-001 response packet
-> browser listener
```

The sales-agent core is still reusable across campaigns. VOICE-002 does not create a product-specific voice agent.

## Why Manual Transcript First

The first provider is `manual-transcript`.

This means the script accepts a recorded audio file plus a human-approved transcript. That choice is intentional:

- no cloud ASR dependency
- no API key required
- no provider lock-in
- no private customer recording needed for the first test
- transcript quality is controlled while the audio pipeline is being tested

Future ASR providers can replace the manual transcript adapter as long as they produce the same output boundary:

```text
audio -> transcript text + provider metadata
```

## Script

```text
scripts/run_voice_input_turn.py
```

Example:

```powershell
python scripts\run_voice_input_turn.py `
  --campaign campaign-prod-005-b2c-telecom `
  --stage relevance-check `
  --audio research\experiments\generated\VOICE-002-customer-placeholder.wav `
  --transcript "Nur wenn Sie garantieren koennen, dass es stabil ist." `
  --consent-confirmed `
  --out-json research\experiments\generated\VOICE-002-audio-input-packet.json `
  --listener-out research\experiments\generated\VOICE-002-listen.html
```

## Consent Gate

`--consent-confirmed` is required before the script runs.

This prevents recorded-audio experiments from becoming casual or accidental. For the current generated experiment, the audio is a synthetic placeholder WAV and does not contain a real person's voice.

## Packet Contract

The VOICE-002 packet includes:

- audio metadata
- consent metadata
- transcription provider metadata
- transcript text
- full VOICE-001 response packet
- listener output path
- trace metadata

The response packet reuses the existing realtime agent path, so `response_packet.tts_text` must match `response_packet.decision.agent_response`.

VOICE-002 now preserves campaign language through the recorded-audio path:

- transcript metadata carries the campaign language
- the realtime decision receives the campaign profile
- `response_packet.decision.response_language` must match the campaign language
- the generated listener uses a matching browser speech-synthesis language such as `de-DE`

## Generated Artifacts

```text
research/experiments/generated/VOICE-002-customer-placeholder.wav
research/experiments/generated/VOICE-002-audio-input-packet.json
research/experiments/generated/VOICE-002-listen.html
```

The listener page uses browser speech synthesis to play the selected agent response.

## Validation

Run:

```powershell
python scripts\validate_voice_002_audio_input.py
```

The validator checks consent gating, audio metadata, transcript routing, realtime decision reuse, listener generation, and secret-safe output.

## Next Milestones

- VOICE-003: automatic ASR provider comparison
- VOICE-004: local spoken turn loop
- VOICE-005: interruption and barge-in behavior
- VOICE-006: telephony/call-center integration plan
