# VOICE-009: TTS Provider Research

## Objective

Choose the first real TTS integration candidate for the voice-agent path without adding a vendor integration yet.

## Method

The checkpoint used a source-backed comparison matrix:

- official/primary sources only
- sources retrieved on 2026-05-01
- no API calls
- no API keys
- no audio upload
- no SDK installation
- German and English support required for any recommended first-integration candidate

The evaluator scored each candidate on:

- latency fit
- German and English support
- streaming fit
- voice quality fit
- sales voice control
- integration simplicity
- privacy and key safety
- telephony readiness
- thesis usefulness
- provider maturity fit

## Result

The generated report recommends:

- first integration candidate: `cartesia-sonic-3`
- quality/latency alternate: `elevenlabs-flash-v2-5`
- stack-simplest alternate: `openai-gpt-4o-mini-tts`
- enterprise alternate: `google-cloud-chirp-3-hd`
- enterprise backup: `amazon-polly-neural`
- offline research lane: `piper-local-tts`
- do-not-integrate-first candidate: `deepgram-aura-2`

## Interpretation

Cartesia is the best first pilot because the reviewed official sources combine the product's most important voice constraints:

- low-latency voice-agent positioning
- German and English support
- streaming TTS
- emotion and speed controls
- telephony-oriented audio options

This does not mean Cartesia is production-approved.

It means Cartesia is the first candidate worth testing with a real, carefully guarded latency smoke script.

## Safety Notes

VOICE-009 keeps cloud TTS blocked until:

- API keys are environment-only
- provider terms are reviewed
- generated response-text retention is reviewed
- timeout guardrails are present
- fallback remains available

Custom or cloned voices are blocked until:

- explicit voice consent exists
- legal review is complete
- provider-specific voice cloning rules are documented

## Known Limitation

This checkpoint relies on official provider claims and documentation.

It does not measure:

- real end-to-end latency from this workspace
- audio quality with the actual agent responses
- German pronunciation quality
- telephony playback quality
- provider reliability under repeated calls

Those belong in the next guarded integration checkpoint.

## Commands

```powershell
python scripts\validate_voice_009_tts_provider_research.py
```

## Generated Evidence

```text
research/experiments/generated/VOICE-009-tts-provider-research.json
research/experiments/generated/VOICE-009-tts-provider-research-report.md
```
