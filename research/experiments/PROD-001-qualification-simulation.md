# PROD-001: Product MVP Qualification Simulation

## Status

Ready for simulation

## Source Label

`product-synthetic`

## Date

2026-04-28

## Question

Can the first product MVP workflow be represented as a repeatable turn-based simulation before real outbound calling or calendar integration exists?

## Hypothesis

A small structured case set can cover the main lead-qualification outcomes and make the product logic testable:

- `interested`
- `maybe-interested`
- `not-interested`
- `needs-human`
- `do-not-call`

## Dataset

- Name: PROD-001 qualification simulation cases
- Source: project-authored synthetic product scenarios
- License/usage notes: internal research/product planning artifact
- Size: 8 cases
- Language: English
- Labels: compact emotion label, expected interest state, compact strategy label, expected `CallOutcome`
- Notes: this is not thesis evidence from public or private customer data; it is a controlled product-workflow test set.

## Scope

Editable files or modules:

- `research/experiments/cases/prod-001-qualification-simulation.json`
- `scripts/render_product_simulation.py`
- `research/experiments/generated/PROD-001-simulation-packet.md`

Fixed constraints:

- use the qualification flow from `docs/product/QUALIFICATION_QUESTION_FLOW.md`
- keep scheduling constrained to explicit confirmation
- use existing compact emotion and strategy labels where possible
- preserve fallback and escalation guardrails

Out of scope:

- real calling
- live calendar integration
- automated response generation
- automated scoring
- client-private data

## Metrics

Primary metric:

- correct final interest-state classification for each case

Secondary metrics:

- correct scheduling trigger behavior
- correct escalation trigger behavior
- strategy label matches the lead's state
- no guardrail violation in the expected next action

## Method

1. Load the structured case file.
2. Render a markdown simulation packet.
3. For each turn, ask the candidate agent to produce:
   - state estimate
   - selected strategy
   - next response or action
   - scheduling/escalation decision
4. Compare the agent output against the expected turn labels and final `CallOutcome`.
5. Record misses and revise either the prompt, rules, or case definitions.

## Results

Not run yet.

## Observations

The first case set intentionally includes normal success cases and boundary cases:

- clear interested lead with confirmed scheduling
- tentative lead asking for information first
- irrelevant workflow
- explicit do-not-call
- complex integration question
- skeptical lead that becomes open through inquiry
- wrong contact with referral path
- interested lead with unconfirmed scheduling window

## Decision

Keep.

Reason:

This creates the first runnable product-track artifact and gives the client MVP a concrete simulation target before implementation moves into telephony or UI work.

## Next Step

Use the generated packet to test a product-specific agent prompt or rule engine that emits structured `CallOutcome` records.
