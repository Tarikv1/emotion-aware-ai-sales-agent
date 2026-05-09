# VOICE-009 TTS Provider Research

## Purpose

VOICE-009 selects the best first real TTS integration candidate before any vendor SDK, API key, or audio-generation call is added.

This checkpoint exists because VOICE-008 proved that local Windows SAPI is safe as a no-key attempt, but not reliable enough to be the only audible-output path.

## Scope

VOICE-009 is research only.

It:

- reviews official/primary provider sources retrieved on 2026-05-01
- compares German and English TTS readiness
- keeps the first response target at `2000 ms`
- keeps the TTS start target at `500 ms`
- stores no API key
- makes no API call
- uploads no audio
- blocks cloned, custom, or customer-like voices until consent and legal review
- requires local/browser/text-only fallback before integration

## Evaluated Candidates

The current provider matrix evaluates:

- `cartesia-sonic-3`
- `elevenlabs-flash-v2-5`
- `openai-gpt-4o-mini-tts`
- `google-cloud-chirp-3-hd`
- `azure-ai-speech-neural`
- `amazon-polly-neural`
- `deepgram-aura-2`
- `piper-local-tts`

## Recommendation

Recommended first integration candidate:

- `cartesia-sonic-3`

Why:

- official docs support German and English
- official docs describe streaming TTS for real-time voice-agent use
- official materials state a low time-to-first-audio target
- WebSocket output can support incremental LLM responses
- the model exposes voice-agent-relevant controls such as speed and emotion
- telephony-oriented output options are available

Important caveat:

- this is not a launch approval
- Cartesia still needs an API key, environment-only key storage, provider-terms review, text-retention review, and a latency smoke test
- voice cloning must not be used in the first integration

## Alternates

- Quality/latency alternate: `elevenlabs-flash-v2-5`
- Stack-simplest alternate: `openai-gpt-4o-mini-tts`
- Enterprise alternate: `google-cloud-chirp-3-hd`
- Enterprise backup: `amazon-polly-neural`
- Offline research lane: `piper-local-tts`
- Do not integrate first: `deepgram-aura-2`

Deepgram Aura is not recommended first because the official TTS language list reviewed for this checkpoint did not confirm German support.

## Commands

Generate:

```powershell
python scripts\evaluate_voice_009_tts_provider_research.py `
  --candidates research\experiments\cases\voice-009-tts-provider-research.json `
  --out research/experiments/generated/VOICE-009/VOICE-009-tts-provider-research.json `
  --report-out research/experiments/generated/VOICE-009/VOICE-009-tts-provider-research-report.md
```

Validate:

```powershell
python scripts\validate_voice_009_tts_provider_research.py
```

## Generated Artifacts

```text
research/experiments/generated/VOICE-009/VOICE-009-tts-provider-research.json
research/experiments/generated/VOICE-009/VOICE-009-tts-provider-research-report.md
```

## Product Meaning

VOICE-009 keeps the product vertical-agnostic.

The voice layer is not insurance-specific and not tied to one campaign. It should speak the response chosen by the reusable sales-agent core, using the active `SalesCampaign` language, guardrails, disclosures, and fallback rules.

The next integration should therefore test provider latency and audio quality against the same bilingual sales-agent response contract, not against a separate hardcoded voice demo.

## Next Work

VOICE-010 now adds the first Cartesia-specific TTS smoke harness.

The committed VOICE-010 artifact is intentionally dry-run by default. A live Cartesia run still requires:

- the API key is provided via environment variable only
- the selected Cartesia voice ID is provided via environment variable only
- no key is written to the repository
- the test uses synthetic prompts only
- no customer audio is uploaded
- response text retention assumptions are documented
- timeout guardrails prevent long-attached shell calls
- fallback to text-only packet remains available
