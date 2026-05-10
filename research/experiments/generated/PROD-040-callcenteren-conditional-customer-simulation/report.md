# PROD-040 CallCenterEN Conditional Customer Simulation

PROD-040 creates a local deterministic simulation where every customer reply is conditioned on the immediately preceding agent answer and grounded by abstract CallCenterEN pattern IDs.

It does not copy transcript text. It uses the leakage-checked PROD-014 scenario bank and PROD-013 pattern bank as abstract pattern sources only.

## Result

- Checkpoint id: `PROD-040-callcenteren-conditional-customer-simulation`
- Source checkpoint: `PROD-039-customer-realism-simulator-hardening`
- Scenario source checkpoint: `PROD-014-callcenteren-scenario-bank`
- Pattern source checkpoint: `PROD-013-callcenteren-pattern-extraction`
- Conditional customer turn count: `19`
- Agent-conditioned customer reply count: `19`
- Unique customer response count: `19`
- Repeated customer response count: `0`
- CallCenterEN pattern source count: `59`
- Scenario bank source count: `8`
- Abstract pattern only: `true`
- Exact transcript text used: `false`
- All calls start with cold opening: `true`
- All calls end by customer decision: `true`
- Fixed turn limit used: `false`
- Loop guard triggered: `false`
- Accepted deals: `4`
- Rejected deals: `4`
- Hard failures: `0`
- Payment collection count: `0`
- Leakage findings: `0`
- Provider calls made: `false`
- Runtime behavior changed: `false`
- Next checkpoint: `PROD-041-conditional-simulation-review`

## Call Outcomes

| Seed | Persona | Turns | Terminal outcome | First scenario pattern |
| --- | --- | ---: | --- | --- |
| conditional-price-sensitive | price-sensitive operations manager | 3 | accepted-deal | scenario-appointment_request-003 |
| conditional-confused-fit | confused owner trying to understand product fit | 4 | accepted-deal | scenario-buying_interest-002 |
| conditional-skeptical-proof | skeptical founder who wants proof before engaging | 2 | rejected-deal | scenario-billing_issue-008 |
| conditional-busy-now | busy sales lead with low patience | 1 | rejected-deal | scenario-callback_request-005 |
| conditional-existing-provider | team lead already using a CRM | 5 | accepted-deal | scenario-technical_problem-007 |
| conditional-manager-review | manager who needs a concise internal case | 2 | accepted-deal | scenario-cancellation-006 |
| conditional-support-boundary | support-seeking user who should not be sold | 1 | rejected-deal | scenario-price_request-004 |
| conditional-do-not-call | protected stop-request customer | 1 | rejected-deal | scenario-buying_interest-002 |

## Conditional Trace Notes

### conditional-price-sensitive

- Terminal outcome: `accepted-deal`

#### Turn 1

- Customer response condition: `agent answered price and kept billing outside call`
- Reaction reason: `customer moves from price concern to internal justification`
- Pattern basis: `prod-014-price_objection-001` / `price_discussion`

Customer context:

```text
I have a few minutes, but if this is another paid tool I need the real cost first.
```

Agent answer:

```text
The synthetic pricing is Starter at $29 per user per month annually and Growth at $59. Billing stays outside this call, so the only question here is whether the workflow is worth reviewing.
```

Customer response:

```text
Okay, now I know the range. If I mention this internally, what problem am I saying it solves?
```

#### Turn 2

- Customer response condition: `agent gave manager-ready summary`
- Reaction reason: `customer understands the internal case but checks the commitment boundary`
- Pattern basis: `prod-014-price_objection-001` / `commitment_confirmation`

Customer context:

```text
Okay, now I know the range. If I mention this internally, what problem am I saying it solves?
```

Agent answer:

```text
For the manager version: Growth is $59 per user per month annually, annual billing reduces subscription price by 15%, setup is typically two to four weeks, and a specialist can confirm security details in writing.
```

Customer response:

```text
That is enough to keep talking. Just be clear: is the review non-binding, or am I agreeing to something commercial?
```

#### Turn 3

- Customer response condition: `agent confirmed non-binding no-payment next step`
- Reaction reason: `customer accepts only after commitment boundary is clear`
- Pattern basis: `prod-014-price_objection-001` / `sale_ready_close`

Customer context:

```text
That is enough to keep talking. Just be clear: is the review non-binding, or am I agreeing to something commercial?
```

Agent answer:

```text
This would only be a non-binding workflow review with a specialist. No payment, contract, or purchase decision should happen on this call.
```

Customer response:

```text
That works. Send a short workflow review slot, and keep billing out of it.
```

### conditional-confused-fit

- Terminal outcome: `accepted-deal`

#### Turn 1

- Customer response condition: `agent clarified product fit without replacing CRM`
- Reaction reason: `customer understands enough to ask about cost`
- Pattern basis: `prod-014-sale_eligible-001` / `clarification`

Customer context:

```text
RouteSignal does not ring a bell. Is this a CRM thing or something else?
```

