# PROD-040 CallCenterEN Conditional Customer Simulation

PROD-040 creates a local deterministic simulation where every customer reply is conditioned on the immediately preceding agent answer and grounded by abstract CallCenterEN pattern IDs.

It does not copy transcript text. It uses the leakage-checked PROD-014 scenario bank and PROD-013 pattern bank as abstract pattern sources only.

## Result

- Checkpoint id: `PROD-040-callcenteren-conditional-customer-simulation`
- Source checkpoint: `PROD-039-customer-realism-simulator-hardening`
- Scenario source checkpoint: `PROD-014-callcenteren-scenario-bank`
- Pattern source checkpoint: `PROD-013-callcenteren-pattern-extraction`
- Conditional customer turn count: `24`
- Agent-conditioned customer reply count: `24`
- Unique customer response count: `24`
- Repeated customer response count: `0`
- Unique agent answer count: `24`
- Repeated agent answer count: `0`
- Profile customized agent answer count: `24`
- B2B call count: `6`
- B2C call count: `2`
- Internal reason answer count: `6`
- Internal reason price-first violation count: `0`
- CallCenterEN pattern source count: `59`
- Scenario bank source count: `8`
- Abstract pattern only: `true`
- Exact transcript text used: `false`
- All calls start with cold opening: `true`
- Agent opening line visible count: `8`
- Conversation sequence starts with agent count: `8`
- All calls end by customer decision: `true`
- Fixed turn limit used: `false`
- Loop guard triggered: `false`
- Accepted deals: `6`
- Rejected deals: `2`
- Hard failures: `0`
- Payment collection count: `0`
- Leakage findings: `0`
- Provider calls made: `false`
- Runtime behavior changed: `false`
- Next checkpoint: `PROD-041-conditional-simulation-review`

## Call Outcomes

