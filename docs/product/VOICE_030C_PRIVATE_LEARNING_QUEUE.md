# VOICE-030C Private Learning Queue

VOICE-030C is the local-only hook that runs after `VOICE-030B` captures or imports a speech sample.

## Purpose

- Queue every saved sample for local private learning.
- Analyze WAV files immediately with the VOICE-030A acoustic feature extractor.
- Mark non-WAV files as `needs_local_conversion`.
- Keep derived outputs under `data/private/tarik-speech-samples/derived`.
- Keep runtime voice settings unchanged until human review.

## Automatic Hook

`scripts/run_voice_030b_local_speech_capture.py` now calls `scripts/private_speech_learning_queue.py` after each saved recording/import.

For WAV files, the hook writes:

```text
data/private/tarik-speech-samples/derived/audio-features/<sample-id>.json
```

For all samples, the hook appends a private queue record to:

```text
data/private/tarik-speech-samples/derived/local-speech-learning-queue.jsonl
```

## Processing Statuses

- `analyzed_needs_review`: WAV acoustic features were extracted locally.
- `needs_local_conversion`: file is not WAV and needs a local conversion path before VOICE-030A analysis.
- `analysis_failed_needs_review`: WAV analysis failed and should be inspected locally.

## Learning Signal Policy

Tarik's owner samples may contain long formulation pauses because he is thinking through complex product and engineering instructions while speaking. Those pauses are valid human behavior, but they should not become the sales agent's target speaking pace.

Diagnostic-only features:

- `pause_ratio`
- `average_pause_ms`
- `longest_pause_ms`
- `silence_seconds`

Reviewable runtime candidates:

- `speech_burst_count`
- `energy_variation`
- `mean_speech_rms`

This means VOICE-030C can keep pause metrics as private evidence while preventing average pause ratio or pause duration from affecting runtime voice behavior.

## Speaker Context

Tarik is a native Turkish speaker with high English proficiency. VOICE-030C records this context so the system can learn useful delivery patterns from his speech without cloning or overfitting the product voice to one speaker identity.

Learn from:

- timing
- filler placement
- repair style
- thinking pauses
- sentence rhythm
- clear English delivery patterns

Guardrails:

- do not clone or overfit to one speaker identity
- do not force every campaign to match Tarik exactly

## Privacy Boundary

- No provider calls.
- No transcription.
- No voice cloning.
- No runtime profile application.
- No public generated artifact.
- No raw audio path is written into the VOICE-030C queue manifest.
- Pause ratio and pause-duration metrics are diagnostic-only, not runtime-learning targets.
- Human review is required before any derived pattern can affect runtime voice settings.

## Validation

```powershell
python scripts\validate_voice_030c_private_learning_queue.py
```
