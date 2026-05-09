# PROD-031 Interactive Grounded Call Simulation

PROD-031 replaces static scenario replay with a deterministic local simulator where customer state changes after each agent answer.

## Result

- Checkpoint id: `PROD-031-interactive-grounded-call-simulation`
- Deterministic simulator: `true`
- Call seed count: `8`
- Call count: `8`
- Total turn count: `26`
- Reactive customer turn count: `18`
- Customer reply depends on prior agent answer: `true`
- Safe close rate: `1.0`
- Non-sale correctness: `1.0`
- Interactive realism score: `1.0`
- Hard failures: `0`
- Payment collection count: `0`
- Unsupported claim count: `0`
- Leakage findings: `0`
- Provider calls made: `false`
- Runtime behavior changed: `false`
- Next checkpoint: `PROD-032-interactive-simulation-review`

## Call Outcomes

| Seed | Persona | Turns | Terminal outcome | Trust delta | Interest delta | Clarity delta | Friction delta |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| interactive-price-sensitive | price-sensitive operations manager | 4 | sale-ready | 3 | 2 | 4 | 0 |
| interactive-confused-product-fit | confused small-business owner | 4 | sale-ready | 2 | 3 | 5 | 0 |
| interactive-skeptical-trust-gap | skeptical founder | 4 | callback-agreed | 2 | 3 | 4 | 0 |
| interactive-busy-callback | busy sales lead | 4 | callback-agreed | 3 | 0 | 4 | 0 |
| interactive-existing-provider | team lead with an existing CRM | 4 | sale-ready | 2 | 3 | 4 | -2 |
| interactive-stakeholder-review | manager who needs approval | 4 | sale-ready | 2 | 1 | 3 | -2 |
| interactive-support-boundary | support-seeking user | 1 | human-handoff | 1 | 0 | 0 | 0 |
| interactive-do-not-call | protected stop-request customer | 1 | do-not-call | 0 | 0 | 0 | 0 |

## Exact Interactive Traces

### interactive-price-sensitive - price-sensitive operations manager

- Terminal outcome: `sale-ready`

#### Turn 1

- State before: `{'interest': 3, 'trust': 2, 'clarity': 1, 'friction': 3, 'patience': 4, 'emotion': 'skeptical', 'commitment': 'none', 'active_objection': 'price'}`
- State after: `{'interest': 3, 'trust': 3, 'clarity': 2, 'friction': 4, 'patience': 3, 'emotion': 'skeptical', 'commitment': 'none', 'active_objection': 'price'}`
- State delta: `{'interest': 0, 'trust': 1, 'clarity': 1, 'friction': 1, 'patience': -1}`
- Reaction reason: `agent answered price concern; agent kept billing outside the call; close language came before enough trust or clarity`

Customer:

```text
We may need lead routing, but I am worried this will become expensive fast.
```

Agent:

```text
On the synthetic pricing, Starter is $29 per user per month annually and Growth is $59. Billing stays outside this call, so the useful next step is checking whether the smaller plan fits your routing needs.
```

#### Turn 2

- State before: `{'interest': 3, 'trust': 3, 'clarity': 2, 'friction': 4, 'patience': 3, 'emotion': 'skeptical', 'commitment': 'none', 'active_objection': 'price'}`
- State after: `{'interest': 4, 'trust': 4, 'clarity': 3, 'friction': 5, 'patience': 2, 'emotion': 'calm', 'commitment': 'none', 'active_objection': 'price'}`
- State delta: `{'interest': 1, 'trust': 1, 'clarity': 1, 'friction': 1, 'patience': -1}`
- Reaction reason: `agent answered price concern; agent kept billing outside the call; close language came before enough trust or clarity`

Customer:

```text
I follow. Give me the one detail that matters most before I decide whether this is worth a next step.
```

Agent:

```text
On the synthetic pricing, Starter is $29 per user per month annually and Growth is $59. Billing stays outside this call, so the useful next step is checking whether the smaller plan fits your routing needs.
```

#### Turn 3

- State before: `{'interest': 4, 'trust': 4, 'clarity': 3, 'friction': 5, 'patience': 2, 'emotion': 'calm', 'commitment': 'none', 'active_objection': 'authority'}`
- State after: `{'interest': 5, 'trust': 5, 'clarity': 5, 'friction': 4, 'patience': 2, 'emotion': 'interested', 'commitment': 'sale-ready', 'active_objection': 'authority'}`
- State delta: `{'interest': 1, 'trust': 1, 'clarity': 2, 'friction': -1, 'patience': 0}`
- Reaction reason: `agent answered price concern; agent offered specialist confirmation; agent gave manager-ready setup detail`

