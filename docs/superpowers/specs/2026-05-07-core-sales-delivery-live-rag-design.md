# Core Sales Delivery And Live RAG Design

Date: 2026-05-07

## Purpose

Give the sales agent stronger baseline sales and voice behavior before live calls while still using the RAG registry for turn-specific guidance during a conversation.

The design decision is not "hard-code everything" versus "retrieve everything." The chosen architecture is:

```text
teach now + retrieve live + learn later
```

## Goals

- Distill the current reviewed RAG into a compact always-on core playbook.
- Use live RAG retrieval during calls for contextual tactical guidance.
- Keep live retrieval fast enough for a real-time call path.
- Improve speech delivery now, especially pacing, rhythm, pauses, fillers, confidence, empathy, and emotional tone.
- Learn from successful calls, failed calls, and individual successful or failed moments inside calls.
- Preserve compliance and safety boundaries around do-not-call, refusal, escalation, disclosure, truthful claims, private data, and protected text.

## Non-Goals

- Do not hard-code the full RAG registry into the prompt or runtime core.
- Do not let raw customer calls or private transcripts enter runtime RAG automatically.
- Do not use an external vector database, embedding provider, or hosted memory service for this checkpoint.
- Do not let retrieval change protected campaign, disclosure, refusal, handoff, appointment, or do-not-call text.
- Do not let generic RAG advice override campaign facts, product facts, pricing facts, discount terms, or compliance requirements.
- Do not replace the existing voice pipeline. The new delivery pack should feed the current RESP/VOICE layers.

## Architecture

### 1. Safety And Compliance Core

Always on and non-negotiable.

Rules:

- Obey do-not-call, opt-out, refusal, escalation, protected script, and required disclosure handling.
- Do not hide material facts.
- Do not invent product claims, deadlines, scarcity, discounts, outcomes, guarantees, or social proof.
- Do not exploit vulnerable customers.
- Do not infer protected traits.
- Do not claim certainty about hidden internal emotional state.

Persuasion boundary:

```text
Use ethical persuasion. Strong persuasion is allowed when it is truthful, campaign-supported, reversible, and respectful. Do not deceive, coerce, exploit, or invent pressure.
```

Urgency and scarcity:

- Real campaign urgency is allowed.
- Real limited availability is allowed.
- Fake urgency and invented scarcity are not allowed.
- Discount or deadline language must come from campaign facts.

### 2. Core Sales Playbook

Always on, compact, and distilled from reviewed RAG. This is the part the agent should know before live calls.

Includes:

- cold-call openers
- permission-based openers
- pattern interrupts
- call control
- keeping prospects on the phone
- "not interested" handling
- price objections
- timing objections
- trust objections
- competitor objections
- "send me info"
- "we already have someone"
- "I need to think about it"
- "I need to ask my partner/boss"
- soft closing
- trial closing
- next-step closing
- appointment setting
- buying-signal recognition

The playbook should be small enough to load every turn. It should contain reusable rules and examples, not long source notes.

### 3. Core Delivery Intelligence Pack

Always on and used now to improve the voice path.

Includes:

- empathy and active listening
- mirroring and labeling expressed concerns
- observable-empathy phrases such as "I understand why that would be frustrating"
- matching customer energy without overacting
- calming annoyed or skeptical customers
- tone, pacing, pauses, intonation, articulation, confidence
- natural fillers and human-like hesitation where safe
- reducing robotic speech
- phrase-level emphasis and low-pressure wording

Boundary:

```text
Use observable empathy. Reflect expressed or observable emotion without pretending to know hidden internal state.
```

This pack should feed RESP-002 and existing VOICE layers such as speech realism, interaction prosody, pacing calibration, connected speech, emotion smoothing, semantic emphasis, and low-pressure focus. It may adjust provider-facing TTS text and metadata where those layers already allow it, but `final_response` remains policy-owned.

### 4. Live Tactical RAG

Opt-in retrieval during the call. This uses the existing RAG-017 registry:

```text
research/experiments/generated/RAG-017-runtime-knowledge-registry/result.json
```

The live turn flow should become:

```text
customer turn
-> realtime state classification
-> retrieval blocker check
-> campaign fact grounding
-> retrieve top 2-4 relevant advisory rules that pass relevance and source gates
-> compose candidate response using core playbook + allowed RAG hints
-> guardrail validation
-> final response
-> voice delivery pack
```

RAG should be used for:

- uncommon or nuanced objection variants
- campaign-specific handling
- German wording variants
- advanced consultative-selling questions
- advanced emotional-intelligence guidance
- contextual sales psychology
- tactical phrasing alternatives

