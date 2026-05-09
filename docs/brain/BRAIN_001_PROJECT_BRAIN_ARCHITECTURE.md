# BRAIN-001 Project Brain Architecture

BRAIN-001 defines what belongs inside the project brain for the Emotion Aware AI Sales Agent.

The brain is not a prompt dump and not a hidden all-knowing memory. It is a small runtime decision architecture:

```text
short-term call state
  + SalesCampaign facts and guardrails
  + buyer-state and emotion uncertainty
  + sales strategy rules
  + optional guarded retrieval
  + response planner
  + voice delivery profile
  + safety and handoff rules
```

This preserves the project principle:

```text
one reusable sales-agent core
  + configurable SalesCampaign profiles
  + explicit guardrails, consent, provider gates, and human escalation paths
```

## Scope

BRAIN-001 is an architecture checkpoint. It does not change runtime behavior by itself.

It answers:

- what information the agent should carry while answering a call
- what stays in the latency-critical live path
- what stays advisory-only until a separate validator promotes it
- how RAG, voice, campaign facts, and emotional understanding should fit together
- what must never enter the project brain

## Brain Layers

| Layer | Runtime role | Default status | Owner |
| --- | --- | --- | --- |
| Sales-agent core | Handles the live turn, state update, strategy choice, next action, and output contract. | Current runtime direction | Project-local runtime scripts |
| SalesCampaign profile | Supplies campaign language, product facts, allowed claims, qualification flow, disclosures, and escalation rules. | Current runtime input | Campaign config |
| Short-term call state | Tracks what the buyer said, what the agent promised, open objections, interest, risk, and current next action. | Runtime-required | Live call session |
| Buyer-state estimator | Treats emotion and intent as uncertain context from observable language and call behavior. | Runtime-required, conservative | Core response planner |
| Sales strategy library | Chooses discovery, clarification, trust repair, objection handling, summary, schedule, end, or handoff moves. | Runtime-required | Core plus reviewed rules |
| Guarded RAG hints | Adds source-backed advice only when retrieval is explicitly enabled and the context is allowed. | retrieval disabled by default | RAG-017/RAG-018 gates |
| Voice delivery profile | Converts accepted response text into provider-facing spoken delivery metadata and text. | Runtime delivery layer | RESP/VOICE checkpoints |
| Post-call learning | Uses reviewed feedback, simulation outcomes, and safe pattern notes to improve later rules. | Not in live path | Evaluation and review scripts |

## Live Path

The live path should stay small enough to respond within the 1-2 second product target.

```text
latest transcript
  -> campaign guardrail check
  -> compact buyer-state update
  -> difficulty and risk estimate
  -> strategy selection
  -> next-action and call-control decision
  -> response draft
  -> output contract
  -> voice delivery profile
  -> short-term call state update
```

The live path should not wait for broad research, slow multi-agent debate, CRM enrichment, post-call scoring, or long retrieval pipelines before every ordinary reply.

## Short-Term Call State

The brain should carry only the minimum live state needed to avoid sounding forgetful or unsafe:

- `conversation_stage`: opening, discovery, objection, proof request, scheduling, handoff, refusal, do-not-call, or close.
- `buyer_goal`: the buyer's stated practical goal or concern, not a guessed private motive.
- `buyer_emotional_signal`: observable uncertainty, skepticism, confusion, frustration, urgency, interest, or calm.
- `emotion_confidence`: low, medium, or high confidence; high confidence still does not justify hidden-state claims.
- `open_objections`: price, time, authority, trust, relevance, complexity, privacy, existing provider, or unknown.
- `agent_promises`: information, callback, handoff, schedule, or follow-up already offered.
- `allowed_next_actions`: ask, clarify, summarize, answer from approved facts, bridge, schedule, transfer, end, or hand off.
- `blocked_actions`: unsupported claim, pressure tactic, unapproved medical/legal/financial advice, biometric emotion claim, or protected-text rewrite.

This is short-term call state. Long-term customer memory, raw transcripts, and private audio are outside this architecture until a separate data-governance checkpoint approves them.

## Buyer-State And Emotion Rules

The agent should use emotional understanding as a decision aid, not as a claim about the buyer's mind.

Allowed:

- "It sounds like the main concern is whether this is worth the effort."
- "Let me make this simpler."
- "I might be misunderstanding, so correct me if this is not the issue."

Blocked:

- claiming the buyer is anxious, vulnerable, or emotionally persuadable
- using emotion estimates to intensify pressure
- treating voice features as biometric emotion recognition
- continuing persuasion after refusal, do-not-call, or high-risk escalation triggers

## Sales Strategy Rules

The runtime strategy selector should choose one primary move per turn:

- clarify the buyer's actual concern
- map the concern to a value dimension
- answer from approved campaign facts
- repair trust with limits, evidence, or human handoff
- reduce cognitive load with one decision at a time
- preserve autonomy with a real choice
- summarize for a decision-maker
- ask for a small consented next step
- bridge while checking approved information
- end or transfer when the call-control policy requires it

