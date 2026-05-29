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

## Post-Checkpoint Evaluation Dimensions

As of the 2026-05-29 thesis update, "sales-ready" should be evaluated more strictly than "can answer questions":

- sales momentum: does the agent move the buyer toward a decision without pressure or fake urgency?
- semantic understanding: does it preserve buyer meaning across paraphrases, ASR aliases, corrections, AND/OR relations, negation, and repeated questions?
- recommendation quality: does it recommend, compare, start lower, or disqualify based on known buyer context instead of pushing the highest tier?
- objection handling: does it acknowledge price, competitor/current-tool, privacy, source, timing, distrust, and no-interest objections without arguing?
- memory and loop resistance: does it avoid asking for information already provided and stop after terminal acceptance?
- source-grounded product claims: are product, price, privacy, API, Enterprise, and plan claims backed by the campaign source bundle or clearly caveated?
- side-effect safety: does it avoid claiming email, calendar, CRM, payment, official affiliation, hidden tracking, or unsupported follow-up actions?
- tool-boundary enforcement: if a hosted speech interface or tool layer is used, does product truth, canonical memory, verifier logic, and side-effect authority remain inside the project runtime?
- latency budget: any model or hosted speech interface in the live turn must still fit the perceived live voice target; 2-3 seconds is the working target and higher latency is problematic.
- warm-turn latency: are p50 and p90 first-agent-audio latencies measured separately from setup/session creation and interpreted as live-demo, thesis-demo, or product-readiness evidence only when gates pass?
- voice/TTS intelligibility: can a listener understand the spoken words without relying on transcript text?
- TTS/voice naturalness: does the selected voice sound natural enough for the intended demo or fallback use, and is voice-ID mismatch separated from provider quality?
- prosody and emotional delivery: does delivery match buyer emotion and sales move while avoiding hype, manipulation, fake laughter, flirting, shouting, guilt, or fear pressure?
- manual listening review: are intelligibility, naturalness, voice quality, sales tone, pacing, artifact severity, thesis-demo suitability, and product-fallback suitability recorded separately from automated checks?

Evidence interpretation:

- evidence-integrity validators check artifact structure, side-effect flags, leakage boundaries, and regression coverage
- quality gates judge whether behavior is good enough for the next use
- a quality gate can fail and still produce useful thesis evidence
- manual live tests and listening reviews remain required for sales naturalness, voice intelligibility, latency perception, and buyer trust
- live-demo readiness, thesis-demo readiness, and product readiness are separate claims
