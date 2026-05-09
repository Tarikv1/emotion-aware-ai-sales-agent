# VOICE-008 Local TTS Smoke Test

## Purpose

VOICE-008 tests the next no-key audible-output path after the provider-readiness gate.

It attempts local Windows SAPI TTS for German and English agent responses, then falls back to dry-run TTS metadata if local audio generation is unavailable.

This is still not a cloud voice integration.

## Why This Exists

VOICE-007 recommended:

- TTS regression baseline: `dry-run-tts-packet`
- Next no-key TTS prototype: `windows-sapi-local-tts`
- Production TTS follow-up after gates: `cloud-low-latency-tts-class`

VOICE-008 checks the no-key local path before introducing cloud provider keys or sending generated response text to a third-party service.

## Safety Rules

VOICE-008 must:

- make no API calls
- require no API key
- use no cloud provider
- upload no customer audio
- use only synthetic test voice metadata
- preserve `decision.agent_response` as `tts_text`
- preserve German and English `response_language`
- define a dry-run fallback for every case

Generated WAV files are machine-local smoke artifacts and are ignored by Git.

## Current Result

The current generated run attempted `windows-sapi` for:

- one German campaign response
- one English campaign response

Result in this workspace:

- Audio files created: `0`
- Dry-run fallback count: `2`
- Response-language matches: `2 / 2`
- TTS text matches decision: `2 / 2`

Windows SAPI was reachable, but no usable local voice was installed or allowed by the current security setting. This is a valid smoke-test result: the local provider path is gated and the fallback is safe.

## Commands

Run:

```powershell
python scripts\run_voice_008_local_tts_smoke.py `
  --out research/experiments/generated/VOICE-008/VOICE-008-local-tts-smoke.json `
  --report-out research/experiments/generated/VOICE-008/VOICE-008-local-tts-smoke-report.md
```

Validate:

```powershell
python scripts\validate_voice_008_local_tts_smoke.py
```

The validator checks both:

- forced fallback mode
- normal local TTS attempt mode

## Generated Artifacts

```text
research/experiments/generated/VOICE-008/VOICE-008-local-tts-smoke.json
research/experiments/generated/VOICE-008/VOICE-008-local-tts-smoke-report.md
```

If local SAPI voices are available on a machine, the script may also create local WAV artifacts under `research/experiments/generated/VOICE-008/`, for example:

```text
research/experiments/generated/VOICE-008/<local-sapi-smoke-output>.wav
```

Those WAV files are intentionally ignored by Git because they depend on the local machine's installed voices. They are not present in this workspace because the current run fell back to dry-run metadata.

## Product Meaning

VOICE-008 shows that a local no-key TTS attempt can be placed behind the same voice packet contract as dry-run TTS.

It also shows that local OS TTS is not reliable enough to assume as the only audible-output path for this project. The next voice checkpoint should compare real provider candidates or install/evaluate a local TTS engine with known German and English voice support.

## Next Work

VOICE-009 has now performed vendor-specific TTS provider research before integration.

The recommended first integration candidate is `cartesia-sonic-3`, with `elevenlabs-flash-v2-5` as the quality/latency alternate and `openai-gpt-4o-mini-tts` as the stack-simplest alternate.

VOICE-010 should run a guarded real-provider TTS latency smoke test only after API-key storage, text-retention review, timeout behavior, and fallback behavior are documented.
