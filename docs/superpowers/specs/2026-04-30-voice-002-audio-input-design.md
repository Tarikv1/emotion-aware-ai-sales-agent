# VOICE-002 Audio Input Prototype Design

Date: 2026-04-30

## Purpose

VOICE-002 adds the first audio-input layer around the existing realtime sales-agent core. The goal is to prove that a recorded customer audio artifact can be associated with a transcript, passed through the reusable realtime agent, and produce the same voice-response packet used by VOICE-001.

This milestone is still vertical-agnostic. It must not introduce an insurance-only, B2B-only, or product-specific voice path.

## Scope

VOICE-002 covers recorded audio ingestion with a human-approved transcript:

```text
recorded audio file
-> manual-transcript STT adapter
-> realtime sales-agent decision
-> VOICE-001 response packet
-> browser listener artifact
```

This is not live call handling and not production ASR.

## Recommended Approach

Use a `manual-transcript` provider first.

This provider requires an audio file plus a transcript supplied by CLI text or a transcript file. It lets the project validate the audio-input pipeline, consent metadata, transcript-to-agent flow, and listener output without cloud dependencies, API keys, or recording real customers.

Future ASR providers can implement the same boundary:

```text
audio file -> transcript text + confidence + provider metadata
```

## Architecture

The audio-input script should sit above the existing realtime turn and VOICE-001 response utilities:

```text
audio file
  |
transcription adapter
  |
transcript text
  |
realtime turn engine
  |
VOICE-001 response packet
  |
VOICE-002 packet and listener
```

The reusable sales-agent core remains responsible for classification, strategy, next action, escalation, and call control.

The VOICE-002 layer is responsible only for:

- validating that an audio file exists
- storing safe audio metadata
- requiring explicit consent confirmation for recorded-audio experiments
- producing or accepting transcript text
- passing transcript text into the realtime agent
- writing traceable metadata and a local listener artifact

## Consent And Safety

VOICE-002 must not use private customer recordings unless explicit permission is documented. The first generated fixture should be synthetic placeholder audio and should not contain a real person's voice.

Every VOICE-002 packet should record:

- provider name
- whether consent was confirmed
- audio path
- audio format
- file size
- duration when available
- transcript source
- whether an API key is required

## Out Of Scope

- live microphone capture
- live telephony
- automatic cloud transcription
- voice cloning
- storing private customer recordings
- real-time interruption handling
- production German ASR evaluation

## Validation

The validator should generate or use a synthetic placeholder WAV, run the audio-input script with a known transcript, and assert:

- the script exists
- consent confirmation is required
- audio metadata is captured
- transcript text reaches the realtime agent
- the resulting response packet matches the VOICE-001 contract
- the listener artifact contains the transcript and agent response
- no secret-like API key patterns are written

