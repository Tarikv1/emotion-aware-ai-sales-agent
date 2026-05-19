# ULTRAVOX-002 Synthetic Live Smoke

## Purpose

ULTRAVOX-002 runs the first approved UltraVox hosted API smoke test.

It is a bounded provider check, not a product-runtime integration.

## Scope

The smoke test:

- reads `ULTRAVOX_API_KEY` from environment or ignored local env file
- creates one UltraVox server-WebSocket call
- uses an agent-first synthetic sentence
- receives first audio bytes from UltraVox when the call succeeds
- closes the WebSocket
- deletes the UltraVox call after the test

It does not:

- upload customer audio
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

If this is blank or absent, the smoke harness omits `voice` and lets UltraVox use its default voice. UltraVox's Create Call API accepts `voice` as a voice ID or unique voice name. Do not use external provider voice IDs or cloned voices for this smoke.

Do not put the key in tracked docs, JSON, Markdown, reports, screenshots, or chat.

## Commands

Validate dry-run and forced-missing-key fallback without provider calls:

```powershell
python scripts\validate_ultravox_002_synthetic_live_smoke.py
```

Run the approved synthetic live smoke:

```powershell
python scripts\run_ultravox_002_synthetic_live_smoke.py `
  --live `
  --timeout-seconds 8
```

The command defaults to:

```text
--cases research/experiments/cases/ultravox-002-synthetic-live-smoke.json
--env-file runtime/config/local/ultravox.env
--out research/experiments/generated/ULTRAVOX-002/ULTRAVOX-002-synthetic-live-smoke.json
--report-out research/experiments/generated/ULTRAVOX-002/ULTRAVOX-002-synthetic-live-smoke-report.md
```

## Generated Artifacts

```text
research/experiments/generated/ULTRAVOX-002/ULTRAVOX-002-synthetic-live-smoke.json
research/experiments/generated/ULTRAVOX-002/ULTRAVOX-002-synthetic-live-smoke-report.md
research/experiments/generated/ULTRAVOX-002/audio/ULTRAVOX-002-agent-first-audio.wav
```

The audio file is ignored by Git through generated-audio ignore rules.

## Limitation

This is an agent-first audio smoke test.

It proves whether the hosted UltraVox API key, call creation, server WebSocket join, first agent audio, and cleanup path work. It does not yet prove full speech-to-speech latency because it does not send synthetic customer speech into UltraVox.

That next step needs a separate synthetic-audio input test after this smoke test passes.

## Current Live Result

The first approved synthetic live smoke ran on `2026-05-17`.

Result:

- create-call HTTP status: `201`
- create-call latency: `568.868 ms`
- WebSocket connected: `true`
- time to first audio byte: `581.866 ms`
- total listen latency: `1189.897 ms`
- audio bytes received: `48000`
- audio file created: `true`
- voice selection: `ultravox-default`
- customer audio uploaded: `false`
- voice cloning used: `false`
- runtime behavior changed: `false`
- opens `PROD-102`: `false`
- initial delete returned `425` because the call was still ongoing or unbilled
- follow-up cleanup matched the call by suffix and deleted it with HTTP status `204`

Generated audio:

```text
research/experiments/generated/ULTRAVOX-002/audio/ULTRAVOX-002-agent-first-audio.wav
```