The brain should avoid stacking many persuasion tactics into one turn. Dense tactics can sound fake, pushy, or slow.

## RAG Boundary

RAG is useful, but it must stay gated.

Current runtime rule:

- retrieval disabled by default
- RAG-017 is the runtime registry owner
- RAG-018 is the guarded retrieval evaluation owner
- protected text, refusal, do-not-call, compliance, and human handoff contexts override retrieval

RAG-020 and RAG-021 are advisory-only in BRAIN-001. They strengthen the strategy library, but they are not automatically in the runtime brain.

runtime use requires a separate RAG-017 registry rebuild and RAG-018 guarded-retrieval evaluation.

## RAG-020 And RAG-021 Use

RAG-020 adds sales persuasion and emotion-understanding guidance:

- insight-led selling before pitching
- behavior-change diagnosis
- autonomy-supportive persuasion
- buyer confidence and clear tradeoffs
- emotion-inference limits
- affect-labeling repair
- AI risk and deception boundaries

RAG-021 adds buyer trust and conversation-repair guidance:

- buyer value mapping
- trust repair across ability, benevolence, and integrity concerns
- reactance-aware choice framing
- cognitive-load reduction
- plain-language summaries
- conversation repair
- consented next-step planning
- AI transparency and human handoff

These rules can inform future runtime logic only after promotion tests prove they improve behavior without increasing pressure, unsupported claims, latency, or privacy risk.

## Voice And Personality Boundary

Voice is part of the brain only as delivery intent and profile selection, not as sales reasoning.

Current voice evidence:

- `old_plain_guarded` is an accepted English direction for a more natural, laid-back salesperson feel.
- `new_shaped_runtime` is an accepted English direction for a more serious, lower-energy feel.
- The voice-personality selector remains blocked until the RESP-007 German pacing-stability follow-up is heard and accepted.

The brain should not pick a universal voice personality for all campaigns. Future selection should consider campaign language, buyer context, risk, provider behavior, and human listening evidence.

## Memory And Data Boundary

The project brain may use:

- project-owned rules
- campaign-approved facts
- synthetic simulation cases
- reviewed public-source paraphrases
- reviewed aggregate private-pattern notes after a separate approval gate

The project brain must not store or retrieve:

- No raw private audio
- No raw private transcripts
- customer identifiers
- unredacted call-center exports
- copied source excerpts
- API keys or provider secrets
- hidden prompt or model behavior that cannot be inspected
- private evidence inside public generated artifacts

Private learning belongs behind `data/private/` boundaries and explicit review gates. Runtime customer memory needs a later product-data design before it becomes part of the live brain.

## Response Planner

The response planner should produce a compact decision packet before text reaches voice:

```text
buyer_state:
  emotional_signal
  confidence
  objection
  interest
strategy:
  selected_move
  reason
  allowed_next_action
safety:
  blocked_actions
  escalation_needed
response:
  final_response
  protected_text
  retrieval_used
voice:
  language
  delivery_profile
  pacing_bounds
```

The final spoken answer must stay grounded in campaign facts and protected text. Voice layers may shape delivery only inside their existing boundaries.

## What Does Not Belong In The Brain

- a giant prompt that mixes every source, tactic, and voice note
- automatic default retrieval for every turn
- source excerpts copied into runtime memory
- private audio or raw transcripts
- voice cloning assumptions
- unvalidated emotion classifiers
- a multi-agent chain blocking every reply
- campaign-specific claims hard-coded into the reusable core
- pressure tactics that treat objection handling as winning rather than understanding

## Promotion Path

Future brain changes should move through narrow checkpoints:

1. `BRAIN-002`: define a project-local runtime state schema for buyer state, strategy, safety, call control, retrieval status, voice, response, and evidence logging.
2. `RAG-017/RAG-018`: optionally rebuild and evaluate runtime retrieval with selected RAG-020/RAG-021 rules.
3. `RESP/VOICE`: define a voice-personality selector only after the RESP-007 German pacing-stability follow-up is accepted.
4. `PROD`: test complete call behavior through fixed scripted simulations before any launch claim.
5. Thesis tracking: update `METHODOLOGY_LOG.md`, `DECISION_LOG.md`, and reference docs whenever source-backed or runtime behavior changes.

`BRAIN-002` is now implemented as a schema checkpoint in `docs/brain/BRAIN_002_RUNTIME_STATE_SCHEMA.md`. It keeps retrieval disabled by default, treats voice as delivery metadata, and makes non-sale correctness a first-class output field before the full-call gauntlet.

## BRAIN-001 Decision

BRAIN-001 keeps the always-on brain small:

- reusable core
- campaign profile
- short-term call state
- guarded strategy selector
- optional retrieval only when explicitly enabled
- voice delivery profile after response safety
- post-call learning outside the live path

This makes the project brain useful for real sales calls without turning it into uncontrolled memory, slow agent orchestration, or unsupported emotional persuasion.
