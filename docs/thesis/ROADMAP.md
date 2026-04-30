# Roadmap

This roadmap is the working steering document for the thesis and product project.
It should be updated whenever the project direction changes, a phase completes, or a meaningful new constraint appears.

## Current Direction

Build and evaluate an emotion-aware AI sales agent that adapts persuasion strategy based on customer state.

The project starts with a public-data-first text baseline, then moves toward multimodal speech and voice-feature adaptation.

This is also a real product effort with a potential paying client. The first product track should turn thesis evidence into an autonomous lead-qualification and appointment-setting agent with fallback and escalation guardrails.

The product track should support both B2B and B2C sales contexts. The first product simulation is B2B-leaning, but later case sets should include direct-to-consumer customer conversations.

The first concrete B2C client example is a German call center selling consumer insurance products, including dental insurance and cancer-related or serious-illness insurance. This should inform the next product simulation expansion, but it is only one example of the broader campaign-driven product model.

The product simulation runner now supports campaign wrappers, so one reusable core can be exercised across multiple client/product profiles while preserving per-campaign guardrails. The mixed case sets are examples of that breadth, not the boundary of the product.

The next product-learning priority is difficulty-first: strengthen the reusable core against universal sales objections and edge cases before expanding aggressively into more industries.

The product runtime priority is low latency. The live call path should be a fast real-time sales-agent core with deterministic guardrails and short bridge responses when slower lookup is needed. Specialist modules or sub-agents should support background compliance, product lookup, CRM work, handoff preparation, and post-call learning rather than blocking every customer-facing reply.

## Dual Track Principle

The thesis track and product track should reinforce each other without being confused.

Thesis track:

- prove and evaluate the core adaptation idea
- keep experiments reproducible and honest
- document methods, limitations, and evidence

Product track:

- define a usable client workflow
- build toward reliability, reviewability, and trust
- target autonomous launch behavior while validating it through supervised testing and sales-expert feedback

## Phase 1: Text And Strategy Baseline

Status: in progress

Goal:

- test whether emotion-conditioned strategy selection improves persuasive response behavior compared with a non-adaptive baseline

Completed:

- public-data-first scope selected
- `MELD` selected for compact emotion/sentiment grounding
- `Persuasion for Good` selected for persuasion strategy grounding
- compact emotion taxonomy defined
- compact persuasion taxonomy defined
- non-adaptive vs adaptive baseline specified
- prompt templates created
- evaluation rubric created
- `EXP-001` synthetic seed comparison completed
- `EXP-002` dataset-derived comparison completed
- repeatable prompt-packet runner created
- structured JSON case files created for phase-1 case sets

Current result:

- adaptive baseline was preferred in both early comparison passes
- strongest gains appeared in emotional appropriateness and strategy coherence
- skeptical or resistant cases showed the clearest benefit from adaptation

Next:

- expand from six-case experiments to a larger mixed case set
- reduce manual adaptation where possible
- decide how much of rubric scoring should remain manual versus semi-structured
- document limitations clearly before treating results as thesis evidence

## Phase 2: Dataset-Grounded Expansion

Status: planned

Goal:

- create a larger, more defensible case set grounded in public datasets

Likely work:

- extract more candidate emotional dialogue snippets from `MELD`
- extract more persuasion strategy examples from `Persuasion for Good`
- create a larger mixed case set
- compare adaptive and non-adaptive behavior across more examples
- decide whether rubric scoring remains sufficient or needs additional evaluator support

Open questions:

- how much manual domain adaptation is acceptable
- whether to include human evaluator judgments
- whether to add automated consistency checks

## Phase 3: Voice Feature Module

Status: planned

Goal:

- add interpretable voice features as a later multimodal customer-state signal

Planned module:

- pitch features
- energy features
- speech rate
- pause ratio
- silence ratio
- hesitation markers

Evaluation direction:

- compare text-only adaptation against text-plus-voice adaptation

Important boundary:

- this module adapts the concept of modular voice analytics from collaborative thesis work with Shehzeb Iftakhar
- it remains focused on sales-dialogue customer-state estimation, not music or creative-expression analysis

## Phase 4: Integrated Thesis Prototype

Status: planned

Goal:

- connect the thesis components into a small turn-based prototype that can also inform a product MVP

Likely components:

- input text or transcript
- compact emotion/state estimation
- strategy selection
- LLM response generation
- visible rationale for selected strategy
- logging and confidence checks
- fallback or escalation rule
- optional audio/TTS layer if time permits

Out of scope:

- production call-center deployment
- large-scale live customer testing
- full-duplex real-time interruption handling
- broad autonomous sales behavior outside the constrained target workflow

## Product MVP Track

Status: planned

Goal:

- define and build the smallest autonomous client-usable lead-qualification and appointment-setting workflow that comes out of the thesis work

Likely MVP:

- import lead/contact details
- place or simulate an outbound call
- start the first agent response within a 1-2 second target after the customer finishes speaking
- ask a small set of qualification questions
- estimate customer state
- select a strategy
- generate and execute the next response autonomously
- schedule a human follow-up call if the lead is interested
- log the strategy choice and rationale
- escalate or pause when confidence or safety boundaries require it
- collect sales-expert feedback during development and testing
- use bridge responses when approved lookup, scheduling, or human handoff preparation takes longer than the live turn budget

Scope note:

- B2B workflows may qualify business contacts, teams, decision-makers, and company needs
- B2C workflows may qualify individual consumers, personal needs, callback interest, and service appointment readiness

Open questions:

- whether the first product interface should be a CLI, dashboard, or lightweight web app
- what workflow the ready client actually needs first
- what data the client can legally and practically provide
- what claims can be made safely at launch
- how sales experts should label, correct, and rate agent behavior during development
- how calendar/availability integration should work for human sales-agent scheduling
- how much the first B2C flow should differ from the first B2B lead-qualification flow
- what German insurance-sales and outbound-calling constraints must be reviewed before any live deployment
- how to measure live-turn latency in the prototype without confusing model quality with voice-platform delay

## Phase 5: Thesis Write-Up Support

Status: ongoing

Goal:

- keep the written thesis easy to produce from project evidence

Ongoing actions:

- update `METHODOLOGY_LOG.md` after meaningful work
- update `DECISION_LOG.md` after important decisions
- keep experiment notes complete
- record limitations as they appear
- preserve collaboration, attribution, and AI-usage notes

Key writing sources:

- `PROJECT_BRIEF.md`
- `DATASETS.md`
- `DATA_READINESS.md`
- `BASELINE_SPEC.md`
- `EVALUATION_RUBRIC.md`
- `METHODOLOGY_LOG.md`
- `DECISION_LOG.md`
- experiment files under `research/experiments/`
- `docs/product/PRODUCT_BRIEF.md`

## Near-Term Next Step

Expand the case inventory beyond the first six-case sets and move toward a larger mixed evaluation pool with stronger dataset grounding.

Parallel product step:

Define the first autonomous lead-qualification and appointment-setting workflow before building a UI, so product decisions are grounded in the real client use case rather than a generic demo.

Immediate product artifact:

- qualification-question flow
- interest-state decision rules
- scheduling trigger
- escalation trigger
- turn-based product simulation case set
- mixed B2B/B2C simulation expansion
- B2C insurance-specific simulation cases
- mixed campaign wrappers that combine consumer and B2B product profiles
- sales difficulty gauntlet before broad industry-library expansion
- real-time agent architecture and latency budget