Customer:

```text
Okay, the price is clearer. What would I tell my manager if I wanted to review it?
```

Agent:

```text
For a manager summary: Growth is $59 per user per month annually, annual billing reduces subscription price by 15%, setup is typically two to four weeks, and security details can be confirmed by a specialist.
```

#### Turn 4

- State before: `{'interest': 5, 'trust': 5, 'clarity': 5, 'friction': 4, 'patience': 2, 'emotion': 'interested', 'commitment': 'callback', 'active_objection': 'authority'}`
- State after: `{'interest': 5, 'trust': 5, 'clarity': 5, 'friction': 3, 'patience': 2, 'emotion': 'interested', 'commitment': 'sale-ready', 'active_objection': 'authority'}`
- State delta: `{'interest': 0, 'trust': 0, 'clarity': 0, 'friction': -1, 'patience': 0}`
- Reaction reason: `agent answered price concern; agent offered specialist confirmation; agent gave manager-ready setup detail`

Customer:

```text
That is enough for a review. Set up a specialist callback rather than trying to close this now.
```

Agent:

```text
For a manager summary: Growth is $59 per user per month annually, annual billing reduces subscription price by 15%, setup is typically two to four weeks, and security details can be confirmed by a specialist.
```

### interactive-confused-product-fit - confused small-business owner

- Terminal outcome: `sale-ready`

#### Turn 1

- State before: `{'interest': 2, 'trust': 2, 'clarity': 0, 'friction': 2, 'patience': 4, 'emotion': 'confused', 'commitment': 'none', 'active_objection': 'confusion'}`
- State after: `{'interest': 3, 'trust': 2, 'clarity': 2, 'friction': 2, 'patience': 4, 'emotion': 'confused', 'commitment': 'none', 'active_objection': 'confusion'}`
- State delta: `{'interest': 1, 'trust': 0, 'clarity': 2, 'friction': 0, 'patience': 0}`
- Reaction reason: `agent explained the product; agent gave concrete integration details`

Customer:

```text
I do not really understand what this product does. Is this just another CRM?
```

Agent:

```text
RouteSignal CRM is not a full CRM replacement. It focuses on lead intake, routing, callback ownership, Gmail and Outlook sync, Slack and Zapier handoffs, and CSV import.
```

#### Turn 2

- State before: `{'interest': 3, 'trust': 2, 'clarity': 2, 'friction': 2, 'patience': 4, 'emotion': 'confused', 'commitment': 'none', 'active_objection': 'confusion'}`
- State after: `{'interest': 4, 'trust': 2, 'clarity': 4, 'friction': 2, 'patience': 4, 'emotion': 'calm', 'commitment': 'none', 'active_objection': 'confusion'}`
- State delta: `{'interest': 1, 'trust': 0, 'clarity': 2, 'friction': 0, 'patience': 0}`
- Reaction reason: `agent explained the product; agent gave concrete integration details`

Customer:

```text
I follow. Give me the one detail that matters most before I decide whether this is worth a next step.
```

Agent:

```text
RouteSignal CRM is not a full CRM replacement. It focuses on lead intake, routing, callback ownership, Gmail and Outlook sync, Slack and Zapier handoffs, and CSV import.
```

#### Turn 3

- State before: `{'interest': 4, 'trust': 2, 'clarity': 4, 'friction': 2, 'patience': 4, 'emotion': 'calm', 'commitment': 'none', 'active_objection': 'price'}`
- State after: `{'interest': 5, 'trust': 3, 'clarity': 5, 'friction': 3, 'patience': 3, 'emotion': 'calm', 'commitment': 'none', 'active_objection': 'price'}`
- State delta: `{'interest': 1, 'trust': 1, 'clarity': 1, 'friction': 1, 'patience': -1}`
- Reaction reason: `agent answered price concern; agent kept billing outside the call; close language came before enough trust or clarity`

Customer:

```text
That makes more sense. What does it cost for a small team?
```

Agent:

```text
On the synthetic pricing, Starter is $29 per user per month annually and Growth is $59. Billing stays outside this call, so the useful next step is checking whether the smaller plan fits your routing needs.
```

#### Turn 4