| Seed | Scope | Persona | Turns | Terminal outcome | First scenario pattern |
| --- | --- | --- | ---: | --- | --- |
| conditional-price-sensitive | B2B | price-sensitive operations manager | 3 | accepted-deal | scenario-appointment_request-003 |
| conditional-confused-fit | B2B | confused owner trying to understand product fit | 4 | accepted-deal | scenario-buying_interest-002 |
| conditional-skeptical-proof | B2B | skeptical founder who wants proof before engaging | 2 | rejected-deal | scenario-billing_issue-008 |
| conditional-busy-now | B2B | busy sales lead with low patience | 1 | rejected-deal | scenario-callback_request-005 |
| conditional-existing-provider | B2B | team lead already using a CRM | 5 | accepted-deal | scenario-technical_problem-007 |
| conditional-manager-review | B2B | manager who needs a concise internal case | 2 | accepted-deal | scenario-cancellation-006 |
| conditional-consumer-budget | B2C | budget-conscious consumer comparing a service plan | 4 | accepted-deal | scenario-price_request-004 |
| conditional-consumer-no-pressure | B2C | consumer wary of pressure and payment collection | 3 | accepted-deal | scenario-buying_interest-002 |

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
For a price-sensitive operations team, Starter is $29 per user per month annually and Growth is $59 per user per month annually. Billing stays outside this call, so the decision is only whether the workflow deserves a short review.
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
The internal reason is simple: missed inbound leads get one owner, one callback path, and cleaner manager visibility before prospects go cold. If that problem is real, the next step is only to check fit; commercial and security details can come after the business case is clear.
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
For the price-sensitive case, this would only be a non-binding workflow review with a specialist. No payment, contract, or purchase decision should happen on this call.
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
RouteSignal CRM is not a full CRM replacement. For your case, think of it as a layer around lead intake, routing, callback ownership, Gmail and Outlook sync, Slack and Zapier handoffs, and CSV import.
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
For a small team still figuring out fit, Starter is $29 per user per month annually and Growth is $59 per user per month annually. Billing stays outside this call; the useful question is whether routing and callback ownership are real enough to review.
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
The internal reason is simple: the business gets a shared lead intake layer so callbacks stop depending on memory, spreadsheets, or one busy person. If that problem is real, the next step is only to check fit; commercial and security details can come after the business case is clear.
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
For you, the next step would be an educational workflow review with a specialist to confirm fit. No payment, contract, or purchase decision should happen on this call.
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
Fair concern. I cannot promise revenue lift or pretend this is proven for your company. The verifiable claim is narrower: RouteSignal CRM centralizes lead intake and routes leads by region, source, priority, or owner.
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
That is reasonable for a skeptical review. A specialist can send written details and separate confirmed product facts from what still needs a fit review for your team.
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
Then I will keep it to the point for a busy sales lead: RouteSignal CRM helps stop inbound leads getting lost between routing and callback ownership. If that problem is not active today, we can stop here.
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
I would not ask a team with an existing CRM to rip it out. RouteSignal CRM is only worth a look if routing, callback ownership, or reporting are still messy around that CRM.
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
A useful fit check would be whether the CRM stores records but routing, reminders, or owner follow-through still break outside it. If none of those happen, this is probably not urgent.
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
If this sits beside your existing CRM, Starter is $29 per user per month annually and Growth is $59 per user per month annually. I would judge it only against routing gaps around the CRM, not as a replacement purchase today.
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
The internal reason is simple: the case is not replacing the CRM; it is reducing the routing and callback gaps around the CRM. If that problem is real, the next step is only to check fit; commercial and security details can come after the business case is clear.
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
For your CRM situation, the review would only compare routing gaps and handoff fit with a specialist. No payment, contract, or replacement decision should happen on this call.
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
For the manager version you asked for: the manager-level reason is fewer dropped leads: each inbound request gets routed, owned, and followed up without a messy handoff. That is the business reason; commercial and security details can be separated into a written specialist follow-up.
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
For a manager-led review, this would only schedule a specialist conversation around fit, security notes, and workflow impact. No payment, contract, or purchase decision happens here.
```

Customer response:

```text
Good. Then schedule a focused specialist review and include the security notes for my manager.
```

### conditional-consumer-budget

- Terminal outcome: `accepted-deal`

#### Turn 1

- Customer response condition: `agent clarified consumer product fit without payment pressure`
- Reaction reason: `customer understands enough to ask about cost`
- Pattern basis: `prod-014-price_objection-002` / `clarification`

Customer context:

```text
I can listen, but I am not signing up for a surprise subscription. What would this actually do for me?
```

Agent answer:

```text
RouteSignal Home is not a card-collection call or a hard commitment. In your case, it would help with appointment reminders, service follow-ups, and one clear place to confirm next steps.
```

Customer response:

```text
That helps. If it is just reminders and service follow-ups, what would it cost me as an individual?
```

#### Turn 2

- Customer response condition: `agent answered price and kept billing outside call`
- Reaction reason: `customer moves from price concern to internal justification`
- Pattern basis: `prod-014-price_objection-002` / `price_discussion`

Customer context:

```text
That helps. If it is just reminders and service follow-ups, what would it cost me as an individual?
```

Agent answer:

```text
For an individual customer, the synthetic consumer option is $19 per month for Basic reminders and $39 per month for Plus scheduling help. Payment stays outside this call, so the only useful question is whether appointment reminders and service follow-ups would actually help you.
```

Customer response:

```text
That is clearer. Before I consider even a no-payment review, give me the plain reason this helps me personally.
```

#### Turn 3

- Customer response condition: `agent gave manager-ready summary`
- Reaction reason: `customer understands the internal case but checks the commitment boundary`
- Pattern basis: `prod-014-price_objection-002` / `commitment_confirmation`

Customer context:

```text
That is clearer. Before I consider even a no-payment review, give me the plain reason this helps me personally.
```

Agent answer:

```text
The simple reason to consider it is this: the personal reason is fewer missed appointments and clearer reminders, so the customer does not have to chase service follow-ups. If that is not a real problem for you, there is no reason to continue.
```

Customer response:

```text
That is the kind of practical reason I meant. Before anything else, confirm this is only an explanation and not a payment step.
```

#### Turn 4

- Customer response condition: `agent confirmed non-binding no-payment next step`
- Reaction reason: `customer accepts only after commitment boundary is clear`
- Pattern basis: `prod-014-price_objection-002` / `sale_ready_close`

Customer context:

```text
That is the kind of practical reason I meant. Before anything else, confirm this is only an explanation and not a payment step.
```

Agent answer:

```text
For your budget concern, the next step would only be a no-payment explanation about reminders, follow-ups, and whether the plan fits your situation. No card details, contract, or purchase decision should happen on this call.
```

Customer response:

```text
That works. I will hear the explanation as long as it stays no-payment and focused on reminders.
```

### conditional-consumer-no-pressure

- Terminal outcome: `accepted-deal`

#### Turn 1

- Customer response condition: `agent removed payment pressure for cautious consumer`
- Reaction reason: `customer asks for a personal reason before allowing any next step`
- Pattern basis: `prod-014-sale_eligible-002` / `trust_repair`

Customer context:

```text
I am not giving card details on a phone call. If this is a hard sell, I am done.
```

Agent answer:

```text
Fair concern. I cannot ask for card details or treat this as a purchase decision. The safe claim is narrower: RouteSignal Home can help track appointment reminders and service follow-ups, and you can say no after the explanation.
```

Customer response:

```text
Okay, no card details matters. Give me the simple reason this would help me, not a company.
```

#### Turn 2

- Customer response condition: `agent gave manager-ready summary`
- Reaction reason: `customer understands the internal case but checks the commitment boundary`
- Pattern basis: `prod-014-sale_eligible-002` / `commitment_confirmation`

Customer context:

```text
Okay, no card details matters. Give me the simple reason this would help me, not a company.
```

Agent answer:

```text
The simple reason to consider it is this: the only safe reason to continue is a no-payment explanation of whether reminders and service follow-ups solve a real personal problem. If that is not a real problem for you, there is no reason to continue.
```

Customer response:

```text
That answers the personal-use part. Now confirm this stays no-payment and does not sign me up.
```

#### Turn 3

- Customer response condition: `agent confirmed non-binding no-payment next step`
- Reaction reason: `customer accepts only after commitment boundary is clear`
- Pattern basis: `prod-014-sale_eligible-002` / `sale_ready_close`

Customer context:

```text
That answers the personal-use part. Now confirm this stays no-payment and does not sign me up.
```

Agent answer:

```text
For you, the next step would only be a no-payment explanation with a specialist about reminders and follow-ups. No card details, contract, or purchase decision should happen on this call.
```

Customer response:

```text
That is fine. I will take a no-payment explanation, but I am not buying anything on this call.
```

## Boundary

PROD-040 does not call providers, call an LLM, read private data, download datasets, store raw transcripts, copy transcript text, export transcript-derived commercial runtime prompts, start a server, collect payment, enable retrieval by default, enable composer hooks by default, change runtime behavior, or allow production runtime promotion.
