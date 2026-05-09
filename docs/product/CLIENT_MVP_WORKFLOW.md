# Client MVP Workflow

## Purpose

Define the first concrete product workflow requested by the client.

This document now represents the safer appointment-setting subset of the product. The broader current direction is defined in `docs/product/FULL_SALE_MVP_STRATEGY.md`: a constrained full-sale agent that can close campaign-approved next steps while still recognizing non-sale, support, escalation, and do-not-call outcomes.

The first client workflow may still use appointment-setting as the approved close. In that mode, the agent qualifies interest and schedules a follow-up call with a human sales agent instead of completing the sale itself.

This workflow can apply to B2B or B2C sales. The current first case set is B2B-leaning, but the product should also support direct-to-consumer qualification.

The first concrete client example is a German call center selling consumer insurance products, including dental insurance and cancer-related or serious-illness insurance. This should be treated as a sensitive B2C insurance context.

## Workflow Summary

```text
lead list
  -> AI places outbound call
  -> AI asks a small set of qualification questions
  -> AI detects interest level
  -> if interested, AI schedules an appropriate human follow-up
  -> if not interested, AI records outcome and ends politely
  -> if uncertain or risky, AI escalates or marks for review
```

## Core Job

In appointment-setting mode, the agent's job is:

- call potential customers
- ask a few predefined or semi-adaptive questions
- determine whether the person is interested
- schedule the next available appointment with a human sales agent, specialist, consultant, or service representative

This is a lead-qualification and appointment-setting mode inside the larger full-sale product strategy, not the only product endpoint.

## Minimum Capabilities

### 1. Outbound calling

- receive lead/contact details
- initiate the call
- introduce itself appropriately
- confirm basic willingness to continue

### 2. Qualification dialogue

- ask a short sequence of client-approved questions
- adapt follow-up wording based on responses
- detect disinterest, uncertainty, interest, or request for more information

### 3. Interest classification

Use a compact state model:

- `interested`
- `maybe-interested`
- `not-interested`
- `needs-human`
- `do-not-call`

### 4. Scheduling

If the lead is interested:

- offer available follow-up windows
- schedule the call with a human sales agent
- confirm date and time
- record appointment details

### 5. Outcome logging

Every call should produce a structured outcome:

```text
CallOutcome
  call_id
  lead_id
  call_status
  interest_state
  qualification_answers
  selected_strategy
  appointment_scheduled
  appointment_time
  escalation_reason
  call_summary
  next_action
```

## Guardrails

The agent should not:

- make unsupported product claims
- pressure uninterested leads
- continue after a clear do-not-call request
- pretend to be a human
- schedule without clear confirmation
- handle complex objections beyond the approved scope
- make unapproved insurance coverage, health, payout, savings, or legal claims
- use fear-based pressure around illness or medical costs

## Escalation Conditions

Escalate or mark for review when:

- the person asks for a human
- the person has a complex product question
- the person is angry or strongly negative
- the agent is unsure whether the lead is interested
- compliance-sensitive topics appear
- scheduling fails after reasonable attempts
- detailed insurance policy, coverage, health, or legal questions appear

## Relation To Thesis

This workflow aligns well with the thesis because emotion-aware adaptation can help decide:

- whether to ask a clarifying question
- whether to provide a short benefit explanation
- whether to move toward scheduling
- whether to back off or escalate

The thesis can evaluate the adaptation logic before the full outbound-calling system is production-ready.

## Near-Term Build Target

Before integrating real telephony, build a turn-based simulation:

```text
lead scenario
  -> qualification question
  -> lead response
  -> interest/state estimate
  -> strategy selection
  -> next agent response
  -> scheduling or outcome
```

This gives the product a concrete path while keeping implementation manageable.

## Next Product Artifact

Use `QUALIFICATION_QUESTION_FLOW.md` as the first concrete question-and-decision layer for this workflow.

The simulation contract is defined in `SIMULATION_CONTRACT.md`.

The first lead and outcome persistence design is defined in `LEAD_DATABASE_DESIGN.md`.
