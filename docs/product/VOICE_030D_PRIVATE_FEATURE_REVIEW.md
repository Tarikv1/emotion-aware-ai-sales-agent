# VOICE-030D Private Feature Review

VOICE-030D summarizes private VOICE-030C acoustic feature files before any runtime voice-setting work.

## Purpose

- Read private derived feature files under `data/private`.
- Create a human-reviewable private summary.
- Keep pause ratio and pause-duration metrics diagnostic-only.
- Summarize safer runtime candidates without changing runtime behavior.

## Inputs

```text
data/private/tarik-speech-samples/derived/audio-features/*.json
```

## Outputs

```text
data/private/tarik-speech-samples/derived/review/voice-030d-feature-review-summary.json
data/private/tarik-speech-samples/derived/review/voice-030d-feature-review-summary.md
```

## Runtime Candidate Summary

VOICE-030D summarizes only:

- `speech_burst_count`
- `energy_variation`
- `mean_speech_rms`

These are still only review candidates. They do not change runtime voice settings.

## Diagnostic-Only Summary

VOICE-030D keeps these excluded from runtime learning:

- `pause_ratio`
- `average_pause_ms`
- `longest_pause_ms`
- `silence_seconds`

Reason: owner samples can include long formulation pauses while Tarik thinks through complex product and engineering instructions. Those pauses are human and valid, but they should not slow down the sales agent.

## Commands

Run on the real private Tarik speech-sample features:

```powershell
python scripts\run_voice_030d_private_feature_review.py --allow-private-read
```

Validate with private fixtures:

```powershell
python scripts\validate_voice_030d_private_feature_review.py
```

## Boundary

- No provider calls.
- No transcription.
- No voice cloning.
- No runtime profile application.
- No public generated artifact.
- No raw audio paths in the review summary.
- Human review is required before any candidate can influence runtime voice behavior.
