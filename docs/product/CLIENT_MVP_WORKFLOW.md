# Client MVP Workflow

## Purpose

Define the first concrete product workflow requested by the client.

The first client need is not a full sales-closing agent.
It is an autonomous calling agent that qualifies interest and schedules a follow-up call with a human sales agent.

## Workflow Summary

```text
lead list
  -> AI places outbound call
  -> AI asks a small set of qualification questions
  -> AI detects interest level
  -> if interested, AI schedules a human follow-up call
  -> if not interested, AI records outcome and ends politely
  -> if uncertain or risky, AI escalates or marks for review
```

## Core Job

The agent's first job is:

- call potential customers
- ask a few predefined or semi-adaptive questions
- determine whether the person is interested
- schedule the next available appointment with a human sales agent

This is a lead-qualification and appointment-setting agent, not a full autonomous closer.

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

## Escalation Conditions

Escalate or mark for review when:

- the person asks for a human
- the person has a complex product question
- the person is angry or strongly negative
- the agent is unsure whether the lead is interested
- compliance-sensitive topics appear
- scheduling fails after reasonable attempts

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
