# Evaluation Rubric

## Purpose

Provide a lightweight, repeatable rubric for comparing the non-adaptive and adaptive baseline responses in phase 1.

## Unit of evaluation

For each test case, compare:

- the non-adaptive response
- the adaptive response

Both responses should be evaluated against the same dialogue context and current user utterance.

## Scoring dimensions

Score each response on a 1 to 5 scale for each dimension.

### 1. Context fit

Does the response make sense given the recent dialogue and the current user utterance?

- 1: poorly matched or off-topic
- 3: generally relevant but somewhat generic
- 5: highly relevant and well grounded in the context

### 2. Strategy coherence

Does the response reflect the intended persuasive strategy in a clear and believable way?

- 1: strategy is unclear or contradicted
- 3: strategy is somewhat visible but weak
- 5: strategy is clear, appropriate, and well executed

### 3. Emotional appropriateness

Does the response feel appropriate for the user's inferred emotional state?

- 1: tone or tactic clashes with the state
- 3: acceptable but not especially adaptive
- 5: clearly well matched to the state

### 4. Persuasive quality

Does the response move the conversation forward in a credible persuasive direction?

- 1: ineffective or counterproductive
- 3: plausible but unremarkable
- 5: strong next-step persuasive behavior

### 5. Human-likeness

Does the response sound like something a competent human sales agent might say?

- 1: robotic, awkward, or unnatural
- 3: acceptable but somewhat generic
- 5: natural, smooth, and believable

## Comparison outcome

For each test case, record:

- total score for non-adaptive response
- total score for adaptive response
- preferred response
- short justification

## Suggested comparison note template

### Case ID

- Emotion label:
- Strategy label for adaptive response:
- Non-adaptive total:
- Adaptive total:
- Preferred:
- Why:

## Thesis note

This rubric is intended for the first baseline comparison and should be described as a lightweight qualitative evaluation tool.
It is useful for early validation before the project settles on a more formal final evaluation design.

## Current Runtime Evaluation Addendum

The original 1-to-5 rubric remains useful for early prompt comparison, but the current prototype needs additional checks.

Dialogue and sales dimensions:

- direct question answering: does the agent answer product, price, privacy, process, and next-step questions before asking another question?
- buyer-move satisfaction: does the response match the detected buyer move rather than falling back to a broad menu?
- response progression: does the conversation move forward after challenge, correction, objection, or repetition?
- no-loop/no-menu behavior: does the agent avoid repeating the same response or reopening a large menu after a specific buyer statement?
- close quality: does the close mode match the campaign, buyer fit, and source facts?
- no-fit quality: can the agent say a free/no-paid option may be enough without pressure?

Campaign and claim dimensions:

- product knowledge grounding: are product, pricing, plan, feature, privacy, and API claims source-backed or campaign-backed?
- campaign isolation: do facts from one campaign stay out of another campaign?
- claim safety: does the agent avoid unsupported discounts, guarantees, legal/security advice, ROI promises, payment collection, and fake side effects?
- affiliation safety: does a public-data simulation avoid claiming official vendor representation?

Live voice dimensions:

- ASR robustness for near-miss phrases
- TTS naturalness and pronunciation
- latency and turn-taking
- voice-ready close wording, including not reading raw URLs aloud
- listener trust, professionalism, and pressure perception

Method note:

Deterministic validators can score many content and safety dimensions, but human/live review is still required for voice realism, perceived sales quality, and production-readiness claims.
