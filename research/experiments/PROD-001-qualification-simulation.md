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
- Size: 12 cases
- Language: English
- Labels: compact emotion label, expected interest state, compact strategy label, expected `CallOutcome`
- Notes: this is not thesis evidence from public or private customer data; it is a controlled product-workflow test set.

## Scope

Editable files or modules:

- `research/experiments/cases/prod-001-qualification-simulation.json`
- `scripts/render_product_simulation.py`
- `scripts/run_product_simulation.py`
- `packages/prompts/product-qualification-agent.txt`
- `docs/product/SIMULATION_CONTRACT.md`
- `research/experiments/generated/PROD-001/PROD-001-simulation-packet.md`
- `research/experiments/generated/PROD-001/PROD-001-evaluation-packet.md`

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
3. Render an evaluation packet using the product qualification prompt and simulation contract.
4. For each turn, ask the candidate agent to produce:
   - state estimate
   - selected strategy
   - next response or action
   - scheduling/escalation decision
5. Compare the agent output against the expected turn labels and final `CallOutcome`.
6. Record misses and revise either the prompt, rules, or case definitions.

## Results

Runnable packet generation completed.

- `research/experiments/generated/PROD-001/PROD-001-simulation-packet.md` renders the scenario scripts.
- `research/experiments/generated/PROD-001/PROD-001-evaluation-packet.md` renders prompts, reference structured outputs, candidate-output slots, and manual checks.
- `research/experiments/generated/PROD-001/PROD-001-db-records.json` exports database-shaped synthetic reference records.
- `research/experiments/PROD-001-first-simulation-pass.md` records the first three-case dry run.

Live model execution has not been run yet.

Database-shaped export counts:

- Leads: 12
- Call sessions: 12
- Qualification answers: 32
- Turn decisions: 32
- Call outcomes: 12
- Appointments: 1
- Escalations: 5

SQLite import completed:

- `research/experiments/generated/PROD-001/PROD-001.sqlite`
- `research/experiments/generated/PROD-001/PROD-001-sqlite-report.md`

The report verifies retrieval of interested leads, do-not-call leads, appointments, escalations, and turn-level decisions.

Rule baseline completed:

- `research/experiments/PROD-001-rule-baseline.md`
- `research/experiments/generated/PROD-001/PROD-001-rule-baseline-results.json`
- `research/experiments/generated/PROD-001/PROD-001-rule-baseline-report.md`

The rule baseline matched all final outcome checks but only matched 18 / 32 turn-level emotion labels.

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
- busy lead asking for later contact
- relevant workflow with no budget or urgency
- direct request for a human
- privacy/compliance concern

## Decision

Keep.

Reason:

This creates the first runnable product-track artifact and gives the client MVP a concrete simulation target before implementation moves into telephony or UI work.

## Next Step

Use the generated evaluation packet to test a product-specific agent prompt or rule engine that emits structured turn outputs and final `CallOutcome` records.
