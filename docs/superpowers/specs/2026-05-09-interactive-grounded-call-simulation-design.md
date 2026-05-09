# Interactive Grounded Call Simulation Design

Date: 2026-05-09

## Context

The current PROD-027 through PROD-030 path created useful static evidence:

- `PROD-027` created `20` scripted full scenarios with `120` fixed customer turns.
- `PROD-029` reran those turns with grounded RouteSignal CRM answers.
- `PROD-030` accepted `120/120` grounded answers, but found `10` route gaps and only `13/20` full scenarios demo-ready.

This is still too weak as sales-agent evidence because the customer does not react to the agent. The current shape is:

`fixed customer turn -> agent answer -> next fixed customer turn`

The next checkpoint should instead test:

`customer state -> customer turn -> agent answer -> customer state changes -> reactive customer turn`

## Decision

Replace the planned `PROD-031-grounded-route-gap-fix` with `PROD-031-interactive-grounded-call-simulation`.

The route-gap fix is deferred until the interactive simulator shows which route gaps matter in reactive conversations. Static route mismatches may still matter, but fixing them before interactive evaluation risks optimizing for a weak benchmark.

## Recommended Approach

Build a deterministic local customer simulator first.

Why:

- repeatable enough for regression tests
- no LLM/provider calls
- easy to inspect and debug
- safe for thesis evidence because every state transition is explicit
- strong enough to prove whether the agent changes customer interest, trust, clarity, and commitment over a conversation

LLM customer simulation can be added later as an optional comparison lane, not the first version.

## Alternatives Considered

### A. Keep Static Full Scenarios And Fix Route Gaps

This is easiest and keeps continuity with PROD-030, but it would optimize a non-reactive benchmark. The agent could pass while still feeling fake in real conversation.

### B. Deterministic Interactive Simulator

This is the selected path. It adds real turn-to-turn reactivity while staying local, repeatable, inspectable, and safe.

### C. LLM-Based Customer Simulator

This would be more natural, but it adds nondeterminism, provider boundaries, cost, prompt-injection risk, and harder thesis evidence. It should be optional after deterministic simulation exists.

## Scope

PROD-031 should create an offline simulator that runs multiple calls where customer replies are generated from state transitions, not prewritten follow-up turns.

Each simulated call should include:

- customer persona
- hidden buying intent
- emotional baseline
- trust score
- interest score
- clarity score
- friction score
- objection state
- product information need
- decision-maker status
- stage: opening, discovery, objection, product explanation, close attempt, callback, escalation, not interested, sale-ready

Each turn should record:

- customer message
- agent answer
- agent decision snapshot if available
- detected agent behavior
- state before
- state after
- customer reaction reason
- route/action label
- safety flags

## Simulator State

The first deterministic state model should use bounded integer or enum values:

- `interest`: `0` to `5`
- `trust`: `0` to `5`
- `clarity`: `0` to `5`
- `friction`: `0` to `5`
- `patience`: `0` to `5`
- `commitment`: `none`, `curious`, `considering`, `callback`, `verbal-interest`, `sale-ready`
- `emotion`: `neutral`, `curious`, `skeptical`, `confused`, `annoyed`, `calm`, `interested`
- `active_objection`: `none`, `price`, `trust`, `time`, `authority`, `provider`, `confusion`, `written-info`

State updates should be deterministic rules based on the agent answer.

Example:

- Directly answers a product question with approved facts: `clarity +1`, `trust +1`
- Asks more than one question before answering: `friction +1`, `patience -1`
- Handles price with a concrete plan and no payment collection: `clarity +1`, `friction -1`
- Makes unsupported claim or payment collection attempt: hard failure and terminate
- Pushes for close while `clarity < 3` or `trust < 3`: `friction +2`, possible rejection
- Respects delay/callback request: `trust +1`, possible callback outcome

## Customer Response Generation

Customer replies should be generated from templates plus state, not from copied transcript text.

The simulator should produce natural-ish customer messages such as:

