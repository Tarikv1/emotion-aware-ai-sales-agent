# PREMORTEM-001 Project Risk Review

Date: 2026-05-08

Status: read-only product/thesis risk review. No runtime behavior, retrieval behavior, provider behavior, customer-data flow, or voice setting is changed by this document.

## Failure Scenario

Assume the project fails to become a client-usable and thesis-defensible emotion-aware sales agent.

The most likely failure mode is not that the voice or RAG work is weak. It is that the project becomes a strong research harness with many good isolated checkpoints, but does not converge into a small, auditable live-call product path. The project could also fail by promoting advisory RAG, voice personality, private speech patterns, or emotion inference into runtime before the evidence and gates are strong enough.

## Current Evidence Base

- `docs/thesis/ROADMAP.md` sets the current checkpoint as `RESP-007` human listening review before unblocking the voice-personality selector.
- `docs/brain/BRAIN_001_PROJECT_BRAIN_ARCHITECTURE.md` keeps the brain small: reusable sales-agent core, configurable `SalesCampaign`, short-term call state, conservative buyer-state/emotion estimates, strategy selector, optional guarded retrieval, voice delivery, and post-call learning outside the live path.
- `docs/product/RAG_018_GUARDED_RUNTIME_RETRIEVAL.md` shows opt-in retrieval improves selected fixed synthetic turns, but retrieval remains off by default.
- `docs/product/RESP_007_GERMAN_PACING_STABILITY_FOLLOW_UP.md` blocks German pacing-quality claims and voice-personality promotion until human listening review.
- `docs/product/PRODUCT_BRIEF.md` already names core product risks: autonomy overclaiming, weak edge-case handling, privacy/compliance issues, hallucinated sales claims, poor client workflow fit, and unclear responsibility for bad AI suggestions.

## Top Failure Modes

| Severity | Failure mode | Why it could happen | Early warning | Prevention |
| --- | --- | --- | --- | --- |
| P0 | Premature client or live-call deployment | The product goal points toward autonomous lead qualification and appointment setting, including a German insurance example, while legal, claims, scheduling, and data boundaries are still open. | Real customer audio, real leads, or insurance claims are introduced before the campaign claim matrix and handoff policy are locked. | Keep real deployment blocked until a first `SalesCampaign` has allowed claims, forbidden claims, disclosures, handoff rules, call-control states, data retention rules, and legal review notes. |
| P0 | Advisory knowledge becomes runtime behavior accidentally | RAG-020/RAG-021 are valuable, and RAG-018 showed retrieval benefits, so it is tempting to make retrieval broadly default. | New rules appear in runtime output without a RAG-017 rebuild and RAG-018 evaluation. | Keep retrieval disabled by default; promote only narrow validated influence paths through RAG-017/RAG-018. |
| P0 | Voice/personality evidence is over-promoted | English personalities are promising, but German pacing still has an open listening gate. | A universal voice/personality default is selected before RESP-007 is heard and accepted. | Keep the voice-personality selector blocked until RESP-007 review is recorded, then build a bounded selector rather than one global default. |
| P1 | The project optimizes voice indefinitely and misses end-to-end product behavior | Voice quality has produced many useful checkpoints, but the MVP also needs call control, scheduling, logging, escalation, and latency handling. | The next several checkpoints all adjust provider-facing delivery without adding product call-flow evidence. | After RESP-007, limit voice work to selector gating and move to BRAIN-002 state schema plus fixed scripted full-call simulations. |
| P1 | Emotion-awareness becomes overclaiming | The product name invites hidden-emotion or classifier assumptions, but current evidence supports conservative buyer-state estimates from observable behavior. | Runtime labels customer emotion as certain, sensitive, or diagnostic. | Keep buyer state probabilistic and observable; log uncertainty; use emotion cues only to choose low-pressure strategy, repair, handoff, or pacing. |
| P1 | Safety/compliance gets buried under sales strategy | Persuasion research can improve outcomes, but insurance and serious-illness contexts are high-risk for pressure, fear, and unsupported benefit claims. | Responses mention coverage, payout, medical benefit, savings, urgency, or fear without explicit campaign approval. | Use campaign-level allowed/forbidden claim lists, protected text, handoff triggers, and fixed negative tests for fear-based or medical/coverage pressure. |
| P1 | Evidence sprawl makes results hard to trust | The repo has many generated artifacts, validators, thesis logs, and currently many dirty/untracked files from recent work. | A later checkpoint cannot say which script, case file, generated output, and decision log produced a claim. | Keep each checkpoint as a synchronized bundle: runner, validator, case file, generated result/report, product doc, and thesis decision/methodology note. |
| P1 | Client workflow mismatch | The MVP still has open questions around interface, client data, scheduling, CRM, feedback labels, and B2B versus B2C differences. | The agent sounds good but cannot fit a real caller workflow or appointment process. | Define the first client workflow before more breadth: input data, call goal, qualification fields, transfer/schedule/end decisions, and human review loop. |
| P2 | Context and memory bloat slow development | Local audit found only P2 issues, but always-on memory and project instructions are already long. | New sessions spend more time re-orienting than implementing narrow checkpoints. | Keep roadmap checkpoints narrow, use `scripts/read_relevant.py`, and move long reasoning into project docs rather than always-on instructions. |

## What Is Already Strong

- Default commands and validators are mostly no-provider, no-key-safe, and synthetic by default.
- The project has explicit provider gates for TTS/live audio.
- RAG evidence is kept opt-in and measured against fixed synthetic cases.
- Private audio and private transcripts are repeatedly blocked from runtime/public artifacts.
- The thesis trail is unusually strong: methodology logs, decision logs, reference registry, generated evidence, and drift checks.
- The BRAIN-001 architecture correctly avoids a giant prompt, broad default retrieval, unvalidated emotion classifiers, private raw memory, and multi-agent chains in the customer-facing path.

## Immediate Risk-Reducing Move

The safest next move is not more broad research.

1. Finish `RESP-007` only through explicit live-provider opt-in and human listening review.
2. If accepted, create a bounded voice-personality selector that chooses between already accepted styles without making either a universal production default.
3. Build `BRAIN-002` as a narrow runtime state schema: buyer state, strategy, safety, response, retrieval status, voice profile, call-control decision, and evidence log fields.
4. Run fixed full-call simulations before any first-client claim.

## Approval Gates Before Risk Increases

- Live provider audio: explicit provider opt-in, key in environment only, bounded timeout, no customer audio upload.
- Retrieval promotion: RAG-017 rebuild plus RAG-018 evaluation; default retrieval stays off until separately justified.
- Private learning: local-only `data/private/` boundary, aggregate reviewed notes only, no raw audio/transcripts in runtime memory.
- Client pilot: legal/compliance review for outbound calling and campaign claims, especially German insurance contexts.
- Product claim: fixed simulation evidence plus logged failures, not just good isolated voice or RAG examples.

## Decision

Keep moving, but narrow the project around product convergence:

- close the RESP-007 listening gate,
- then build the smallest auditable runtime brain schema,
- then prove full-call behavior with fixed simulations,
- then discuss client-facing pilot shape.