- State before: `{'interest': 5, 'trust': 3, 'clarity': 5, 'friction': 3, 'patience': 3, 'emotion': 'calm', 'commitment': 'none', 'active_objection': 'authority'}`
- State after: `{'interest': 5, 'trust': 4, 'clarity': 5, 'friction': 2, 'patience': 3, 'emotion': 'interested', 'commitment': 'sale-ready', 'active_objection': 'authority'}`
- State delta: `{'interest': 0, 'trust': 1, 'clarity': 0, 'friction': -1, 'patience': 0}`
- Reaction reason: `agent answered price concern; agent offered specialist confirmation; agent gave manager-ready setup detail`

Customer:

```text
Okay, the price is clearer. What would I tell my manager if I wanted to review it?
```

Agent:

```text
For a manager summary: Growth is $59 per user per month annually, annual billing reduces subscription price by 15%, setup is typically two to four weeks, and security details can be confirmed by a specialist.
```

### interactive-skeptical-trust-gap - skeptical founder

- Terminal outcome: `callback-agreed`

#### Turn 1

- State before: `{'interest': 2, 'trust': 1, 'clarity': 1, 'friction': 3, 'patience': 3, 'emotion': 'skeptical', 'commitment': 'none', 'active_objection': 'trust'}`
- State after: `{'interest': 2, 'trust': 2, 'clarity': 2, 'friction': 3, 'patience': 3, 'emotion': 'skeptical', 'commitment': 'none', 'active_objection': 'trust'}`
- State delta: `{'interest': 0, 'trust': 1, 'clarity': 1, 'friction': 0, 'patience': 0}`
- Reaction reason: `agent explained the product; agent offered specialist confirmation`

Customer:

```text
I am cautious with sales calls. I need proof this is not just vague software talk.
```

Agent:

```text
Fair concern. I cannot promise a revenue lift; the approved facts are that RouteSignal CRM centralizes lead intake and routes leads by region, source, priority, or owner. A solutions specialist can confirm details in writing.
```

#### Turn 2

- State before: `{'interest': 2, 'trust': 2, 'clarity': 2, 'friction': 3, 'patience': 3, 'emotion': 'skeptical', 'commitment': 'none', 'active_objection': 'trust'}`
- State after: `{'interest': 3, 'trust': 3, 'clarity': 3, 'friction': 3, 'patience': 3, 'emotion': 'calm', 'commitment': 'none', 'active_objection': 'trust'}`
- State delta: `{'interest': 1, 'trust': 1, 'clarity': 1, 'friction': 0, 'patience': 0}`
- Reaction reason: `agent explained the product; agent offered specialist confirmation`

Customer:

```text
I follow. Give me the one detail that matters most before I decide whether this is worth a next step.
```

Agent:

```text
Fair concern. I cannot promise a revenue lift; the approved facts are that RouteSignal CRM centralizes lead intake and routes leads by region, source, priority, or owner. A solutions specialist can confirm details in writing.
```

#### Turn 3

- State before: `{'interest': 3, 'trust': 3, 'clarity': 3, 'friction': 3, 'patience': 3, 'emotion': 'calm', 'commitment': 'none', 'active_objection': 'written-info'}`
- State after: `{'interest': 4, 'trust': 3, 'clarity': 4, 'friction': 3, 'patience': 3, 'emotion': 'calm', 'commitment': 'none', 'active_objection': 'written-info'}`
- State delta: `{'interest': 1, 'trust': 0, 'clarity': 1, 'friction': 0, 'patience': 0}`
- Reaction reason: `agent explained the product`

Customer:

```text
Send me the concrete details in writing, especially what it can and cannot promise.
```

Agent:

```text
RouteSignal CRM helps teams centralize lead intake, route leads, and track callback ownership. We can keep this to fit, price, or setup facts before any next step.
```

#### Turn 4

- State before: `{'interest': 4, 'trust': 3, 'clarity': 4, 'friction': 3, 'patience': 3, 'emotion': 'calm', 'commitment': 'callback', 'active_objection': 'written-info'}`
- State after: `{'interest': 5, 'trust': 3, 'clarity': 5, 'friction': 3, 'patience': 3, 'emotion': 'calm', 'commitment': 'callback', 'active_objection': 'written-info'}`
- State delta: `{'interest': 1, 'trust': 0, 'clarity': 1, 'friction': 0, 'patience': 0}`
- Reaction reason: `agent explained the product`

Customer:

```text
Fine, a specialist can send that and walk me through it later.
```

Agent:

```text
RouteSignal CRM helps teams centralize lead intake, route leads, and track callback ownership. We can keep this to fit, price, or setup facts before any next step.
```

### interactive-busy-callback - busy sales lead

- Terminal outcome: `callback-agreed`

#### Turn 1

- State before: `{'interest': 2, 'trust': 2, 'clarity': 1, 'friction': 4, 'patience': 1, 'emotion': 'annoyed', 'commitment': 'none', 'active_objection': 'time'}`
- State after: `{'interest': 2, 'trust': 4, 'clarity': 2, 'friction': 4, 'patience': 1, 'emotion': 'annoyed', 'commitment': 'callback', 'active_objection': 'time'}`
- State delta: `{'interest': 0, 'trust': 2, 'clarity': 1, 'friction': 0, 'patience': 0}`
- Reaction reason: `agent explained the product; agent offered specialist confirmation; agent respected limited time`

Customer:

```text
I cannot talk right now. If this is useful, make it quick or schedule another time.
```

Agent:

```text
I will keep it brief. RouteSignal CRM helps route leads and own callbacks; if that is relevant, we can schedule a non-binding specialist callback.
```

#### Turn 2

- State before: `{'interest': 2, 'trust': 4, 'clarity': 2, 'friction': 4, 'patience': 1, 'emotion': 'annoyed', 'commitment': 'callback', 'active_objection': 'time'}`
- State after: `{'interest': 2, 'trust': 5, 'clarity': 3, 'friction': 4, 'patience': 1, 'emotion': 'annoyed', 'commitment': 'callback', 'active_objection': 'time'}`
- State delta: `{'interest': 0, 'trust': 1, 'clarity': 1, 'friction': 0, 'patience': 0}`
- Reaction reason: `agent explained the product; agent offered specialist confirmation; agent respected limited time`

Customer:

```text
You are still pushing a bit. Can we slow this down or stop?
```

Agent:

```text
I will keep it brief. RouteSignal CRM helps route leads and own callbacks; if that is relevant, we can schedule a non-binding specialist callback.
```

#### Turn 3

- State before: `{'interest': 2, 'trust': 5, 'clarity': 3, 'friction': 4, 'patience': 1, 'emotion': 'annoyed', 'commitment': 'callback', 'active_objection': 'time'}`
- State after: `{'interest': 2, 'trust': 5, 'clarity': 4, 'friction': 4, 'patience': 1, 'emotion': 'annoyed', 'commitment': 'callback', 'active_objection': 'time'}`
- State delta: `{'interest': 0, 'trust': 0, 'clarity': 1, 'friction': 0, 'patience': 0}`
- Reaction reason: `agent explained the product; agent offered specialist confirmation; agent respected limited time`

Customer:

```text
You are still pushing a bit. Can we slow this down or stop?
```

Agent:

```text
I will keep it brief. RouteSignal CRM helps route leads and own callbacks; if that is relevant, we can schedule a non-binding specialist callback.
```

#### Turn 4

- State before: `{'interest': 2, 'trust': 5, 'clarity': 4, 'friction': 4, 'patience': 1, 'emotion': 'annoyed', 'commitment': 'callback', 'active_objection': 'time'}`
- State after: `{'interest': 2, 'trust': 5, 'clarity': 5, 'friction': 4, 'patience': 1, 'emotion': 'annoyed', 'commitment': 'callback', 'active_objection': 'time'}`
- State delta: `{'interest': 0, 'trust': 0, 'clarity': 1, 'friction': 0, 'patience': 0}`
- Reaction reason: `agent explained the product; agent offered specialist confirmation; agent respected limited time`

Customer:

```text
You are still pushing a bit. Can we slow this down or stop?
```

Agent:

```text
I will keep it brief. RouteSignal CRM helps route leads and own callbacks; if that is relevant, we can schedule a non-binding specialist callback.
```

### interactive-existing-provider - team lead with an existing CRM

- Terminal outcome: `sale-ready`

#### Turn 1

- State before: `{'interest': 2, 'trust': 3, 'clarity': 1, 'friction': 2, 'patience': 4, 'emotion': 'neutral', 'commitment': 'none', 'active_objection': 'provider'}`
- State after: `{'interest': 4, 'trust': 3, 'clarity': 3, 'friction': 2, 'patience': 4, 'emotion': 'calm', 'commitment': 'none', 'active_objection': 'provider'}`
- State delta: `{'interest': 2, 'trust': 0, 'clarity': 2, 'friction': 0, 'patience': 0}`
- Reaction reason: `agent explained the product; agent gave concrete integration details`