Retrieval must remain advisory-only. If retrieval is blocked, the agent should continue with the core playbook and policy response path.

Campaign facts must outrank RAG:

- campaign facts
- product facts
- price and discount terms
- compliance and disclosure rules
- client-provided scripts
- allowed and forbidden claims

If a retrieved RAG hint conflicts with campaign facts, the hint is ignored and the response follows the campaign facts.

Live retrieval latency budget:

```text
target: under 150 ms
acceptable: under 300 ms
fallback: skip retrieval and use core playbook, or use a short stall-for-time bridge only when the call state allows it
```

Fallback behavior:

- If retrieval exceeds the budget before composition, use the core playbook.
- If the context is blocked, skip retrieval influence.
- If no relevant hint passes the gate, use the core playbook.
- If the customer asks a protected or campaign-fact-sensitive question, prefer campaign grounding over RAG.

Relevance and source gate:

- Retrieve at most 2-4 candidate hints.
- Use a hint only if its relevance score passes a configured threshold.
- Use a hint only if its source type/lane is allowed for the active campaign and current call state.
- Prefer higher-confidence, source-traced, campaign-compatible hints over broad generic sales advice.
- Record rejected hint IDs and rejection reasons for debugging, but do not expose raw source excerpts.

### 5. Batch Pattern Learning Loop

Learning must happen from both successful and failed calls, but individual calls must not become runtime rules by themselves. A single call can create a redacted note or hypothesis. Runtime RAG promotion requires repeated evidence across a reviewed batch.

The learning loop is pattern-based:

```text
many calls
-> redacted local call notes
-> batch analysis after a threshold
-> repeated pattern candidates
-> human review
-> project-owned advisory rule
-> RAG registry rebuild
-> guarded runtime retrieval
```

Required initial batch threshold:

```text
200 redacted call notes per campaign or comparable call type
```

After 200 eligible notes, the system should notify Tarik and stop short of automatic promotion. Tarik decides whether to run pattern mining, change the threshold, split by campaign/language, or continue collecting.

The threshold can be lower only for safety/compliance failures that require immediate blocking rules, and those should still be reviewed before runtime use.

Call notes should be event-level, not only call-level.

Call outcomes:

- successful
- failed
- neutral
- escalated
- do-not-call

Event outcomes:

- successful opener
- failed opener
- successful repair
- failed repair
- successful objection handling
- failed objection handling
- successful close
- failed close
- useful discovery question
- risky moment inside otherwise successful call

Failed calls should produce:

- "do not do this" rules
- failure patterns
- risk constraints
- failed repair examples
- escalation and fallback improvements

Successful calls should produce:

- reusable phrasing patterns
- successful repair strategies
- better sequencing
- buying-signal recognition
- effective objection handling
- pacing and turn-taking patterns
- campaign-specific winning moves

Nothing from calls should enter runtime RAG automatically. The path is:

```text
call event
-> redacted local note
-> local note store
-> batch pattern mining
-> pattern candidate registry
-> human review
-> project-owned advisory rule
-> RAG registry rebuild
-> guarded runtime retrieval
```

The system should distinguish:

- **Call note:** one redacted observation from one call. Never runtime-active.
- **Hypothesis:** a possible pattern suggested by one or a few calls. Never runtime-active.
- **Pattern candidate:** an aggregated finding across a batch, with counts and counterexamples. Reviewable, but not runtime-active.
- **Accepted advisory rule:** a human-approved project-owned rule derived from aggregated evidence. Eligible for future RAG promotion.

## Data Flow

### Teach Now

Inputs:

- RAG-017 registry items
- RAG-016B voice-delivery advisory items
- RAG-019 sales communication source expansion
- existing RESP/VOICE docs and generated artifacts

Outputs:

- compact core sales playbook artifact
- compact core delivery intelligence artifact
- validators proving the packs avoid private data, raw excerpts, protected text mutation, and invented urgency/scarcity

### Retrieve Live

Inputs:

- current transcript
- realtime decision snapshot
- campaign facts
- core playbook
- RAG-017 registry

Outputs:

- retrieved advisory hint IDs
- citation trace
- retrieval status
- retrieval latency
- relevance/source-gate decisions
- campaign-fact conflict decisions
- candidate response influenced by allowed hints
- final response after guardrail validation

### Learn Later

Inputs:

- redacted call notes
- outcome labels
- event labels
- human review decisions

Outputs:

- private/local call note store
- batch pattern mining output
- pattern candidate registry
- accepted project-owned advisory rules derived from repeated evidence
- rejected or quarantined unsafe notes
- future RAG registry update

