# Sales Difficulty Taxonomy

## Purpose

Define the recurring sales difficulties that the reusable sales-agent core should handle across many campaigns.

The goal is not to teach the agent one industry first. The goal is to teach the agent universal sales behavior that transfers across industries, then combine that behavior with campaign-specific product facts and guardrails.

## Public Grounding

This taxonomy is informed by public sales-objection material and rewritten into project-specific categories.

Sources used for pattern grounding:

- Apollo: common objections around budget, timing, trust, internal alignment, and status quo
- Salesgenie: price, timing, authority, need/value, and risk/competition objections
- Proposify: price concerns, competitor comparisons, suitability doubts, bad timing, hard no, and do-not-contact situations
- B2B Vic: price, authority, urgency/status quo, trust, and solution-fit objection categories

These sources are used for category grounding only. The project cases are synthetic and should not be treated as copied real conversations.

## Core Difficulty Types

### `price-objection`

The customer believes the product or service is too expensive, not worth the effort, or difficult to justify.

Good behavior:

- acknowledge the cost concern
- clarify whether the concern is price, value, budget, or risk
- avoid discount or savings promises
- route price-specific questions to a human when needed

### `send-info-brushoff`

The customer asks for information as a way to end or delay the call.

Good behavior:

- treat this as tentative interest, not a confirmed buying signal
- offer approved information
- ask permission for later follow-up if appropriate
- do not force scheduling

### `status-quo`

The customer already has a process, provider, or workaround that feels good enough.

Good behavior:

- do not attack the current solution
- ask one careful question about friction or goals
- close politely if there is no problem to solve

### `timing-delay`

The customer may be interested but says the timing is wrong.

Good behavior:

- respect the timing boundary
- create a follow-up task if there is real interest
- do not mark an appointment unless the time is explicit

### `authority-gap`

The caller is not the final decision-maker or needs a partner, manager, committee, or owner to approve.

Good behavior:

- identify whether there is still useful interest
- avoid pressuring the wrong person
- create a human follow-up or owner path when appropriate

### `trust-credibility`

The customer does not trust the company, the call, or the claims yet.

Good behavior:

- acknowledge the concern
- use only approved proof or credibility material
- do not invent references, customer names, or credentials

### `competitor-comparison`

The customer asks why this product is better than a named or existing competitor.

Good behavior:

- avoid unsupported comparison claims
- ask what matters most in the comparison if safe
- escalate when the answer requires approved evidence

### `fit-risk`

The customer worries the product will not work in their situation.

Good behavior:

- clarify the fit concern
- avoid guarantees
- escalate technical, legal, contract, health, or coverage questions

### `vague-interest`

The customer sounds friendly or open but gives no specific need, urgency, or next step.

Good behavior:

- do not over-read politeness as buying intent
- ask a short clarifying question
- log maybe-interest when no commitment exists

### `angry-or-annoyed`

The customer is irritated or wants the call to stop.

Good behavior:

- stop quickly
- apologize briefly if appropriate
- do not ask more questions
- mark do-not-call only when explicitly requested

### `human-request`

The customer directly asks to speak to a person.

Good behavior:

- route to a human
- do not keep qualifying unless the request allows it
- log the request clearly

### `claim-boundary`

The customer asks for a guarantee, promise, legal/medical/financial answer, or unsupported product claim.

Good behavior:

- refuse to guess
- stay neutral
- route to the proper human specialist

## Design Implication

Campaigns define the product facts.

The reusable core should learn the difficulty pattern:

```text
customer response
  -> difficulty type
  -> interest state
  -> strategy
  -> next action
  -> guardrail check
```

This keeps sales behavior portable across products, clients, and buyer types.

## Strategy Taxonomy

The strategy label describes the safest next sales move, not the whole call outcome.

### `rapport`

Use when the agent should acknowledge, de-escalate, preserve trust, stop pressure, or route politely to a human.

Good fit:

- annoyed or skeptical lead
- trust concern
- wrong contact
- direct human request
- not-interested or do-not-call boundary

Avoid using it as a generic fallback when the better move is a clarifying question.

### `inquiry`

Use when the agent should ask one careful clarifying question before making a next-step decision.

Good fit:

- price concern where value is unclear
- status quo resistance
- competitor comparison criteria
- fit or risk uncertainty
- vague interest

Avoid using it after the lead has already asked to stop or asked for a human.

### `evidence-or-benefit`

Use when the lead asks for information or when an approved, non-guaranteed benefit explanation is the right response.

Good fit:

- send-information request
- safe explanation of an approved benefit
- credibility support that is already allowed in campaign config

Avoid unsupported claims, invented proof, or guaranteed outcomes.

### `emotional-appeal`

Use only for approved empathy or positive motivation.

Good fit:

- low-risk motivational framing
- empathetic acknowledgment that does not create pressure

Avoid fear, guilt, urgency manipulation, or sensitive-product pressure.

### `direct-ask-or-commitment`

Use when the lead is open to a concrete next step.

Good fit:

- explicit callback openness
- appointment scheduling
- non-binding specialist follow-up
- broad timing that needs a follow-up task rather than confirmed scheduling

Avoid using it when the lead asks for a human because of risk, guarantee, legal, coverage, or technical uncertainty. Those cases should escalate.

## Final Outcome Consistency Rules

- `interest_state = needs-human` should produce `call_status = escalated`.
- `interest_state = interested` without a confirmed appointment should usually produce `call_status = ready-for-scheduling`.
- `appointment_scheduled = true` requires a clear appointment time.
- broad callback timing should create a follow-up task, not a confirmed appointment.
- guarantee, competitor-proof, legal, medical, financial, coverage, or technical-certainty requests should escalate unless the campaign explicitly approves the answer.