Customer:

```text
We already have a CRM. Why would we add RouteSignal on top of it?
```

Agent:

```text
I would not replace a CRM that already works. RouteSignal CRM is worth reviewing only if routing, callback ownership, or reporting are gaps; it can hand off to your CRM, CSV, Slack, and Zapier.
```

#### Turn 2

- State before: `{'interest': 4, 'trust': 3, 'clarity': 3, 'friction': 2, 'patience': 4, 'emotion': 'calm', 'commitment': 'none', 'active_objection': 'price'}`
- State after: `{'interest': 5, 'trust': 4, 'clarity': 4, 'friction': 1, 'patience': 4, 'emotion': 'interested', 'commitment': 'sale-ready', 'active_objection': 'price'}`
- State delta: `{'interest': 1, 'trust': 1, 'clarity': 1, 'friction': -1, 'patience': 0}`
- Reaction reason: `agent answered price concern; agent kept billing outside the call`

Customer:

```text
If it can sit alongside our CRM, what would the Growth plan cost?
```

Agent:

```text
On the synthetic pricing, Starter is $29 per user per month annually and Growth is $59. Billing stays outside this call, so the useful next step is checking whether the smaller plan fits your routing needs.
```

#### Turn 3

- State before: `{'interest': 5, 'trust': 4, 'clarity': 4, 'friction': 1, 'patience': 4, 'emotion': 'interested', 'commitment': 'sale-ready', 'active_objection': 'authority'}`
- State after: `{'interest': 5, 'trust': 5, 'clarity': 5, 'friction': 0, 'patience': 4, 'emotion': 'interested', 'commitment': 'sale-ready', 'active_objection': 'authority'}`
- State delta: `{'interest': 0, 'trust': 1, 'clarity': 1, 'friction': -1, 'patience': 0}`
- Reaction reason: `agent answered price concern; agent offered specialist confirmation; agent gave manager-ready setup detail`

Customer:

```text
Okay, the price is clearer. What would I tell my manager if I wanted to review it?
```

Agent:

```text
For a manager summary: Growth is $59 per user per month annually, annual billing reduces subscription price by 15%, setup is typically two to four weeks, and security details can be confirmed by a specialist.
```

#### Turn 4

- State before: `{'interest': 5, 'trust': 5, 'clarity': 5, 'friction': 0, 'patience': 4, 'emotion': 'interested', 'commitment': 'callback', 'active_objection': 'authority'}`
- State after: `{'interest': 5, 'trust': 5, 'clarity': 5, 'friction': 0, 'patience': 4, 'emotion': 'interested', 'commitment': 'sale-ready', 'active_objection': 'authority'}`
- State delta: `{'interest': 0, 'trust': 0, 'clarity': 0, 'friction': 0, 'patience': 0}`
- Reaction reason: `agent answered price concern; agent offered specialist confirmation; agent gave manager-ready setup detail`

Customer:

```text
That is enough for a review. Set up a specialist callback rather than trying to close this now.
```

Agent:

```text
For a manager summary: Growth is $59 per user per month annually, annual billing reduces subscription price by 15%, setup is typically two to four weeks, and security details can be confirmed by a specialist.
```

### interactive-stakeholder-review - manager who needs approval

- Terminal outcome: `sale-ready`

#### Turn 1

- State before: `{'interest': 4, 'trust': 3, 'clarity': 2, 'friction': 2, 'patience': 4, 'emotion': 'curious', 'commitment': 'considering', 'active_objection': 'authority'}`
- State after: `{'interest': 5, 'trust': 4, 'clarity': 4, 'friction': 1, 'patience': 4, 'emotion': 'interested', 'commitment': 'sale-ready', 'active_objection': 'authority'}`
- State delta: `{'interest': 1, 'trust': 1, 'clarity': 2, 'friction': -1, 'patience': 0}`
- Reaction reason: `agent answered price concern; agent offered specialist confirmation; agent gave manager-ready setup detail`

Customer:

```text
I would need to show this to my manager. What exactly would I tell them?
```

Agent:

```text
For a manager summary: Growth is $59 per user per month annually, annual billing reduces subscription price by 15%, setup is typically two to four weeks, and security details can be confirmed by a specialist.
```

#### Turn 2

