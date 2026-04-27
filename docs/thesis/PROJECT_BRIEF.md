# Project Brief

## Thesis goal

Create and evaluate an AI agent that detects customer emotion from speech and tone, selects a persuasion strategy, and generates human-like call responses. The core research question is whether emotion-aware adaptation improves conversion-related outcomes compared with a non-adaptive baseline.

## Product goal

Develop the thesis work toward a real client-usable product: an autonomous emotion-aware AI calling agent that qualifies leads, handles basic objections, detects interest, and schedules follow-up calls with human sales agents.

The launch target is autonomous behavior inside a constrained sales workflow, with fallback and escalation guardrails rather than human approval for every normal response.

## Smallest believable system

A turn-based pipeline:

1. Accept recorded or live call audio
2. Run speech-to-text
3. Classify a small set of emotions
4. Select a persuasion strategy with rules or a lightweight model
5. Generate response text with an LLM
6. Produce spoken output through TTS

Constraints for the first version:

- no full-duplex interruption handling
- 3 to 5 emotion classes
- fixed domain or narrow scenario

## In scope

- emotion detection from speech as a core ML component
- strategy selection logic
- LLM-based response generation
- basic latency-aware pipeline
- quantitative and qualitative evaluation
- interpretable voice-feature analysis as a later module supporting customer-state estimation
- product MVP planning for a client-usable assistant workflow
- lead qualification and appointment-setting workflow design

## Out of scope

- production-grade call-center deployment
- perfect human indistinguishability
- large-scale live A/B testing
- advanced low-level prosody control
- full legal-compliance implementation
- broad autonomous sales behavior outside the constrained target workflow

## Current risks

- noisy real-call audio
- mismatch between public and private data sources
- missing persuasion labels
- latency pressure
- LLM unpredictability
- evaluation design complexity
- product overclaiming before the system is reliable
- privacy and workflow-integration risk for client deployment
- insufficient expert feedback before autonomous launch

## Research posture

Treat the thesis proposal as directional, not binding.
Do not lock in exact architecture, datasets, metrics, or tools too early.
Use iterative discovery and keep the system design narrow until the data reality is clear.

## Product posture

Treat client usefulness as a real constraint from the beginning.
Prefer MVP slices that could later become a usable workflow:

- conversation context input
- lead/contact input
- qualification question flow
- customer-state estimate
- strategy selection
- autonomous response generation
- human follow-up scheduling for interested leads
- strategy and confidence logging
- fallback or escalation when needed
- sales-expert feedback during development and testing

## Collaboration posture

This thesis may adapt the concept of modular interpretable voice analysis from collaborative thesis work with Shehzeb Iftakhar.
The adapted module supports emotion-aware sales dialogue and remains distinct from lyrical/vocal creative-expression analysis.
