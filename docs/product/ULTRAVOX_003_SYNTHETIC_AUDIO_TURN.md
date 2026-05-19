# ULTRAVOX-003 Synthetic Audio Turn

## Purpose

ULTRAVOX-003 runs one approved synthetic customer-audio UltraVox hosted API turn.

It tests the missing part of `ULTRAVOX-002`: sending speech input into the server WebSocket and measuring whether UltraVox returns transcript and/or agent audio.

It is a bounded provider evaluation, not a product-runtime integration.

## Scope

The test:

- reads `ULTRAVOX_API_KEY` from environment or ignored local env file
- generates one local synthetic customer WAV using Windows SAPI, or copies the prior ignored `ULTRAVOX-002` synthetic audio fixture if local speech synthesis is unavailable
- converts the WAV to mono 48 kHz signed 16-bit PCM
- creates one UltraVox server-WebSocket call
- streams the synthetic customer PCM to UltraVox
- listens for transcript and agent audio
- closes the WebSocket
- deletes the UltraVox call after the test

It does not:

- upload real customer audio
- use voice cloning
- create a durable UltraVox console agent
- move sales policy, protected text, campaign logic, or evidence out of this repository
- change runtime behavior
- open `PROD-102`

## Local Env File

Machine-local key file:

```text
runtime/config/local/ultravox.env
```

This path is ignored by Git.

Expected shape:

```text
ULTRAVOX_API_KEY=...
```

Optional voice selection:

```text
ULTRAVOX_VOICE_ID_OR_NAME=...
```

If this is blank or absent, the harness omits `voice` and lets UltraVox use its default voice. Use only a public included UltraVox voice ID or unique voice name for this bounded test.

Do not put the key, raw voice value, full call ID, join URL, provider token, or provider transcript URLs in tracked docs, JSON, Markdown, reports, screenshots, or chat.

## Commands

Validate dry-run and forced-missing-key fallback without provider calls:

```powershell
python scripts\validate_ultravox_003_synthetic_audio_turn.py
```

Run the approved synthetic customer-audio live turn:

```powershell
python scripts\run_ultravox_003_synthetic_audio_turn.py `
  --live `
  --timeout-seconds 10
```

The command defaults to:

```text
--cases research/experiments/cases/ultravox-003-synthetic-audio-turn.json
--env-file runtime/config/local/ultravox.env
--out research/experiments/generated/ULTRAVOX-003/ULTRAVOX-003-synthetic-audio-turn.json
--report-out research/experiments/generated/ULTRAVOX-003/ULTRAVOX-003-synthetic-audio-turn-report.md
--audio-dir research/experiments/generated/ULTRAVOX-003/audio
```

## Generated Artifacts

```text
research/experiments/generated/ULTRAVOX-003/ULTRAVOX-003-synthetic-audio-turn.json
research/experiments/generated/ULTRAVOX-003/ULTRAVOX-003-synthetic-audio-turn-report.md
research/experiments/generated/ULTRAVOX-003/audio/ULTRAVOX-003-synthetic-customer-input.wav
research/experiments/generated/ULTRAVOX-003/audio/ULTRAVOX-003-agent-response-audio.wav
```

The audio files are ignored by Git through generated-audio ignore rules.

## Limitation

This is still one synthetic turn.

It can show whether UltraVox accepts our server-WebSocket audio stream and returns an agent response under bounded latency. It cannot prove production latency, interruption behavior, voice quality, cost stability, retention suitability, CRM integration fit, or whether UltraVox should replace the existing guarded runtime.

The recommendation can only change after repeated synthetic cases and a baseline comparison against the current `RESP-003` path.

If the script uses the `ULTRAVOX-002` synthetic audio fixture because local Windows speech synthesis is unavailable, the input is still synthetic and safe, but it no longer matches the `customer_text` field. Treat that result as an audio-transport and response-latency smoke, not a semantic customer-intent test.

## Current Live Result

The first approved synthetic customer-audio live turn ran on `2026-05-17`.

Result:

- local Windows SAPI speech generation failed in this process
- local COM SAPI fallback also failed
- the runner used the ignored `ULTRAVOX-002` synthetic audio fixture as the input WAV
- input text did not match the `customer_text` field because fixture fallback was used
- create-call HTTP status: `201`
- create-call latency: `529.111 ms`
- WebSocket connected: `true`
- synthetic PCM bytes sent, including trailing silence: `163200`
- transcript text received: `false`
- agent audio bytes received: `0`
- agent audio file created: `false`
- WebSocket text events received: `call_started`, `state`, `user_started_speaking`, `user_stopped_speaking`
- delete-call HTTP status: `204`
- delete attempt count: `2`
- voice selection: `ultravox-default`
- real customer audio uploaded: `false`
- voice cloning used: `false`
- runtime behavior changed: `false`
- opens `PROD-102`: `false`

Generated input audio:

```text
research/experiments/generated/ULTRAVOX-003/audio/ULTRAVOX-003-synthetic-customer-input.wav
```

No generated agent-response audio was created.

Interpretation:

This run proves the hosted API accepted the create-call request, opened the server WebSocket, received synthetic audio bytes, emitted user speech activity events, and deleted the call. It does not prove useful speech-to-speech latency yet, because no transcript or agent audio was received. The harness has been corrected so future receive-loop timeouts continue until the bounded deadline, but another live attempt requires separate approval.