- confused customer asks a follow-up product question
- skeptical customer asks for written information
- annoyed customer pushes back on pressure
- interested customer asks price/setup questions
- sale-ready customer gives verbal commitment or asks for next step
- non-sale customer requests callback, human, stop, or support handoff

The wording must remain project-owned and source-safe:

- no exact CallCenterEN transcript text
- no high-similarity paraphrase
- no real names or companies
- no transcript-derived prompt text entering runtime

## Agent Under Test

V1 should test the local guarded/grounded response path only.

It should use the RouteSignal CRM synthetic campaign facts from PROD-028/PROD-029, but should not promote those facts into default runtime behavior. The simulator may call existing local response builders with explicit test inputs.

Provider calls, LLM calls, private data reads, retrieval defaults, composer-hook defaults, customer data, server start, payment collection, and runtime promotion remain blocked.

## Scenario Seeds

The first seed set should be small but stronger than static traces:

- price-sensitive but interested buyer
- confused buyer who needs product explanation
- skeptical trust-gap buyer
- busy callback-request buyer
- existing-provider comparison buyer
- authority/stakeholder-review buyer
- support/handoff boundary buyer
- do-not-call protected boundary buyer

Each seed should run for up to `8` agent turns, stopping earlier when a terminal condition is reached.

## Terminal Conditions

Calls should stop when any of these happens:

- `sale-ready`
- callback agreed
- human handoff required
- do-not-call / stop request
- support-only boundary reached
- hostile rejection
- max turns reached
- hard failure

## Metrics

PROD-031 should report:

- call count
- total turn count
- safe close rate
- sale-ready outcome count
- callback outcome count
- non-sale correctness
- hard failure count
- payment collection count
- unsupported claim count
- average trust delta
- average interest delta
- average clarity delta
- average friction delta
- question overuse count
- premature close count
- route/action correctness where applicable
- interactive realism score
- reactive customer state trace visibility

## Outputs

PROD-031 should create:

- `research/experiments/generated/PROD-031-interactive-grounded-call-simulation/result.json`
- `research/experiments/generated/PROD-031-interactive-grounded-call-simulation/report.md`
- `research/experiments/generated/PROD-031-interactive-grounded-call-simulation/interactive_call_traces.json`
- `research/experiments/generated/PROD-031-interactive-grounded-call-simulation/interactive_call_trace.html`
- `docs/product/PROD_031_INTERACTIVE_GROUNDED_CALL_SIMULATION.md`
- runner and validator scripts

The HTML trace should show each call as a real conversation:

- customer turn
- agent answer
- state before
- state after
- why the customer reacted that way
- terminal outcome

## Validation Requirements

The PROD-031 validator should prove:

- simulator is deterministic
- at least `8` call seeds are run
- every call has reactive state transitions
- every customer message after turn one depends on the prior agent answer/state
- exact customer/agent/state trace is visible
- no provider calls
- no LLM use
- no private data reads
- no dataset download
- no copied transcript text
- no payment collection
- no runtime default changes
- no production promotion

## Non-Goals

PROD-031 should not:

- fix the static PROD-030 route gaps yet
- use an LLM customer simulator
- start a server
- create a polished UI
- call voice providers
- enable telephony
- collect payment
- use real customer data
- claim production readiness

## Next Work After PROD-031

If PROD-031 shows the grounded agent performs well interactively, the next step should be a post-simulation review packet that decides:

- which failures are simulator-design issues
- which failures are runtime policy issues
- whether route-gap fixes still matter
- whether a local demo should use interactive traces instead of static scenario tables

If PROD-031 exposes major interactive failures, fix those before any route-gap cleanup or demo polish.

## Self-Review

- Placeholder scan: no TBD/TODO placeholders remain.
- Consistency check: PROD-031 is defined as deterministic, local, and non-promotional throughout.
- Scope check: the first implementation is one checkpoint with a bounded seed set and explicit outputs.
- Ambiguity check: LLM simulation, route-gap fixes, provider calls, and runtime promotion are explicitly out of scope.
