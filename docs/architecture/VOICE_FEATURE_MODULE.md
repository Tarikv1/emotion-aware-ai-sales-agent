# Voice Feature Module

## Purpose

Define how modular voice analysis can be incorporated into the emotion-aware AI sales agent.

This module adapts the idea of interpretable modular voice analytics from collaborative thesis work into the sales-dialogue domain.

## Role In The Sales Agent

The voice feature module should help the emotion engine move beyond text-only sentiment.

Conceptual flow:

```text
customer audio
  -> voice feature extraction
  -> compact voice feature record
  -> fusion with text and dialogue context
  -> customer state estimate
  -> persuasion strategy selection
```

## Initial Feature Set

Start with interpretable features that are feasible to compute and explain:

- `pitch_mean_hz`
- `pitch_range_hz`
- `pitch_variability`
- `energy_mean`
- `energy_variability`
- `speech_rate_wpm`
- `pause_ratio`
- `mean_pause_duration`
- `silence_ratio`
- `hesitation_marker_count`

## Why These Features Matter

- Pitch and pitch variability may help identify intensity, uncertainty, or emotional activation.
- Energy and loudness variation may help distinguish engaged, flat, or irritated delivery.
- Speech rate may help identify confidence, urgency, hesitation, or overload.
- Pauses and silence may help identify uncertainty, resistance, or cognitive load.
- Hesitation markers can strengthen the bridge between voice analysis and dialogue-state interpretation.

## Proposed Schema

Use a small structured record first:

```text
VoiceFeatureRecord
  audio_id
  segment_id
  start_time
  end_time
  pitch_mean_hz
  pitch_range_hz
  pitch_variability
  energy_mean
  energy_variability
  speech_rate_wpm
  pause_ratio
  mean_pause_duration
  silence_ratio
  hesitation_marker_count
  extraction_status
```

This is not final. It is a first working schema for thesis planning and later implementation.

## Integration With Current Phase Plan

Phase 1 remains text and strategy focused:

- `MELD` compact sentiment mapping
- `Persuasion for Good` strategy taxonomy
- non-adaptive vs adaptive prompt comparison

Phase 2 can add the voice feature module:

- extract audio features from suitable speech/audio data
- combine voice features with text-derived emotion signals
- compare text-only adaptation against text-plus-voice adaptation

## Boundary From Friend's Thesis

This module does not import the CLVAD creative-expression schema.

The shared concept is modular interpretable voice analysis.
The adaptation here is customer-state estimation for sales dialogue, not lyrical or vocal-performance analysis.

## Implementation Notes

Likely tools:

- `librosa` for pitch, energy, tempo-related and silence features
- ASR transcript timing when available for speech rate and hesitation markers
- simple schema validation later with `pydantic`

Keep the first implementation small and testable.
Do not build a full audio analytics platform before the text-based phase-1 baseline is runnable.