## Implementation Phases

### Phase 1: Distilled Core Packs

Create project-local artifacts for:

- core sales playbook
- core delivery intelligence pack
- ethical persuasion boundary

Add validators for:

- no raw source excerpts
- no private data paths
- no fake urgency/scarcity permissions
- no hidden-emotion certainty claims
- protected text remains policy-owned

### Phase 2: Retrieval Before Composition

Change guarded response generation so retrieval happens before candidate composition when enabled.

The composer should receive:

- core playbook rules
- delivery guidance summary
- retrieved advisory hints
- retrieval trace metadata

The output packet should distinguish:

- retrieval attempted
- retrieval blocked
- retrieval matched
- retrieval actually influenced wording
- retrieval only influenced delivery metadata

### Phase 3: Voice Delivery Integration

Feed the core delivery intelligence pack into the current RESP-002 and VOICE stack.

Rules:

- provider-facing speech can be improved where existing voice layers allow it
- protected text remains unchanged
- final response remains unchanged after RESP-001
- emotional delivery must use observable empathy, not hidden-state certainty

### Phase 4: Batch Pattern Learning

Add a reviewed batch-learning workflow for successful and failed call events.

Minimum call note fields:

- call_outcome
- event_type
- event_outcome
- campaign_id
- language
- sanitized_context
- proposed_rule
- source_label
- reviewer_status
- do_not_use_when
- safety_flags

Minimum pattern candidate fields:

- pattern_id
- batch_id
- source_note_count
- supporting_event_count
- contradicting_event_count
- campaign_scope
- language_scope
- pattern_type
- proposed_rule
- evidence_summary
- counterexample_summary
- confidence_level
- minimum_batch_size_met
- reviewer_status
- do_not_use_when
- safety_flags

Accepted pattern candidates can later be promoted into a RAG checkpoint. Individual call notes and hypotheses stay out of runtime retrieval.

When the 200-note threshold is reached, the first system action is a notification/checkpoint, not automatic pattern mining or promotion.

### Phase 5: Experiment Harness

Compare:

- baseline without live RAG influence
- core playbook only
- live RAG retrieval
- hybrid core playbook plus live RAG

Metrics:

- call continuation
- objection handling quality
- appointment setting
- buying-signal detection
- safety/compliance pass rate
- protected text preservation
- voice naturalness
- latency
- retrieval under 150 ms target
- retrieval under 300 ms acceptable ceiling
- retrieval relevance
- campaign-fact conflict rate

## Safety Rules

- Persuasion is allowed; deception is not.
- Real urgency is allowed; fake urgency is not.
- Real scarcity is allowed; invented scarcity is not.
- Observable empathy is allowed; hidden-emotion certainty claims are not.
- Pressure is allowed only when truthful, bounded, respectful, reversible, and campaign-supported.
- Do-not-call, refusal, escalation, required disclosure, and protected campaign text override sales tactics and retrieval.
- Campaign facts override generic RAG advice.
- Private call learning requires redaction, local storage, review, and explicit promotion before runtime use.

## Verification

Required checks after implementation:

```powershell
python scripts\validate_resp_001_guarded_response_generation.py
python scripts\validate_resp_002_runtime_voice_delivery.py
python scripts\validate_rag_017_runtime_knowledge_registry.py
python scripts\validate_rag_018_guarded_runtime_retrieval.py
python scripts\validate_private_data_boundary.py
python scripts\check_thesis_update_gate.py
python scripts\check_project_drift.py
```

Additional new validators should cover:

- core playbook scope
- core delivery intelligence scope
- retrieval-before-composition behavior
- retrieval latency budget and fallback behavior
- retrieval relevance threshold behavior
- source-type and campaign-scope gating
- campaign fact grounding before RAG influence
- batch pattern learning safety
- successful-call and failed-call event labels
- 200-note evidence threshold before pattern-mining notification
- fake urgency/scarcity rejection
- observable empathy wording boundaries

## Open Decisions

- Exact file names for the core playbook and delivery pack.
- Whether Phase 1 should create JSON artifacts only, Markdown docs only, or both.
- Whether live retrieval should influence only response wording first, or wording plus delivery metadata in the first implementation pass.
- Whether the first batch should be public-source examples only or include reviewed redacted private-call pattern notes from the existing private-call learning scaffold.
- The exact first relevance threshold for deterministic keyword retrieval before adding any stronger local scorer.
- Whether stall-for-time fallback should be enabled in v1 or whether v1 should always skip retrieval when the budget is exceeded.
