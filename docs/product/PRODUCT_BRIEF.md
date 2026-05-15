# Product Brief

## Purpose

Define the product-facing direction for the Emotion Aware AI Sales Agent.

This project is both:

- a bachelor thesis project
- a real product intended for a paying client after launch

The thesis and product tracks should support each other, but they are not identical.

## Product Goal

Build a usable autonomous AI sales agent that can adapt its response strategy based on customer state and help sales conversations move forward more effectively.

The launch target is autonomous operation, with fallback and escalation guardrails for uncertain, risky, or out-of-scope conversations.

The product should be vertical-agnostic. It is intended for call centers and sales teams that sell different products or services, not one fixed product category.

The product is not limited to selling to companies. It should support both B2B and B2C sales contexts:

- B2B: business contacts, teams, departments, and company decision-makers
- B2C: individual consumers, households, or personal buyers

The product must also be low-latency. In a live call, the customer should normally hear the first response within 1-2 seconds after they finish speaking. If a turn requires slower lookup or verification, the agent should immediately use a short bridge response and continue the deeper work in the background.

## Initial Product Positioning

The current product direction is a configurable autonomous sales agent for constrained outbound calling workflows, with appointment-setting as a lower-risk campaign mode rather than the full product boundary.

A more realistic early product positioning is:

`A configurable emotion-aware autonomous calling agent that qualifies potential customers, adapts to their conversational state, follows campaign-specific guardrails, and either closes the campaign-defined next step or logs the right non-sale outcome.`

For full-sale campaigns, "close" means a verbal commitment, confirmed next action, sale-ready outcome, or approved handoff. It does not mean autonomous payment collection, contract signing, regulated advice, or unsupported product claims.

The first simulation case set is B2B-leaning because the initial client workflow focused on business lead qualification. That should not constrain the long-term product scope.

The first concrete client example is a German call center selling insurance products to consumers, including dental insurance and cancer-related or serious-illness insurance. This should be treated as a sensitive B2C insurance sales context, not ordinary generic lead qualification.

That client is an early vertical example, not the product boundary. Future clients may sell windows, glasses, SD cards, software, services, or many other products through call centers. Those examples are illustrative, not exhaustive.

## Likely First Client Value

The first client is most likely buying:

- faster lead handling
- better objection handling
- more consistent sales responses
- reduced manual follow-up effort
- insight into customer hesitation and interest
- automated appointment setting for interested leads

The client is probably not buying academic metrics directly, but thesis experiments can support product credibility.

## Product MVP

Start with a constrained autonomous full-sale simulation for approved campaign types, while keeping lead qualification, scheduling, and handoff as supported lower-risk modes.

MVP capabilities:

- accept a dialogue transcript or manually entered conversation context
- load a campaign configuration for the product being sold
- run a real-time response path optimized for 1-2 second first response latency
- estimate compact customer state
- select a persuasion strategy
- generate and execute the next response autonomously in the target channel
- ask a short sequence of client-approved qualification questions
- classify interest state
- attempt a campaign-approved close when the customer is eligible and interested
- correctly avoid closing when the right outcome is support, escalation, do-not-call, or no sale
- schedule a follow-up call with a human sales agent when that is the approved close or fallback
- decide whether to continue, bridge, transfer, end, close, or schedule-and-end each call turn
- log why the strategy was selected
- escalate or pause when confidence is low, policy boundaries are hit, or the user asks for a human

The live response path should not depend on chaining multiple sub-agents sequentially. Specialist modules can support compliance, product lookup, CRM updates, scheduling, and post-call evaluation, but the customer-facing turn should be handled by the fast real-time sales-agent core.

The live response path also needs explicit call-control behavior. The agent should hang up politely after do-not-call requests, clear refusals, repeated silence, voicemail handling, or completed follow-up/scheduling actions. See `runtime/policy/CALL_TERMINATION_POLICY.md`.

Development and testing may use human review, but launch behavior should not require human approval for every normal response.

For B2C workflows, the approved close may mean verbal purchase intent, a human sales call, consultation, service appointment, demo, callback, or other client-approved next step depending on the product.

For insurance workflows, the agent should qualify interest and schedule an approved human callback or specialist conversation. It should not act as a full autonomous insurance advisor or make detailed coverage, health, legal, or savings claims.

For other workflows, the agent should use the client's approved product facts, claims, scripts, and escalation rules.

## Sales Expert Training Loop

Experienced salespeople can train the agent during development.

Useful training actions:

- rate generated responses
- rewrite weak responses
- label customer objections
- label emotional or conversational state
- choose better persuasion strategies
- provide example responses for difficult cases
- identify unsafe, pushy, or unrealistic sales behavior

The agent should learn from this feedback through stages:

1. update prompts and strategy rules
2. build a library of high-quality examples for retrieval
3. create preference records for response ranking
4. consider fine-tuning only after enough clean examples exist

The first version of this loop should be lightweight and auditable.

## Product Track Versus Thesis Track

### Thesis track

Optimizes for:

- defensible methodology
- clear baseline comparisons
- reproducibility
- documented limitations
- academic honesty

### Product track

Optimizes for:

- client usefulness
- workflow fit
- reliability
- deployment path
- product trust and safety

## Product Risks

- overclaiming autonomy too early
- weak handling of edge cases and aggressive customers
- privacy and compliance issues with real sales conversations
- hallucinated or inappropriate sales claims
- poor integration with the client's actual workflow
- unclear responsibility when the AI suggests a bad response

## Product Guardrails

For the first client-ready version:

- keep human fallback available
- make selected strategies and confidence signals available in logs
- avoid manipulative or high-pressure wording
- log generated responses and selected strategies
- separate experimental thesis results from product claims
- do not use private client data without explicit permission and clear storage rules

Insurance-specific guardrails:

- avoid fear-based pressure around illness, cancer, family, or medical costs
- do not promise coverage, payout, approval, savings, or medical benefit
- escalate detailed policy, legal, health, pricing, or coverage questions to a human specialist
- avoid collecting unnecessary health or sensitive personal data

## Product Roadmap Relationship

The thesis experiments should validate the reasoning behind emotion-aware adaptation.
The product should turn that reasoning into a useful workflow.

The two tracks should meet in a small prototype:

```text
lead/contact details
  -> outbound call
  -> qualification questions
  -> customer-state estimate
  -> strategy selection
  -> low-latency response path
  -> autonomous response
  -> appointment scheduling when interested
  -> logging and confidence checks
  -> fallback or escalation when needed
```

See `runtime/architecture/REALTIME_AGENT_ARCHITECTURE.md` for the runtime layering, latency budget, bridge-response behavior, and sub-agent policy.

## Near-Term Product Step

After the prompt-comparison workflow is stable, define the first autonomous product workflow:

- lead/contact input
- qualification question flow
- detected state
- selected strategy
- generated and executed response
- scheduling handoff
- confidence or safety status
- escalation rule
- sales-expert feedback capture

The next concrete artifact after that is the qualification-question flow that defines:

- what the agent asks
- what signals count as `interested`, `maybe-interested`, or `not-interested`
- when to schedule a human follow-up call
- when to escalate or stop