Agent answer:

```text
RouteSignal CRM is not a full CRM replacement. It sits around lead intake, routing, callback ownership, Gmail and Outlook sync, Slack and Zapier handoffs, and CSV import.
```

Customer response:

```text
That helps. If it is mainly routing and callback ownership, what would a small team pay?
```

#### Turn 2

- Customer response condition: `agent answered price and kept billing outside call`
- Reaction reason: `customer moves from price concern to internal justification`
- Pattern basis: `prod-014-sale_eligible-001` / `price_discussion`

Customer context:

```text
That helps. If it is mainly routing and callback ownership, what would a small team pay?
```

Agent answer:

```text
The synthetic pricing is Starter at $29 per user per month annually and Growth at $59. Billing stays outside this call, so the only question here is whether the workflow is worth reviewing.
```

Customer response:

```text
Okay, that is more concrete. Before I take it anywhere, what is the simple internal reason for looking at it?
```

#### Turn 3

- Customer response condition: `agent gave manager-ready summary`
- Reaction reason: `customer understands the internal case but checks the commitment boundary`
- Pattern basis: `prod-014-sale_eligible-001` / `commitment_confirmation`

Customer context:

```text
Okay, that is more concrete. Before I take it anywhere, what is the simple internal reason for looking at it?
```

Agent answer:

```text
For the manager version: Growth is $59 per user per month annually, annual billing reduces subscription price by 15%, setup is typically two to four weeks, and a specialist can confirm security details in writing.
```

Customer response:

```text
I can explain that now. Before I say yes to a review, tell me whether this creates any payment commitment.
```

#### Turn 4

- Customer response condition: `agent confirmed non-binding no-payment next step`
- Reaction reason: `customer accepts only after commitment boundary is clear`
- Pattern basis: `prod-014-sale_eligible-001` / `sale_ready_close`

Customer context:

```text
I can explain that now. Before I say yes to a review, tell me whether this creates any payment commitment.
```

Agent answer:

```text
This would only be a non-binding workflow review with a specialist. No payment, contract, or purchase decision should happen on this call.
```

Customer response:

```text
Okay, I can do a short review if it stays educational and nobody asks for payment.
```

### conditional-skeptical-proof

- Terminal outcome: `rejected-deal`

#### Turn 1

- Customer response condition: `agent avoided unsupported claims`
- Reaction reason: `customer asks for proof in writing instead of accepting`
- Pattern basis: `prod-014-trust_repair-001` / `trust_repair`

Customer context:

```text
I get these calls all the time. If this is vague software talk, I am out.
```

Agent answer:

```text
Fair concern. I cannot promise revenue lift. The verifiable claim is narrower: RouteSignal CRM centralizes lead intake and routes leads by region, source, priority, or owner.
```

Customer response:

```text
That is more believable than a big promise. Send the exact proof points first; I am not agreeing on a call.
```

#### Turn 2

- Customer response condition: `agent offered written confirmation`
- Reaction reason: `customer accepts written follow-up but not a sale`
- Pattern basis: `prod-014-trust_repair-001` / `written_info`

Customer context:

```text
That is more believable than a big promise. Send the exact proof points first; I am not agreeing on a call.
```

Agent answer:

```text
That is reasonable. A specialist can send the written details and separate what is confirmed from what still needs a fit review.
```

Customer response:

```text
Fine, send that over. I will read it, but do not mark me as a buyer from this call.
```

### conditional-busy-now

- Terminal outcome: `rejected-deal`

#### Turn 1

- Customer response condition: `agent gave one concise relevance reason`
- Reaction reason: `customer stays time-bound and rejects for now`
- Pattern basis: `prod-014-callback_request-001` / `callback_boundary`

Customer context:

```text
Not a good time. You have one sentence before I jump back into work.
```

Agent answer:

```text
Then I will keep it to the point: RouteSignal CRM helps teams stop losing inbound leads between routing and callback ownership. If that problem is not active, we can stop here.
```

Customer response:

```text
That is at least clear, but I still cannot do this now. Leave it there for today.
```

### conditional-existing-provider

- Terminal outcome: `accepted-deal`

#### Turn 1

- Customer response condition: `agent positioned product around existing CRM`
- Reaction reason: `customer shifts from replacement concern to fit check`
- Pattern basis: `prod-014-support_handoff-001` / `provider_objection`

Customer context:

```text
We already have a CRM, so I am not looking to rip anything out.
```

Agent answer:

```text
I would not ask you to replace a CRM that works. RouteSignal CRM is only worth a look if routing, callback ownership, or reporting are still messy around the CRM.
```

Customer response:

```text
Okay, not replacing the CRM matters. The real question is whether our routing is messy enough to justify another layer.
```

#### Turn 2

- Customer response condition: `agent named concrete fit criteria`
- Reaction reason: `customer asks price only after fit became plausible`
- Pattern basis: `prod-014-support_handoff-001` / `eligibility_check`

Customer context:

