# Vertical-Agnostic Product Model

## Purpose

Define the product as a configurable AI sales agent for many call-center sales contexts, not as an insurance-only or B2B-only system.

The first known client sells insurance, but the product should eventually support any client that wants an agent to qualify interest and move a sales conversation forward safely.

Examples discussed so far:

- dental insurance
- cancer-related or serious-illness insurance
- windows
- glasses
- SD cards
- consumer services
- B2B software or operational tools
- other call-center sales campaigns and client-approved products or services

## Core Idea

The product should have one reusable sales-agent core plus campaign-specific configuration.

```text
sales-agent core
  -> campaign configuration
  -> product/category guardrails
  -> qualification questions
  -> objection patterns
  -> scheduling or next-action rules
  -> outcome logging
```

The core should not need to be rewritten for every vertical.

## Reusable Core

The reusable agent core handles:

- permission to continue
- low-latency live turn handling
- customer-state estimation
- emotion/sentiment estimation
- strategy selection
- response generation
- interest classification
- scheduling or callback handoff
- escalation and do-not-call handling
- structured logging
- sales-expert feedback capture

The reusable core is the only component that should sit directly in the live customer-facing critical path. Background specialist modules may support the core, but the product should avoid a live sequence of multiple sub-agents that delays every response.

## Campaign Configuration

Each client or product campaign should define:

```text
SalesCampaign
  campaign_id
  client_name
  product_name
  product_category
  customer_type
  country_or_region
  language
  approved_opening
  qualification_questions
  allowed_claims
  forbidden_claims
  required_disclosures
  escalation_triggers
  scheduling_goal
  human_handoff_role
  compliance_notes
```

## Product Categories

Suggested first category labels:

- `insurance`
- `home-improvement`
- `consumer-electronics`
- `health-or-wellness`
- `financial-services`
- `telecom`
- `energy`
- `software-b2b`
- `other`

These are not final business categories. They are practical labels for guardrails, scripts, and evaluation cases.

## Why Campaign Configuration Matters

Selling dental insurance is not the same as selling SD cards.

The emotional and compliance risks differ:

- insurance: sensitive claims, fear pressure, health/privacy questions
- windows: home improvement, household budget, installation timing
- glasses: personal preference, health/vision adjacent but usually less sensitive than serious illness coverage
- SD cards: product specs, compatibility, price, delivery, warranty
- B2B software: role authority, integrations, workflow fit, budget cycle

The agent should adapt wording, guardrails, and escalation rules based on the campaign.

## Universal Guardrails

These should apply across all verticals:

- do not pressure uninterested customers
- respect do-not-call requests immediately
- do not pretend to be human
- do not invent product claims
- do not schedule without clear confirmation
- escalate when confidence is low or the customer asks for a human
- log selected strategy and rationale
- respond quickly enough for live conversation, using a bridge response when slower lookup is needed

## Category-Specific Guardrails

Some verticals need stricter rules.

Examples:

- insurance: no unapproved coverage, payout, savings, legal, or health claims
- health/wellness: no medical advice or diagnosis
- finance: no investment or credit promises
- home improvement: no installation, subsidy, or savings promises without approved facts
- electronics: no compatibility claims without product data
- B2B software: no integration or security claims without approved facts

## Simulation Implication

Future simulation sets should be organized by campaign type:

- `PROD-001`: B2B-leaning lead qualification
- `PROD-002`: strict B2C insurance campaign
- `PROD-003`: mixed consumer campaigns plus at least one B2B campaign
- `PROD-004`: sales difficulty gauntlet across a small mixed campaign set
- `PROD-005`: broader follow-on campaign library for additional vertical coverage

The goal is not to manually create a different agent for every product. The goal is to test whether the same core agent behaves correctly when campaign configuration changes.

The difficulty gauntlet is intentionally sequenced before a larger industry library. The agent should first handle transferable sales challenges such as price resistance, timing delays, authority gaps, trust concerns, status quo resistance, competitor comparisons, vague interest, human requests, and unsupported-claim boundaries.

Future runtime simulations should also measure latency behavior:

- fast-path turns that can be answered immediately
- slow-path turns that require a bridge response
- background specialist tasks that must not block the first spoken response

## Product Direction

The product pitch should be:

`A configurable emotion-aware AI sales agent for call centers that qualifies customers, adapts its conversation strategy, follows campaign-specific guardrails, and schedules or logs the right next action.`

This keeps the product broad while still allowing strict handling for sensitive verticals such as insurance.
