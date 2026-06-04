# ELEVENLABS-008 Web Design Value And Pricing Repair

Package ID: `ELEVENLABS-008-web-design-value-pricing-repair`

## Decision

The previous `8/8` naturalness pass was not enough.

The screenshots exposed four defects that the prior tests did not punish hard
enough:

- internal reasoning leak: `I should not make it sound hidden`
- price dodging when an approved starting range is available
- treating a statement as a question: `Free usually means there is a catch`
- weak value framing around why a restaurant owner should inspect the mockup

## Sales Basis

This repair uses a compact value-selling correction, not a bulk sales dump.

External source checks:

- Salesforce consultative selling: understand customer challenges, listen, and
  recommend around the buyer's goals instead of pushing product features.
  Source: https://www.salesforce.com/blog/sales/consultative-sales-approach/
- HubSpot objection handling: price objections are common and should be handled
  by demonstrating value and addressing the real concern, not by pressure or
  defensive arguing.
  Source: https://blog.hubspot.com/sales/handling-common-sales-objections
- Bain Elements of Value: value depends on what customers actually care about;
  competing only on price/performance is weak, and value points should be tied
  to buyer motivation.
  Source: https://www.bain.com/consulting-services/customer-strategy-and-marketing/elements-of-value/

Applied to Atlas Web Studio, that means:

- state the approved price anchor when asked
- keep the free mockup as the low-risk first step
- translate website details into restaurant value: less confusion before
  customers call, easier customer decisions, and a concrete homepage direction
  the owner can judge
- never promise more customers, bookings, revenue, SEO ranking, or traffic

## What This Changes

- Updates `universal_sales_core.md` with value and pricing objection rules.
- Adds Atlas campaign pricing variables:
  - starting price: `$1,000`
  - premium/immersive anchor: `$5,000`
  - scope caveat: pages, content, integrations, design depth, and premium or
    immersive work
- Updates the live prompt source to block internal self-correction and require
  direct price answers when the buyer asks.
- Repairs misleading prior turns in the `ELEVENLABS-007` naturalness test pack.
- Adds six value/pricing stress tests in folder:

```text
Atlas Web Studio - Value Pricing Stress
```

## Test Target

The new value/pricing tests cover:

- direct starting-price disclosure
- higher-scope rough range without fake certainty
- statement-vs-question repair for free/catch skepticism
- staff callback after 3 without restarting the pitch
- phone-reservation value point without checklist stuffing
- explaining why the mockup is worth a quick look without unsupported claims

## Provider Patch

The intended live patch keeps the same agent and temperature `0.25`, but
updates:

- prompt value/pricing rules
- dynamic-variable placeholders
- attached universal sales core KB document after re-upload

Final live patch evidence:

- agent ID: `agent_7801kt0g32zxf4f8x5zkykj7syty`
- KB document ID: `42SRCbmq10xDhqIIve73`
- test folder ID: `tfld_2301kta29zg4edxb33ja2bbqq1p6`
- final suite ID: `suite_0401kta2yzeceppb9nebv28ejst3`
- final result: `6/6` passed
- sanitized result summary:
  `research/experiments/generated/ELEVENLABS-008-web-design-value-pricing-repair/value_pricing_results_summary.json`

Intermediate reruns mattered. The first live poll exposed that the agent still
apologized or spoke about grammar on the free/catch path and still stuffed
menu/hours into the phone-reservation path. The final prompt and tests were
tightened before accepting the result.

## Boundary

- No private customer data is used.
- No API key value is logged.
- No real customer calls are allowed.
- Pricing language is campaign-specific. It must not become universal default
  pricing for future clients.
- Passing these tests still is not proof of real call quality. Human transcript
  and audio review remains required.

## Validation

Run:

```powershell
python scripts\validate_elevenlabs_008_web_design_value_pricing.py
```
