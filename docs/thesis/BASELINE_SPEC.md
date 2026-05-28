# Baseline Specification

## Purpose

Define the first comparison that the thesis project will implement and evaluate.

The goal is not to prove the full final agent yet.
The goal is to test whether a simple emotion-aware adaptation layer produces more appropriate persuasive behavior than a non-adaptive alternative.

## Comparison Setup

Compare two systems:

### 1. Non-adaptive baseline

This version does not use emotion state as an input to strategy selection.

Behavior:

- receives dialogue context
- uses a fixed persuasion strategy or a generic strategy-selection rule
- generates a response without adapting strategy to the detected emotional state

Phase-1 simplification:

- start with a fixed default strategy profile centered on `evidence-or-benefit` plus light `rapport`
- do not vary strategy based on positive, neutral, or skeptical-negative emotional state

### 2. Adaptive baseline

This version uses the compact emotion signal to select a persuasion strategy before response generation.

Behavior:

- receives dialogue context
- receives a compact emotion state
- maps emotion state to one of the phase-1 strategy groups
- generates a response conditioned on both context and chosen strategy

## Inputs

For phase 1, define the input state as:

- current user utterance
- recent dialogue context
- compact emotion label

The compact emotion label comes from the phase-1 `MELD` mapping:

- `positive`
- `neutral`
- `skeptical-or-negative`

## Strategy Space

Use the phase-1 persuasion taxonomy:

- `rapport`
- `inquiry`
- `evidence-or-benefit`
- `emotional-appeal`
- `direct-ask-or-commitment`

## Initial Adaptive Policy

Use a transparent rule-based policy first.

Suggested mapping:

- `positive` -> `direct-ask-or-commitment`
- `neutral` -> `evidence-or-benefit`
- `skeptical-or-negative` -> `rapport` or `inquiry`

Working note:

For the first implementation, prefer:

- `skeptical-or-negative` -> `inquiry`

This is more defensible than jumping straight to reassurance language that is not well grounded in the selected dataset taxonomy.

## Output

The output of each system is:

- selected strategy
- generated response text

In later phases, this may extend to spoken output and latency measurements, but phase 1 should stop at strategy-aware response generation.

## Evaluation Intent

The first comparison should answer:

1. Does the adaptive system choose different strategies in a coherent way?
2. Do the generated responses better match the emotional state and dialogue context?
3. Does the adaptive policy appear more persuasive or appropriate than the non-adaptive baseline?

## Phase-1 Evaluation Style

Use lightweight evaluation first.

Candidate evaluation modes:

- manual qualitative review
- rubric-based response comparison
- limited human judgment study
- strategy distribution sanity checks

Do not lock in final quantitative metrics here yet.

## Example Comparison Shape

### Example A

- User state: `skeptical-or-negative`
- Non-adaptive strategy: `evidence-or-benefit`
- Adaptive strategy: `inquiry`

Expected adaptive behavior:

- acknowledge hesitation indirectly
- ask a clarifying or objection-oriented question
- avoid immediate strong ask pressure

### Example B

- User state: `positive`
- Non-adaptive strategy: `evidence-or-benefit`
- Adaptive strategy: `direct-ask-or-commitment`

Expected adaptive behavior:

- move toward commitment
- make the next step explicit
- keep momentum instead of over-explaining

## Why This Baseline Matters

This comparison is simple enough to implement quickly and strong enough to support an early thesis claim:

that emotionally conditioned strategy selection can change persuasive response behavior in an interpretable way.

## What This Does Not Claim Yet

This baseline does not yet claim:

- real-time speech competence
- end-to-end call success optimization
- final production behavior
- validated superiority on real call-center data

It is the first controlled adaptive comparison, not the finished thesis system.

## Current Runtime Baseline Addendum

The historical phase-1 baseline remains useful as the first controlled adaptive comparison, but it is no longer the current system baseline.

Current baseline as of 2026-05-29:

- deterministic/campaign-owned dialogue remains the active live-response authority
- source-grounded campaign configs own product truth, plan names, price/source claims, privacy boundaries, close routes, and no-fit language
- ElevenLabs remains the current live TTS path
- local LLMs are research-only and are not live-wired
- Liquid, Fish, and Kokoro are not live-wired
- Liquid is architecture inspiration only after failed manual listening review
- Fish-inspired prosody labels are internal planning controls only and must not be injected into spoken text
- Kokoro is only an optional future local TTS benchmark candidate

Future architecture target:

- LLM as conversation move planner, not fact owner or side-effect owner
- deterministic memory ledger, verifier, source/fact boundary, safety guardrail, and anti-loop detector
- one LLM replan allowed for non-critical verifier issues
- hard deterministic fallback only for safety-critical or repeated verifier failure
- possible action-id-only selector with deterministic response renderer and separate prosody planner

Current local LLM conclusion:

- Qwen2.5-7B and tested Ollama variants are not live-ready for per-turn voice use
- full local LLM response generation is not live-ready
- action-id-only selection, distilled small selectors, and non-LLM classifier/action selectors are future research paths
- no local LLM live wiring is allowed until quality and roughly 2-3 second live-turn latency gates pass