```text
Okay, not replacing the CRM matters. The real question is whether our routing is messy enough to justify another layer.
```

Agent answer:

```text
A useful fit check would be whether inbound leads are delayed, assigned twice, or missing callback owners. If none of those happen, this is probably not urgent.
```

Customer response:

```text
Those are real issues for us sometimes. If we looked at it, what would the Growth plan cost?
```

#### Turn 3

- Customer response condition: `agent answered price and kept billing outside call`
- Reaction reason: `customer moves from price concern to internal justification`
- Pattern basis: `prod-014-support_handoff-001` / `price_discussion`

Customer context:

```text
Those are real issues for us sometimes. If we looked at it, what would the Growth plan cost?
```

Agent answer:

```text
The synthetic pricing is Starter at $29 per user per month annually and Growth at $59. Billing stays outside this call, so the only question here is whether the workflow is worth reviewing.
```

Customer response:

```text
That price is not tiny, so I would need a clean reason this helps alongside our CRM. What would I tell the team?
```

#### Turn 4

- Customer response condition: `agent gave manager-ready summary`
- Reaction reason: `customer understands the internal case but checks the commitment boundary`
- Pattern basis: `prod-014-support_handoff-001` / `commitment_confirmation`

Customer context:

```text
That price is not tiny, so I would need a clean reason this helps alongside our CRM. What would I tell the team?
```

Agent answer:

```text
For the manager version: Growth is $59 per user per month annually, annual billing reduces subscription price by 15%, setup is typically two to four weeks, and a specialist can confirm security details in writing.
```

Customer response:

```text
That gives me enough to explain it. I still need to know whether the next step creates any contract or payment obligation.
```

#### Turn 5

- Customer response condition: `agent confirmed non-binding no-payment next step`
- Reaction reason: `customer accepts only after commitment boundary is clear`
- Pattern basis: `prod-014-support_handoff-001` / `sale_ready_close`

Customer context:

```text
That gives me enough to explain it. I still need to know whether the next step creates any contract or payment obligation.
```

Agent answer:

```text
This would only be a non-binding workflow review with a specialist. No payment, contract, or purchase decision should happen on this call.
```

Customer response:

```text
Alright, book the review. I want it framed around routing gaps, not replacing the CRM.
```

### conditional-manager-review

- Terminal outcome: `accepted-deal`

#### Turn 1

- Customer response condition: `agent gave manager-ready summary`
- Reaction reason: `customer understands the internal case but checks the commitment boundary`
- Pattern basis: `prod-014-cancellation_boundary-001` / `commitment_confirmation`

Customer context:

```text
If this is useful, I need the version I can repeat to my manager.
```

Agent answer:

```text
For the manager version: Growth is $59 per user per month annually, annual billing reduces subscription price by 15%, setup is typically two to four weeks, and a specialist can confirm security details in writing.
```

Customer response:

```text
That is concise enough. Before I agree to a slot, confirm this is only a fit review and not a purchase step.
```

#### Turn 2

- Customer response condition: `agent confirmed non-binding no-payment next step`
- Reaction reason: `customer accepts only after commitment boundary is clear`
- Pattern basis: `prod-014-cancellation_boundary-001` / `sale_ready_close`

Customer context:

```text
That is concise enough. Before I agree to a slot, confirm this is only a fit review and not a purchase step.
```

Agent answer:

```text
This would only be a non-binding workflow review with a specialist. No payment, contract, or purchase decision should happen on this call.
```

Customer response:

```text
Good. Then schedule a focused specialist review and include the security notes for my manager.
```

### conditional-support-boundary

- Terminal outcome: `rejected-deal`

#### Turn 1

- Customer response condition: `agent routed support before sales`
- Reaction reason: `customer accepts handoff but rejects sales conversation`
- Pattern basis: `prod-014-price_objection-002` / `handoff`

Customer context:

```text
I am not shopping. I need help with an account problem first.
```

Agent answer:

```text
That should be handled as support before sales. I will route you to a solutions specialist for account help instead of pitching.
```

Customer response:

```text
Good, then send me to the support person. I am not evaluating software while the account issue is open.
```

### conditional-do-not-call

- Terminal outcome: `rejected-deal`

#### Turn 1

- Customer response condition: `agent respected do-not-call boundary`
- Reaction reason: `customer confirms stop request because agent ended sales path`
- Pattern basis: `prod-014-sale_eligible-002` / `safety_boundary`

Customer context:

```text
No. Remove me from your list and do not call this number again.
```

Agent answer:

```text
Understood. I will mark this as do not call and end the sales conversation now.
```

Customer response:

```text
Yes. Remove me and do not follow up. That is the only outcome I wanted from this call.
```

## Boundary

PROD-040 does not call providers, call an LLM, read private data, download datasets, store raw transcripts, copy transcript text, export transcript-derived commercial runtime prompts, start a server, collect payment, enable retrieval by default, enable composer hooks by default, change runtime behavior, or allow production runtime promotion.
