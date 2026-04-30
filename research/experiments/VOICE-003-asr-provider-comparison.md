# VOICE-003 ASR Provider Comparison

## Experiment Goal

Compare speech-to-text provider families before connecting the product to a real ASR provider.

The experiment is intentionally deterministic and provider-safe. It makes no API calls and uploads no audio.

## Input

- Candidate file: `research/experiments/cases/voice-003-asr-provider-candidates.json`
- Scoring script: `scripts/compare_asr_providers.py`
- Candidate count: `6`
- Score scale: `1=weak fit, 5=strong fit`

## Compared Provider Families

- `manual-transcript-baseline`
- `browser-speech-recognition-demo`
- `local-offline-asr-class`
- `cloud-batch-asr-class`
- `cloud-streaming-asr-class`
- `hybrid-edge-cloud-asr-class`

## Result

The generated comparison recommends:

- Regression baseline: `manual-transcript-baseline`
- Next no-key prototype: `browser-speech-recognition-demo`
- Production follow-up class: `cloud-streaming-asr-class`

The manual transcript baseline scores highest because it is reliable, private, no-key, and useful for thesis evaluation. However, it is not automatic ASR, so it remains the regression baseline rather than the next automation prototype.

The browser speech recognition demo is the recommended next automation path because it can test spoken transcript flow without adding API-key handling or cloud provider integration yet.

Cloud streaming ASR remains the likely production-relevant class for low-latency call-center use, but it should wait until key management, privacy review, data retention, consent, and provider terms are handled deliberately.

## Generated Artifacts

```text
research/experiments/generated/VOICE-003-asr-provider-comparison.json
research/experiments/generated/VOICE-003-asr-provider-comparison-report.md
```

## Interpretation

VOICE-003 gives the project a clear next move:

1. Keep VOICE-002 manual transcript as the baseline.
2. Build a no-key browser speech recognition prototype next.
3. Use cloud streaming ASR only after explicit security and privacy decisions.

This preserves the reusable sales-agent core and keeps ASR as a swappable adapter.

