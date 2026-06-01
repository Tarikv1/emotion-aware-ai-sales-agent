# Emotion Signal Plan

## Collected Signals

The first valid evidence layer should be annotation-supported, not invented model output:

- text cues
- manual emotion labels
- optional acoustic features
- optional ASR confidence
- optional speech rate / pauses
- optional interruption markers

Optional audio-derived features should be recorded only when transcript/audio is available under the project privacy rules.

## Emotion Labels

- curious
- confused
- skeptical
- price_sensitive
- frustrated
- busy
- high_intent
- low_intent
- trust_concerned
- neutral

## Annotation Rule

Each buyer turn receives one primary emotion_label and supporting text_emotion_cues. Emotion confidence stays null unless it comes from a documented annotation process or implemented model.

## Accuracy Boundary

Do not claim accuracy until evaluated.

Accuracy, F1, or calibration can be reported only after labeled data exists, the evaluation split is defined, and the metric calculation is reproducible.