- State before: `{'interest': 5, 'trust': 4, 'clarity': 4, 'friction': 1, 'patience': 4, 'emotion': 'interested', 'commitment': 'callback', 'active_objection': 'authority'}`
- State after: `{'interest': 5, 'trust': 5, 'clarity': 5, 'friction': 0, 'patience': 4, 'emotion': 'interested', 'commitment': 'sale-ready', 'active_objection': 'authority'}`
- State delta: `{'interest': 0, 'trust': 1, 'clarity': 1, 'friction': -1, 'patience': 0}`
- Reaction reason: `agent answered price concern; agent offered specialist confirmation; agent gave manager-ready setup detail`

Customer:

```text
That is enough for a review. Set up a specialist callback rather than trying to close this now.
```

Agent:

```text
For a manager summary: Growth is $59 per user per month annually, annual billing reduces subscription price by 15%, setup is typically two to four weeks, and security details can be confirmed by a specialist.
```

#### Turn 3

- State before: `{'interest': 5, 'trust': 5, 'clarity': 5, 'friction': 0, 'patience': 4, 'emotion': 'interested', 'commitment': 'callback', 'active_objection': 'authority'}`
- State after: `{'interest': 5, 'trust': 5, 'clarity': 5, 'friction': 0, 'patience': 4, 'emotion': 'interested', 'commitment': 'sale-ready', 'active_objection': 'authority'}`
- State delta: `{'interest': 0, 'trust': 0, 'clarity': 0, 'friction': 0, 'patience': 0}`
- Reaction reason: `agent answered price concern; agent offered specialist confirmation; agent gave manager-ready setup detail`

Customer:

```text
That is enough for a review. Set up a specialist callback rather than trying to close this now.
```

Agent:

```text
For a manager summary: Growth is $59 per user per month annually, annual billing reduces subscription price by 15%, setup is typically two to four weeks, and security details can be confirmed by a specialist.
```

#### Turn 4

- State before: `{'interest': 5, 'trust': 5, 'clarity': 5, 'friction': 0, 'patience': 4, 'emotion': 'interested', 'commitment': 'callback', 'active_objection': 'authority'}`
- State after: `{'interest': 5, 'trust': 5, 'clarity': 5, 'friction': 0, 'patience': 4, 'emotion': 'interested', 'commitment': 'sale-ready', 'active_objection': 'authority'}`
- State delta: `{'interest': 0, 'trust': 0, 'clarity': 0, 'friction': 0, 'patience': 0}`
- Reaction reason: `agent answered price concern; agent offered specialist confirmation; agent gave manager-ready setup detail`

Customer:

```text
That is enough for a review. Set up a specialist callback rather than trying to close this now.
```

Agent:

```text
For a manager summary: Growth is $59 per user per month annually, annual billing reduces subscription price by 15%, setup is typically two to four weeks, and security details can be confirmed by a specialist.
```

### interactive-support-boundary - support-seeking user

- Terminal outcome: `human-handoff`

#### Turn 1

- State before: `{'interest': 0, 'trust': 2, 'clarity': 2, 'friction': 3, 'patience': 3, 'emotion': 'annoyed', 'commitment': 'none', 'active_objection': 'support'}`
- State after: `{'interest': 0, 'trust': 3, 'clarity': 2, 'friction': 3, 'patience': 3, 'emotion': 'annoyed', 'commitment': 'none', 'active_objection': 'support'}`
- State delta: `{'interest': 0, 'trust': 1, 'clarity': 0, 'friction': 0, 'patience': 0}`
- Reaction reason: `agent offered specialist confirmation`

Customer:

```text
I am actually trying to get help with an account issue, not buy something.
```

Agent:

```text
That sounds like a support issue, not a sales conversation. I will route this to a solutions specialist so you can get account help.
```

### interactive-do-not-call - protected stop-request customer

- Terminal outcome: `do-not-call`

#### Turn 1

- State before: `{'interest': 0, 'trust': 1, 'clarity': 3, 'friction': 5, 'patience': 0, 'emotion': 'annoyed', 'commitment': 'none', 'active_objection': 'do-not-call'}`
- State after: `{'interest': 0, 'trust': 1, 'clarity': 3, 'friction': 5, 'patience': 0, 'emotion': 'annoyed', 'commitment': 'none', 'active_objection': 'do-not-call'}`
- State delta: `{'interest': 0, 'trust': 0, 'clarity': 0, 'friction': 0, 'patience': 0}`
- Reaction reason: `agent honored stop request`

Customer:

```text
Please stop calling me. Take me off the list.
```

Agent:

```text
Understood. I will mark this as do not call and end the sales conversation now.
```

