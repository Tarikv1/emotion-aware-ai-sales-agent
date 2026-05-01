# VOICE-007 Provider Readiness Gate

## Purpose

VOICE-007 decides whether ASR and TTS provider paths are ready for integration.

It does not connect to a real provider. It makes no API calls, uses no API keys, and uploads no audio.

The goal is to keep voice integration safe before the project moves from browser/local prototypes to production-relevant ASR and TTS services.

## Why This Exists

The live sales-agent path has a strict timing requirement:

```text
customer finishes speaking
-> agent starts responding within roughly 1-2 seconds
```

Real ASR/TTS providers add hidden risk:

- API key handling
- audio upload behavior
- text payload retention
- customer consent
- German and English quality
- streaming support
- fallback behavior
- provider latency
- provider terms

VOICE-007 makes those gates explicit before any provider key is introduced.

## Gate Rules

Every provider candidate must declare:

- ASR or TTS role
- German and English support
- whether an API key is required
- whether customer audio is uploaded
- consent requirement
- retention review requirement
- launch allowed status
- fallback path
- blockers
- recommended next action

Current global rules:

- first response target: `2000 ms`
- TTS start target: `500 ms`
- API key storage: `environment-only-not-repo`
- customer audio upload: blocked until privacy, consent, and retention review are documented
- fallback: every provider path must define a no-key fallback before integration

## Candidate Classes

VOICE-007 evaluates provider classes, not final vendors:

- `manual-transcript-baseline`
- `browser-speech-recognition-demo`
- `local-offline-asr-class`
- `cloud-batch-asr-class`
- `cloud-streaming-asr-class`
- `hybrid-edge-cloud-asr-class`
- `dry-run-tts-packet`
- `windows-sapi-local-tts`
- `browser-speech-synthesis-demo`
- `cloud-low-latency-tts-class`
- `cloud-voice-clone-tts-class`

## Current Recommendation

- ASR regression baseline: `manual-transcript-baseline`
- TTS regression baseline: `dry-run-tts-packet`
- Next no-key ASR prototype: `browser-speech-recognition-demo`
- Next no-key TTS prototype: `windows-sapi-local-tts`
- Production ASR follow-up after gates: `cloud-streaming-asr-class`
- Production TTS follow-up after gates: `cloud-low-latency-tts-class`

Cloud ASR/TTS paths remain blocked until key management, privacy review, retention review, and provider terms are documented.

Voice cloning is explicitly not ready. It remains blocked behind voice consent, legal review, retention review, and brand-risk review.

## Commands

Generate:

```powershell
python scripts\evaluate_voice_provider_readiness.py `
  --candidates research\experiments\cases\voice-007-provider-readiness-candidates.json `
  --out research\experiments\generated\VOICE-007-provider-readiness.json `
  --report-out research\experiments\generated\VOICE-007-provider-readiness-report.md
```

Validate:

```powershell
python scripts\validate_voice_007_provider_readiness.py
```

## Generated Artifacts

```text
research/experiments/generated/VOICE-007-provider-readiness.json
research/experiments/generated/VOICE-007-provider-readiness-report.md
```

## Product Boundary

VOICE-007 keeps the same product architecture:

```text
ASR adapter -> transcript boundary -> reusable sales-agent core -> TTS adapter
```

The reusable sales-agent core should not depend on a specific ASR or TTS provider.

Provider adapters may change, but they must preserve:

- consent metadata
- language metadata
- latency metadata
- fallback metadata
- no-secret repository policy

## Follow-Up

`VOICE-008` now performs the no-key local TTS smoke test using the existing `windows-sapi` path with dry-run fallback.

The next useful checkpoint is `VOICE-009`: vendor-specific TTS provider research before selecting a real integration candidate.
