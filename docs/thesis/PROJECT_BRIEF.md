# Project Brief

## Thesis goal

Create and evaluate an AI agent that detects customer emotion from speech and tone, selects a persuasion strategy, and generates human-like call responses. The core research question is whether emotion-aware adaptation improves conversion-related outcomes compared with a non-adaptive baseline.

## Product goal

Develop the thesis work toward a real client-usable product: an autonomous emotion-aware AI calling agent that qualifies leads, handles basic objections, detects interest, and schedules follow-up calls with human sales agents.

The launch target is autonomous behavior inside a constrained sales workflow, with fallback and escalation guardrails rather than human approval for every normal response.

Current status as of 2026-07-14: the project is still a research/prototype system. It is not production-deployed or generally production-validated. The Atlas 036/039/040 evidence supports the targeted hosted text/simulation behaviors: paid pricing is buyer-triggered and constrained to one applicable lane, unresolved capability/scope/pricing turns suppress mockup or send CTAs, and terminal control uses one built-in `end_call` path for hard stops, delivery-timing deduplication, and atomic gatekeeper outcomes. The final guarded hosted configuration preserved `17` ordered KB attachments, `30` Analysis criteria, one built-in `end_call`, zero custom/server duplicates, inactive Procedures, exact unrelated tool/configuration preservation, and no outbound calls. However, the last CRM repetition patch was structurally read back without a fresh post-write simulation, so the final live fingerprint is not transcript-verified and a broad live-readiness claim is not supported. The evidence also does not establish PSTN audio quality, ASR, latency, interruption handling, buyer perception, conversion impact, compliance clearance, or real-customer performance.

Sales-ready now means more than explaining the product. The agent must actively move the buyer toward a decision, handle objections, recommend or disqualify based on fit, avoid loops and passive information dumping, and preserve buyer meaning across paraphrases and spoken variations.

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
- universal sales dialogue behavior with campaign-owned product facts
- source-grounded campaign fixtures and claim governance
- deterministic replay and adversarial validation for live-shaped dialogue failures
- semantic frame mapping, buyer-state tracking, and loop resistance for sales dialogue
- local LLM/action-selector research as an isolated future-planning track
- internal backend-neutral prosody planning as a future delivery-control layer
- hosted speech-native interface evaluation as an isolated architecture research track

## Out of scope

- production-grade call-center deployment
- perfect human indistinguishability
- large-scale live A/B testing
- advanced low-level prosody control
- full legal-compliance implementation
- broad autonomous sales behavior outside the constrained target workflow
- official representation of third-party vendors in public-data simulations
- fake email, calendar, CRM, or payment side effects
- production deployment or real customer use without compliance, consent, retention, and handoff review
- live local LLM response generation
- Liquid, Fish, Kokoro, or Ultravox live voice/runtime wiring
- raw Fish-style tags in buyer-facing speech

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
- deterministic validator pass being mistaken for real sales quality
- source-grounded public product facts becoming stale
- universal dialogue being contaminated by campaign-specific product claims
- local LLM latency or output quality being overestimated from small smokes
- successful model setup being mistaken for acceptable speech quality
- prosody labels becoming too redundant or vague to improve real sales calls

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

Current architecture posture:

- universal dialogue owns buyer-move recognition, response shape, repair, call control, and side-effect safety
- campaign configs and adapters own product claims, customer-facing wording, close modes, source policies, and handoff targets
- a future LLM may act as conversation move planner, but it must not own campaign facts, source truth, side effects, or final safety boundaries
- deterministic memory/verifier layers should store what happened, detect loops, enforce source/safety boundaries, and request at most one replan before hard fallback
- the current live voice path remains ElevenLabs
- Ultravox is a promising hosted speech-interface candidate with a working sandbox tool boundary, but current latency is not live-ready and it is not a final ElevenLabs replacement
- Liquid is architecture inspiration only after failed manual listening review
- Fish Audio S2 is inspiration for internal prosody labels only; Fish tags must not leak into ElevenLabs speech
- Kokoro remains optional/future local TTS benchmark candidate, not an immediate replacement
- deterministic dry-run evidence is required before live rehearsal
- live rehearsal is still required before stronger claims about ASR, TTS, latency, voice naturalness, or commercial readiness

## Collaboration posture

This thesis may adapt the concept of modular interpretable voice analysis from collaborative thesis work with Shehzeb Iftakhar.
The adapted module supports emotion-aware sales dialogue and remains distinct from lyrical/vocal creative-expression analysis.
