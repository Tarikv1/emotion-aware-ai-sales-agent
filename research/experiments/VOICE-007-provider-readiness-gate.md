# VOICE-007 Provider Readiness Gate

## Experiment Goal

Evaluate whether ASR and TTS provider paths are ready for integration without making any provider calls.

The experiment is intentionally deterministic:

- no API key required
- no API calls made
- no audio uploaded
- no vendor commitment

## Input

- Candidate file: `research/experiments/cases/voice-007-provider-readiness-candidates.json`
- Evaluator: `scripts/evaluate_voice_provider_readiness.py`
- Validator: `scripts/validate_voice_007_provider_readiness.py`
- Candidate count: `11`
- Runtime languages: German and English

## Compared Provider Classes

ASR candidates:

- `manual-transcript-baseline`
- `browser-speech-recognition-demo`
- `local-offline-asr-class`
- `cloud-batch-asr-class`
- `cloud-streaming-asr-class`
- `hybrid-edge-cloud-asr-class`

TTS candidates:

- `dry-run-tts-packet`
- `windows-sapi-local-tts`
- `browser-speech-synthesis-demo`
- `cloud-low-latency-tts-class`
- `cloud-voice-clone-tts-class`

## Result

Generated recommendations:

- ASR regression baseline: `manual-transcript-baseline`
- TTS regression baseline: `dry-run-tts-packet`
- Next no-key ASR prototype: `browser-speech-recognition-demo`
- Next no-key TTS prototype: `windows-sapi-local-tts`
- Production ASR follow-up after gates: `cloud-streaming-asr-class`
- Production TTS follow-up after gates: `cloud-low-latency-tts-class`

Cloud paths remain blocked until:

- API key handling is defined
- privacy review is complete
- retention review is complete
- provider terms are reviewed
- latency can be measured safely

Voice cloning remains explicitly blocked because it needs voice consent, legal review, retention review, and brand-risk review.

## Generated Artifacts

```text
research/experiments/generated/VOICE-007-provider-readiness.json
research/experiments/generated/VOICE-007-provider-readiness-report.md
```

## Interpretation

VOICE-007 confirms that the next step should not be a random cloud integration.

The safe next path is:

1. keep manual transcript and dry-run TTS as regression baselines
2. keep browser speech recognition as the no-key ASR prototype
3. test local Windows SAPI TTS as the next no-key audible-output checkpoint
4. treat cloud streaming ASR and cloud low-latency TTS as production follow-ups only after key/privacy/retention gates are documented

This supports the thesis methodology because it shows that real-time voice capability is being added through explicit safety and validation gates rather than through uncontrolled provider experimentation.
