# Qualification Question Flow

## Purpose

Define the first qualification-question workflow for the autonomous client MVP.

This flow is designed for:

- outbound lead qualification
- early interest detection
- scheduling a human follow-up call when the lead is ready

It is not designed for full autonomous sales closing.

## Core Design Principles

- keep the call short
- qualify interest before going deep into product detail
- do not interrogate the lead
- move to scheduling when the lead is clearly interested
- back off early when the lead is clearly uninterested
- escalate when the situation is uncertain, risky, or out of scope

## Target Outcome States

The qualification flow should end in one of these states:

- `interested`
- `maybe-interested`
- `not-interested`
- `needs-human`
- `do-not-call`

## Call Stages

```text
opening
  -> permission to continue
  -> relevance / problem check
  -> current process / pain-point check
  -> timing / openness check
  -> interest decision
  -> schedule / close / escalate
```

## Stage 1: Opening And Permission

### Goal

Confirm the person is reachable and willing to continue briefly.

### Example question

`Hi, this is [Agent Name] calling from [Company]. Is now a bad time, or do you have one minute for a quick question about how you currently handle [problem area]?`

### Outcome guidance

- If the lead gives brief permission: continue
- If the lead says they are busy but open later: `maybe-interested`
- If the lead refuses immediately: `not-interested`
- If the lead says do not call again: `do-not-call`

## Stage 2: Relevance / Problem Check

### Goal

Detect whether the lead even has the kind of problem the product is meant to help with.

### Example question

`Are you currently responsible for following up with inbound leads or customer inquiries, or is that handled another way in your team?`

### What counts as a positive signal

- they personally handle it
- their team handles it
- they recognize the workflow as relevant

### What counts as a weak or negative signal

- totally irrelevant role
- no such process exists
- they are clearly the wrong contact

### Outcome guidance

- Relevant workflow present: continue
- Wrong person but knows the right owner: `needs-human` or referral path
- Not relevant at all: `not-interested`

## Stage 3: Current Process / Pain-Point Check

### Goal

Find out whether there is friction worth solving.

### Example questions

- `How are you currently managing follow-up after a lead comes in?`
- `What tends to be the most frustrating part of that process today?`

### Positive signals

- manual work
- delayed responses
- lost leads
- inconsistent follow-up
- too many tools
- unclear ownership

### Neutral signals

- process exists and works somewhat
- no strong pain point stated yet

### Negative signals

- no problem at all
- strong dismissal of the category
- obvious hostility to further discussion

## Stage 4: Timing / Openness Check

### Goal

Determine whether the lead is open to change now or later.

### Example questions

- `Is improving that process something your team is actively looking at right now, or is it more of a future consideration?`
- `Would it be useful to have a short follow-up conversation with a sales specialist if there is a fit?`

### Strong interest signals

- actively evaluating options
- open to a follow-up call
- asks practical next-step questions
- asks about demo, setup, timeline, or pricing at a high level

### Maybe-interest signals

- not ready now but open later
- interested but needs internal alignment
- wants more information first

### Not-interest signals

- no need
- no budget and no urgency
- no openness to follow-up
- repeated dismissal

## Compact Decision Rules

### `interested`

Mark as `interested` when most of the following are true:

- the workflow is relevant
- a real pain point exists
- the lead expresses openness to change or learn more
- the lead accepts a follow-up conversation with a human sales agent

Typical examples:

- `Yes, this is something we are trying to improve.`
- `That sounds relevant, I would be open to a quick follow-up call.`
- `A demo or short call would be useful.`

### `maybe-interested`

Mark as `maybe-interested` when:

- relevance exists
- interest is tentative, delayed, or unclear
- the lead is not ready to schedule yet

Typical examples:

- `Maybe, but not right now.`
- `Send me something first.`
- `We are busy at the moment, but this could be relevant later.`

### `not-interested`

Mark as `not-interested` when:

- the workflow is not relevant
- the lead sees no useful problem to solve
- the lead declines further discussion without ambiguity

Typical examples:

- `We do not need that.`
- `We already have this covered and we are not changing anything.`
- `No thanks, not interested.`

### `needs-human`

Mark as `needs-human` when:

- the lead asks a complex product, pricing, legal, or integration question
- the lead may be interested but wants a specialist immediately
- the lead is the wrong person but offers a better contact path
- the AI cannot confidently classify the situation

### `do-not-call`

Mark as `do-not-call` when:

- the lead explicitly asks not to be called again
- the lead states the contact is inappropriate or unwanted in a way that should block future outreach

## Scheduling Trigger

Schedule a human follow-up call only when all of the following are true:

- state is `interested`
- the lead gives explicit agreement to a follow-up call
- a valid time window is captured
- the agent can confirm the appointment clearly

### Example transition

`It sounds like this may be worth a closer look. Would you like me to schedule a short follow-up call with one of our sales specialists?`

If yes:

- offer time options
- confirm the selected time
- restate the appointment clearly

## Escalation Trigger

Escalate or mark for review when:

- state is between `maybe-interested` and `not-interested` with low confidence
- the lead becomes angry or highly suspicious
- the lead asks a question outside the approved response scope
- the lead requests a human directly
- the agent fails to complete scheduling reliably

## Minimal First Question Set

For the MVP, start with three core questions after the opener:

1. `Are you currently involved in handling follow-up for incoming leads or customer inquiries?`
2. `What is the hardest part of that process for your team right now?`
3. `If there is a fit, would a short follow-up call with a human specialist be useful?`

Use follow-up wording adaptively, but keep this small skeleton stable for the first version.

## Strategy Hints By State

- If the lead sounds `positive`: move efficiently toward follow-up commitment
- If the lead sounds `neutral`: explain practical value and ask one more qualifying question
- If the lead sounds `skeptical-or-negative`: use inquiry first, not pressure

## Product Note

This flow should be implemented first in a turn-based simulation before real outbound telephony is added.
