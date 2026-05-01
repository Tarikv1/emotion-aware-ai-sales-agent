# VOICE-010 Cartesia TTS Smoke Test

## Purpose

VOICE-010 adds the first Cartesia-specific TTS smoke harness.

It is intentionally safe before any key is provided:

- default mode makes no provider call
- no API key is stored
- no API key is printed
- no customer audio is uploaded
- no generated text is sent to Cartesia unless `--live` is explicitly used
- no cloned or custom voice is used
- every provider path has a text-only fallback
- every live request has a bounded timeout

## Why Bytes First

Cartesia supports Bytes, SSE, and WebSocket TTS paths.

VOICE-010 starts with the HTTP `tts/bytes` endpoint because it proves the basic provider contract with fewer moving parts:

- environment-only key handling
- provider request body construction
- bounded timeout behavior
- local audio-file output
- latency metadata
- fallback behavior

WebSocket streaming remains the right later path for incremental LLM speech, but it should come after the first provider smoke test is stable.

Relevant Cartesia docs:

- [Text to Speech Bytes](https://docs.cartesia.ai/api-reference/tts/bytes)
- [Text to Speech WebSocket](https://docs.cartesia.ai/api-reference/tts/websocket)
- [Compare TTS Endpoints](https://docs.cartesia.ai/api-reference/tts/compare-tts-endpoints)

## Guardrails

VOICE-010 requires:

- `CARTESIA_API_KEY` only in the local environment
- `CARTESIA_VOICE_ID` only in the local environment
- `--live` before any provider call is attempted
- `--timeout-seconds` no greater than `10`
- synthetic German and English prompts only
- text-only fallback if the key, voice ID, request, or audio output fails

Generated audio files are ignored by Git:

```text
research/experiments/generated/VOICE-010-*.wav
```

## Default Dry Run

Run without a key:

```powershell
python scripts\run_voice_010_cartesia_tts_smoke.py
```

Validate:

```powershell
python scripts\validate_voice_010_cartesia_tts_smoke.py
```

The validator checks:

- default dry-run mode
- simulated live mode with missing key
- German and English coverage
- no provider API calls during validation
- no audio files during validation
- no secret-like tokens in generated outputs

## Live Smoke Run

Only after obtaining a Cartesia key and selecting a Cartesia voice ID:

```powershell
$cartesiaKey = Read-Host "Cartesia API key"
$cartesiaVoiceId = Read-Host "Cartesia voice ID"
Set-Item -Path Env:CARTESIA_API_KEY -Value $cartesiaKey
Set-Item -Path Env:CARTESIA_VOICE_ID -Value $cartesiaVoiceId

python scripts\run_voice_010_cartesia_tts_smoke.py --live --timeout-seconds 8

Remove-Item Env:CARTESIA_API_KEY
Remove-Item Env:CARTESIA_VOICE_ID
$cartesiaKey = $null
$cartesiaVoiceId = $null
```

The generated report should then show:

- API calls made: `2`
- audio files created: `2`, if both provider calls succeed
- time-to-first-audio-byte metadata
- total provider latency metadata

If anything fails, the script should still produce a report and fall back to `text-only-tts-packet`.

## Generated Artifacts

```text
research/experiments/cases/voice-010-cartesia-tts-smoke.json
research/experiments/generated/VOICE-010-cartesia-tts-smoke.json
research/experiments/generated/VOICE-010-cartesia-tts-smoke-report.md
```

## Product Meaning

VOICE-010 does not change the sales-agent core.

The reusable sales-agent core still chooses the response from campaign context, guardrails, language, and call-control logic. Cartesia only receives the approved `decision.agent_response` as TTS text when a live run is explicitly requested.

This keeps the architecture vertical-agnostic:

- same agent core
- same campaign profiles
- same bilingual runtime checks
- provider-specific audio layer behind a guarded adapter

## Next Work

After a successful live Cartesia smoke run:

- listen to both generated audio files
- record German pronunciation quality
- record English pronunciation quality
- compare measured latency to the `500 ms` TTS-start target
- decide whether to proceed to WebSocket streaming as `VOICE-011`
- keep ElevenLabs as the comparison candidate if Cartesia quality or latency is not convincing
