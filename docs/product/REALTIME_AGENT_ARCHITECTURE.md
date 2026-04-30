# Real-Time Agent Architecture

## Purpose

Define how the sales agent should answer quickly in a live call while still using campaign guardrails, sales reasoning, compliance checks, and optional specialist modules.

The core requirement is conversational speed:

- the customer should normally hear the first agent response within 1-2 seconds after they finish speaking
- if deeper lookup or reasoning will take longer, the agent should immediately say a short bridge response
- background or specialist modules must not block the normal live response path unless the turn is explicitly escalated

## Architecture Principle

The product should behave like a fast real-time sales agent, not a committee of slow agents.

Use one reusable live sales-agent core for the customer-facing turn. Use specialist modules or sub-agents for background support, deeper review, and post-call learning.

```text
customer speech
  -> speech-to-text
  -> real-time sales-agent core
  -> text-to-speech response

background modules
  -> compliance check
  -> campaign knowledge lookup
  -> CRM update
  -> handoff preparation
  -> post-call evaluation
```

## Latency Budget

Target timing for a normal turn:

```text
customer stops speaking
  -> speech-to-text finalizes or stabilizes
  -> fast state/guardrail decision
  -> first spoken response begins within 1-2 seconds
```

Practical budget:

- speech endpointing and transcript stabilization: under 700 ms where possible
- fast state, difficulty, and guardrail classification: under 500 ms
- response generation or template selection: under 700 ms
- text-to-speech start: under 300-500 ms

These are product targets, not guaranteed early prototype numbers. They define what the production architecture should optimize for.

## Live Critical Path

The live path should do only the minimum needed to respond safely.

```text
latest customer answer
  -> campaign guardrail check
  -> emotion estimate
  -> sales difficulty estimate
  -> interest-state estimate
  -> strategy selection
  -> next-action selection
  -> call-control / termination decision
  -> output consistency check
  -> concise response
  -> state update
```

The live path should avoid:

- multiple sequential LLM calls
- waiting for CRM enrichment
- waiting for post-call scoring
- running several sub-agents one after another
- long retrieval pipelines before every ordinary reply

## Bridge Response Behavior

If the agent cannot safely answer within roughly one second, it should immediately use a short bridge response.

Examples:

- "Okay, let me check that carefully."
- "I want to make sure I answer that correctly."
- "One moment, I do not want to guess on that."
- "That is a good question. Let me check the approved information."

For sensitive or regulated topics:

- "I do not want to give you an inaccurate answer on that. I can have a specialist check it with you."
- "That depends on details I should not guess about. I can route this to a human specialist."

Bridge responses should be short. They are not sales pitches. Their purpose is to preserve conversational flow while slower work happens.

## Fast Path

Most turns should use the fast path.

Good fit:

- permission to continue
- simple relevance check
- simple price objection
- timing delay
- vague interest
- not-interested boundary
- do-not-call request
- human request
- obvious claim-boundary escalation

Fast path behavior:

```text
classify state
  -> choose safe strategy
  -> answer or escalate
```

For many risky cases, the safest response is also fast. A guarantee request does not require slow reasoning; it requires the agent to avoid promising and route correctly.

## Slow Path

The slow path is for turns that require deeper lookup or confirmation.

Good fit:

- product details that must be checked against approved campaign facts
- availability lookup for scheduling
- CRM record lookup
- campaign-specific disclosure retrieval
- human handoff preparation
- compliance review after a risky statement

Slow path behavior:

```text
say bridge response
  -> run lookup/check in background
  -> answer if approved
  -> otherwise escalate or create follow-up
```

## Sub-Agent Policy

Sub-agents or specialist modules are useful, but they should not be chained in the live customer-facing path.

Good uses:

- background compliance monitor
- campaign knowledge lookup
- CRM enrichment
- calendar availability helper
- handoff package builder
- post-call transcript evaluator
- sales-expert feedback analyzer
- benchmark and regression evaluator

Bad live-call pattern:

```text
customer answer
  -> emotion sub-agent
  -> compliance sub-agent
  -> product sub-agent
  -> response sub-agent
  -> reviewer sub-agent
  -> customer waits
```

Preferred pattern:

```text
customer answer
  -> real-time core gives safe first response
  -> background modules enrich, verify, or prepare next step
```

## Output Contract In The Live Path

The live core should always enforce consistency before speaking or writing state.

Examples:

- `interest_state = needs-human` should produce escalation behavior
- do-not-call requests should suppress contact
- no appointment should be confirmed without a clear time
- broad timing should create a follow-up task, not a confirmed appointment
- unsupported claims should escalate rather than be answered creatively
- explicit stop, do-not-call, or uninterested boundaries should end the call politely

This is why the product needs a deterministic output-contract layer even when the main language behavior uses an LLM.

See `docs/product/CALL_TERMINATION_POLICY.md` for the dedicated hang-up, transfer, bridge, and schedule-and-end rules.

## Runtime Layers

### Layer 1: Real-Time Conversation Core

Responsible for:

- immediate turn handling
- short safe responses
- state classification
- strategy selection
- next-action decision
- call-control decision
- output consistency

This layer is latency-critical.

### Layer 2: Background Specialist Modules

Responsible for:

- compliance review
- campaign knowledge checks
- CRM and database updates
- calendar checks
- human handoff preparation

This layer can run in parallel and may finish after the first spoken response.

### Layer 3: Post-Call Learning Layer

Responsible for:

- transcript review
- rule-baseline comparison
- LLM evaluation
- sales-expert feedback processing
- taxonomy improvement
- regression tests

This layer is not in the live call path.

## Product Implication

The agent should be sold and built as:

`a low-latency, campaign-configurable AI sales agent with deterministic guardrails and background specialist support`

not:

`a chain of multiple agents that debate every reply while the customer waits`

The architecture preserves the broad product goal:

- one reusable sales-agent core
- configurable campaign profiles
- fast live responses
- background specialist support
- human handoff when risk or complexity requires it
