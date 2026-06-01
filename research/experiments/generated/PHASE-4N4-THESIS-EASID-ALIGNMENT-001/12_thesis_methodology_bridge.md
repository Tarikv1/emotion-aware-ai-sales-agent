# Thesis Methodology Bridge

## Difference From The Original Proposal

The original proposal describes a human-like AI sales agent using emotion-aware speech and persuasion strategies. The current implementation is narrower and more controlled:

- ElevenLabs currently provides hosted voice-agent shell
- the repo owns campaign package, EASID schema, eval protocol, safety boundaries
- emotion detection may initially be manual/annotation-supported unless automatic model is implemented
- real outbound calls are not enabled
- website-sales campaign replaces public OpenAI campaign as the main sales-quality benchmark
- OpenAI campaign remains source-boundary benchmark

## Why This Is Better Than Treating The Upload Package As The Thesis

The upload package alone is weak thesis evidence because it shows configuration, not measurement. The stronger thesis path is the controlled system around it: campaign knowledge, buyer-state and emotion labels, ethical persuasion strategies, fixed evaluation cases, reproducible scoring, and explicit limits.

## Method Sequence

1. Freeze campaign package and evaluation case matrix.
2. Collect or simulate controlled conversations without real outbound calling.
3. Store synthetic/sanitized EASID rows.
4. Manually score buyer state, emotion label, persuasion strategy, safety, and outcome.
5. Compare generic baseline, Atlas structured agent, and future emotion-aware variant.
6. Fill result templates only after evidence exists.

## Claim Boundary

The current phase can claim thesis alignment and operational definitions. It cannot claim measured emotion detection, persuasion improvement, latency performance, human-likeness, or live readiness.
