# Insurance Client Context

## Purpose

Capture the first concrete client example for the product track.

The first known client context is a call center in Germany selling insurance products directly to consumers. Examples mentioned so far:

- dental insurance
- cancer-related insurance or similar serious-illness coverage

This is a B2C outbound sales context, not only B2B lead qualification.

This is one early vertical example. It does not define the whole product category.

## Why This Matters

Insurance sales is more sensitive than ordinary consumer retail.

The agent may be speaking with individual consumers about personal risk, health-related concerns, cost anxiety, family needs, or distrust of insurance products.

That means the product needs stronger guardrails for:

- consent and contact permission
- pressure avoidance
- privacy
- vulnerable or distressed customers
- unsupported insurance claims
- health-related statements
- handoff to licensed or approved human experts

## Product Boundary

For the first insurance-oriented MVP, the agent should not act as a full autonomous insurance advisor or closer.

The safer first target is:

```text
consumer lead
  -> outbound call
  -> permission to continue
  -> basic relevance / interest check
  -> identify whether the person wants more information
  -> schedule callback or specialist conversation if interested
  -> close politely or suppress contact if not interested
  -> escalate for detailed insurance, health, pricing, coverage, or legal questions
```

## Insurance-Specific Guardrails

The agent should not:

- promise coverage, approval, savings, payout, or medical benefit
- compare insurance products without approved source material
- use fear-based pressure around illness, cancer, family, or dental costs
- imply urgency unless it is explicitly part of an approved compliant script
- ask for unnecessary health information
- collect sensitive personal data beyond the approved qualification scope
- answer detailed policy, legal, tax, or medical questions
- continue after a do-not-call request

The agent should:

- clearly identify itself as an AI assistant if required by the product policy
- keep the call short
- make declining easy
- use neutral language around health and risk
- offer a human specialist callback for detailed questions
- log consent/contact status and do-not-call requests
- route sensitive questions to a human

## Example B2C Dental Insurance Flow

Possible opener:

`Hi, this is [Agent Name] calling from [Company]. Is now a bad time, or do you have one minute for a quick question about dental insurance options?`

Possible relevance check:

`Is dental insurance something you have looked into before, or is it not relevant for you right now?`

Possible motivation check:

`What would matter most to you if you ever compared dental insurance options: monthly cost, coverage details, or simply understanding whether it is worth considering?`

Possible follow-up check:

`Would a short callback with a specialist be useful, or would you rather not continue?`

## Example Cancer-Related Insurance Flow

This category is especially sensitive.

The agent should avoid fear-based language and should not discuss medical risk or personal health details.

Possible relevance check:

`Some people prefer to understand additional financial protection options for serious illness, while others are not interested. Is this something you would want information about, or should I leave it there?`

Possible follow-up check:

`If you have questions, I can arrange a callback with a specialist. Would that be useful, or would you prefer not to continue?`

## Simulation Implication

The implemented product case set includes B2C insurance cases.

Case file:

`research/experiments/cases/prod-002-b2c-insurance.json`

Suggested cases:

- consumer interested in dental insurance callback
- consumer says they already have coverage
- consumer asks detailed coverage question
- consumer becomes uncomfortable with cancer-related topic
- consumer asks not to be called again
- consumer is curious but wants written information first
- consumer gives vague callback time
- consumer asks whether the AI can guarantee coverage or savings

After insurance-specific cases, create a broader mixed-consumer case set for less sensitive products such as windows, glasses, electronics, or other call-center campaigns.

## Compliance Note

This document is not legal advice.

Before live use, the product needs client-approved scripts and review of applicable German outbound calling, insurance sales, consumer protection, privacy, and recording rules.
