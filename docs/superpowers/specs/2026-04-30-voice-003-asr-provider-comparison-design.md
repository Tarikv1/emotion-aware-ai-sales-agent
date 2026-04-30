# VOICE-003 ASR Provider Comparison Design

Date: 2026-04-30

## Purpose

VOICE-003 defines how the project should compare automatic speech recognition options before integrating a real provider.

The milestone is intentionally provider-safe. It compares provider families and adapter readiness without calling external APIs, storing secrets, or changing the reusable sales-agent core.

## Scope

VOICE-003 covers:

- an ASR provider-family candidate file
- a deterministic scoring script
- generated JSON and Markdown comparison artifacts
- a recommendation for the next prototype path

VOICE-003 does not cover:

- calling a cloud transcription API
- installing ASR dependencies
- uploading audio
- live microphone capture
- production call-center integration

## Provider Boundary

Every future ASR adapter should produce the same output shape:

```text
audio input
-> transcript text
-> confidence or quality metadata
-> provider metadata
-> consent and privacy metadata
```

Downstream code should not care whether the transcript came from browser speech recognition, a local model, a cloud streaming API, a batch transcription API, or a human-approved transcript.

## Candidate Families

VOICE-003 should compare families rather than overfit to one vendor too early:

- manual transcript baseline
- browser speech recognition demo
- local/offline ASR
- cloud batch ASR
- cloud streaming ASR
- hybrid edge/cloud ASR

These families should be scored against product needs:

- latency fit
- privacy fit
- no-key prototype fit
- streaming readiness
- batch audio readiness
- German-language readiness
- integration simplicity
- cost-control readiness
- thesis evaluation usefulness

## Recommendation Logic

The next prototype should prefer a no-key, low-risk path unless the user explicitly chooses to connect a cloud provider.

The expected recommendation is:

- keep `manual-transcript` as the regression baseline
- use browser speech recognition or another no-key path for a local demo if available
- defer cloud streaming ASR until secrets, consent, data retention, and provider terms are intentionally handled

## Validation

The validator should run the comparison script and assert:

- at least five provider families are compared
- the manual transcript baseline is present
- a no-key demo path is recommended before cloud integration
- cloud providers are marked as requiring explicit key/privacy decisions
- the generated report states that no API calls were made
- no secret-like API key patterns are written

