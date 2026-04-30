# VOICE-003 ASR Provider Comparison

## Purpose

VOICE-003 compares speech-to-text provider families before the project connects to a real ASR provider.

This keeps the architecture vertical-agnostic and provider-safe. The sales-agent core should only receive transcript text and provider metadata. It should not care whether the transcript came from a browser demo, local/offline model, cloud streaming API, cloud batch API, or human-approved transcript.

## Why This Comes Before Real ASR

Real ASR integration has hidden decisions:

- API key handling
- audio upload rules
- data retention
- latency
- German-language quality
- streaming partial transcripts
- interruption handling
- customer consent

VOICE-003 makes those tradeoffs explicit before any provider is connected.

## Script

```text
scripts/compare_asr_providers.py
```

Example:

```powershell
python scripts\compare_asr_providers.py `
  --providers research\experiments\cases\voice-003-asr-provider-candidates.json `
  --out research\experiments\generated\VOICE-003-asr-provider-comparison.json `
  --report-out research\experiments\generated\VOICE-003-asr-provider-comparison-report.md
```

No API calls are made and no audio is uploaded.

## Candidate Families

VOICE-003 compares:

- manual transcript baseline
- browser speech recognition demo
- local/offline ASR class
- cloud batch ASR class
- cloud streaming ASR class
- hybrid edge/cloud ASR class

## Current Recommendation

The comparison recommends:

- Regression baseline: `manual-transcript-baseline`
- Next no-key prototype: `browser-speech-recognition-demo`
- Production follow-up class: `cloud-streaming-asr-class`

This means we should keep VOICE-002's `manual-transcript` path as the evaluation baseline, then try a browser-based speech recognition demo before connecting cloud ASR.

## Adapter Boundary

Every future ASR adapter should output:

```text
audio input
-> transcript text
-> confidence/quality metadata
-> provider metadata
-> consent/privacy metadata
```

Downstream realtime sales-agent logic should consume only that boundary.

## Generated Artifacts

```text
research/experiments/generated/VOICE-003-asr-provider-comparison.json
research/experiments/generated/VOICE-003-asr-provider-comparison-report.md
```

## Validation

Run:

```powershell
python scripts\validate_voice_003_asr_provider_comparison.py
```

The validator confirms provider-family coverage, recommendation logic, cloud-gating, generated artifacts, and secret-safe output.

