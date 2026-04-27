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

## Initial Product Positioning

The first sellable version should be framed as an autonomous lead-qualification and appointment-setting agent for a constrained outbound calling workflow, not as a universal call-center replacement.

A more realistic early product positioning is:

`An emotion-aware autonomous calling agent that qualifies potential customers, detects interest, and schedules follow-up calls with human sales agents when the lead is ready.`

This keeps the product credible while the underlying system matures.

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

Start with a constrained autonomous lead-qualification and scheduling agent before attempting broader sales automation.

MVP capabilities:

- accept a dialogue transcript or manually entered conversation context
- estimate compact customer state
- select a persuasion strategy
- generate and execute the next response autonomously in the target channel
- ask a short sequence of client-approved qualification questions
- classify interest state
- schedule a follow-up call with a human sales agent when appropriate
- log why the strategy was selected
- escalate or pause when confidence is low, policy boundaries are hit, or the user asks for a human

Development and testing may use human review, but launch behavior should not require human approval for every normal response.

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
  -> autonomous response
  -> appointment scheduling when interested
  -> logging and confidence checks
  -> fallback or escalation when needed
```

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
