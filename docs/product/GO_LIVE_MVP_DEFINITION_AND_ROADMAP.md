# Go-Live MVP Definition And Roadmap

Status: planning artifact. This document does not open `PROD-102` and does not promote the product to real customer use.

## Purpose

Define what `go live` means for this project, what the MVP is, and how future work should move from the current `LIVE-DEMO-001` front end into the reusable runtime without creating demo-only product behavior.

The core rule is:

```text
demo-first acceptance, core-runtime implementation
```

The demo is the first customer-heard surface. It is not the product architecture by itself.

## What Go Live Means

`Go live` is not one state. It has levels.

### Level 0: Offline Runtime Evidence

Meaning:

- deterministic runtime, scenario, and validator evidence passes
- no real microphone, no provider calls, no real customer data
- generated evidence stays under `research/experiments/generated/`

Current status: mostly strong through `PROD-101`, but not enough for live user experience.

### Level 1: Supervised Local Live Demo

Meaning:

- Tarik can talk to the repo-owned sales agent locally
- microphone input goes through the current demo front end
- agent logic stays in this repository
- voice output can use ElevenLabs TTS only after explicit opt-in
- turn packets and generated audio stay in ignored private local paths

Current artifact: `LIVE-DEMO-001`.

This is the active development front end until the MVP is stable.

### Level 2: Internal Real-Person Live Test

Meaning:

- one approved human tester talks to the agent
- test uses a fictional or explicitly approved campaign profile
- no real customer lead list is used
- no payment, contract, legal advice, regulated product advice, or production outreach
- consent, provider, transcript, and retention boundaries are recorded before the run

This is the first point where external audio privacy and provider retention become serious review gates.

### Level 3: Limited Pilot Live

Meaning:

- the system handles a bounded real campaign with explicit approval
- calls are supervised or reviewable
- lead data, transcript retention, consent, provider agreements, and fallback/handoff are approved
- the agent cannot collect payment, sign contracts, make unsupported claims, or operate outside the approved campaign profile

This is the first commercially meaningful `live` level.

### Level 4: Production Live

Meaning:

- real customer traffic is allowed
- observability, incident rollback, consent, retention, provider costs, audit logs, handoff, and campaign governance are operational
- production deployment, real telephony, and customer data handling are approved

This project is not at Level 4.

## MVP Definition

The MVP is not a generic autonomous seller. The MVP is:

```text
a supervised voice sales agent that can run one bounded, high-fidelity campaign conversation end to end,
using the repo-owned sales brain, transport-neutral voice turn state, approved campaign facts,
safe objection handling, voice output, private local evidence, and clear handoff boundaries.
```

The first MVP campaign should be the fictional `Northstar Workflow Labs` / `RouteSignal CRM` campaign until a real company profile is explicitly approved.

## MVP Must Include

- A high-fidelity `SalesCampaign` profile with approved facts, prices, value points, qualification path, objections, escalation triggers, forbidden claims, and source provenance.
- A transport-neutral voice turn-state contract using `voice_turn_state`, not browser-specific state names.
- A speech input layer that can decide when customer speech is accepted, rejected, interrupted, or incomplete.
- A turn controller that defines when the agent listens, thinks, speaks, waits, retries, or ends.
- A reusable runtime session-state layer for continuity, topic focus, duplicate-answer prevention, and anti-loop behavior.
- Runtime-owned product-answer logic so product knowledge does not live only in the demo wrapper.
- Voice output through a provider boundary where ElevenLabs or another provider receives only approved final text.
- A demo front end that exercises the same runtime path the MVP will use.
- Local private evidence logs for transcript, ASR quality gate, runtime decision, final response, voice provider boundary, and latency.
- A validator that proves the demo path and the runtime path agree on the same fixed cases.

## MVP Must Not Include

- Real customer outreach.
- Real payment collection.
- Contract signing.
- Legal, medical, insurance, or regulated advice.
- Unsupported ROI, conversion, security, integration, or compliance claims.
- Provider-owned business logic.
- Durable provider agents as the product brain.
- Voice cloning.
- Raw customer audio upload without a separate consent and retention review.
- Production telephony deployment.
- `PROD-102` or later checkpoint work unless Tarik explicitly opens it.

## Architecture Target

```text
audio input adapter
  -> speech endpointing and ASR quality gate
  -> voice_turn_state controller
  -> runtime session state
  -> SalesCampaign profile and source boundary
  -> guarded sales-agent core
  -> output contract and call-control check
  -> voice delivery profile
  -> TTS or speech-to-speech provider adapter
  -> evidence log and review gate
```

The demo is one adapter on the left and one review surface on the right.

Browser, telephony, WebRTC, and provider realtime APIs should all feed the same middle contracts.

## Current Integration Debt

Some behavior was introduced through `LIVE-DEMO-001` because the live experience failed before the core validators exposed the issue.

That was acceptable for recovery, but it is not the final architecture.

Behavior that should move from demo-local code into runtime-owned modules before MVP:

- session continuity and resolved focus handling
- callback scheduling boundaries for busy/no-time buyers
- anti-loop and duplicate-response repair
- fictional campaign product-answer routing
- ASR quality gate contract
- voice turn-state packet shape
- demo/runtime agreement validator

Behavior that can stay demo-local:

- browser UI
- browser SpeechRecognition wiring
- manual send button
- local consent checkbox
- HTML rendering
- local audio playback
- ignored private demo packet storage

## LIVE-DEMO-002 Preservation Contract

`LIVE-DEMO-002` should preserve the currently corrected `LIVE-DEMO-001` behavior while extracting MVP-relevant behavior into runtime-owned modules.

The goal is not to restart from old failures. The goal is to protect the fixed live-demo behavior and move reusable behavior into architecture that can support browser, telephony, WebRTC, and provider-realtime adapters.

When moving behavior from demo-local code into runtime-owned modules, user-heard behavior should remain equivalent or intentionally improved.

Any intentional behavior change must be named in the plan and covered by validator expectations before implementation. If a response changes, the plan must say whether the change is:

- `behavior_preserved`: wording or structure may move, but user-heard behavior should be equivalent
- `intentional_improvement`: user-heard behavior changes to fix a named weakness
- `non_user_visible_extraction`: only module ownership, packet shape, or internal routing changes

Current named `intentional_improvement` items:

- `sales_opening_permission_check`: first greetings should open like a sales call with a permission/time check, not a topic menu.
- `proactive_price_guidance_after_acknowledgement`: weak acknowledgements after a price answer should advance guided selling instead of replaying the same pricing sentence.
- `multi_topic_non_repeating_progression`: generic follow-ups across price, fit, timing, and feature/detail topics should progress without replaying responses or reopening focus menus.
- `callback_scheduling_boundary`: no-time buyer turns should ask for a callback time, and supplied callback times should confirm scheduling with `schedule-and-end` instead of reopening product-topic menus.

Do not create a large failure registry unless current unfixed failures require it. At this stage, the right scope is compact regression coverage for already-fixed `LIVE-DEMO-001` behaviors:

- repetition prevention
- follow-up continuity
- voice delivery propagation
- product-answer routing
- ASR quality handling
- callback scheduling boundary

The extraction should only cover MVP-relevant behavior. It should not become a general cleanup of all historical checkpoint behavior, and it should not be a documentation-only task.

## Current Behavior Baseline

Before runtime extraction starts, record the current passing `LIVE-DEMO-001` behavior as the baseline.

The baseline should include:

- `scripts/validate_live_demo_001_agent_voice_call.py` pass status
- supported campaign questions, including product explanation, pricing, plan differences, manual-tracking objection, small-team fit, unnecessary-handoff challenge, integration boundary, and security boundary
- supported continuity behavior, including short topic answers, explicit topic selections, resolved-focus persistence, topic shifts, continuation phrases, and no-time callback scheduling
- supported anti-loop behavior, including one-menu-per-session and duplicate non-terminal response repair
- supported voice delivery behavior, including RESP-002/RESP-003 propagation, ElevenLabs dry-run and forced-missing-key boundaries, provider-agent false, voice-cloning false, and no runtime behavior change
- supported ASR quality behavior, including obvious fragment repair, low-confidence rejection below `0.45`, clear-confidence acceptance, and `voice_turn_state` metadata
- current private evidence packet shape under ignored `data/private/live-demo-001/`, including transcript, ASR quality gate, demo session continuity, turn-taking metadata, guarded runtime packet, summary, provider boundary, and latency

Extraction is successful only if this baseline still passes after behavior moves into runtime-owned modules, unless an intentional improvement was named upfront and validated.

## Roadmap

### Phase 1: Stabilize The Demo Acceptance Contract

Goal: make `LIVE-DEMO-001` the required acceptance front end for every live-call behavior change.

Acceptance:

- `scripts/validate_live_demo_001_agent_voice_call.py` covers product knowledge, price, fit, follow-up continuity, anti-loop, ASR quality, voice turn state, provider boundary, and no `PROD-102`.
- Every new live behavior starts as a failing demo validator case.
- No direct live provider call is required for validation.

Primary files:

- `scripts/run_live_demo_001_agent_voice_call.py`
- `scripts/validate_live_demo_001_agent_voice_call.py`
- `docs/product/LIVE_DEMO_001_AGENT_VOICE_CALL.md`
- `research/experiments/cases/live-demo-001-fictional-b2b-sales-campaign.json`

### Phase 2: Extract Reusable Runtime Contracts

Goal: preserve the corrected `LIVE-DEMO-001` behavior while moving MVP-relevant behavior out of demo-only code.

Acceptance:

- a baseline artifact records the current passing `LIVE-DEMO-001` behavior before extraction
- `voice_turn_state` has a runtime contract module or documented schema under `runtime/contracts/`.
- ASR quality gate has a runtime-facing contract that accepts provider/browser metadata without depending on the browser.
- Session continuity, anti-loop, and duplicate-response behavior are callable from runtime-owned code.
- Product-answer routing for the `RouteSignal CRM` campaign is runtime-owned or campaign-profile-owned rather than hard-coded in demo-local branches.
- Demo validator proves the demo uses those runtime contracts.
- The compact regression set covers repetition prevention, follow-up continuity, voice delivery propagation, product-answer routing, ASR quality handling, and callback scheduling boundary handling.
- Any intentional user-heard behavior change is named as an `intentional_improvement` and asserted by the validator.
- No broad failure registry is created unless a current unfixed failure requires it.

Candidate files:

- create a baseline artifact under `research/experiments/generated/LIVE-DEMO-002/`
- create `runtime/contracts/voice_turn_state_contract.py`
- create `runtime/speech/asr_quality_gate.py`
- create `runtime/core/live_voice_session_policy.py`
- create or update runtime-owned campaign product-answer helpers
- update `runtime/runtime_manifest.json`
- keep `scripts/run_live_demo_001_agent_voice_call.py` as orchestration and UI glue

### Phase 3: Promote The Fictional Campaign Into A Proper Runtime Profile

Goal: make `RouteSignal CRM` a first-class high-fidelity campaign profile, not only a demo overlay.

Acceptance:

- campaign profile passes `runtime/contracts/campaign_profile_contract.py`
- approved facts, forbidden claims, handoff triggers, pricing, source provenance, and product-answer rules are structured
- product-answer behavior reads from campaign/profile fields rather than hard-coded demo branches
- source reuse remains `inspiration only`

Candidate files:

- create or update a profile under `runtime/campaigns/examples/`
- keep the current JSON case file as test input or fixture
- update validators to reject missing product facts before demo use

### Phase 4: Define The Real Speech Stack

Goal: replace weak browser-only speech handling with an adapter-ready speech layer.

Acceptance:

- speech input adapter interface supports browser ASR, local/provider ASR, telephony, WebRTC, and provider realtime APIs
- voice activity / endpointing policy is separate from transcript text
- barge-in and interruption behavior is explicitly defined
- audio retention and provider upload boundaries are documented before any live run

Decision still open:

- keep ElevenLabs TTS plus separate ASR
- evaluate UltraVox hosted API as a provider adapter
- test a first-party ASR/VAD stack before telephony

No provider path should become the product brain.

### Phase 5: Internal Real-Person Live Test Gate

Goal: move from Tarik-only local demo to one approved internal human test.

Acceptance:

- one campaign profile is selected
- tester consent is recorded
- provider input/output data is documented
- no real customer data is used
- transcript/audio retention path is approved
- rollback is simple: stop local server and disable provider live flag
- pass/fail rubric is fixed before the call

Required evidence:

- local dry-run validator pass
- live provider dry-run or forced-missing-key fallback pass
- one approved live provider run
- private packet review after the call

### Phase 6: Limited Pilot Readiness

Goal: decide whether a real campaign pilot is justified.

Acceptance:

- stable demo and runtime agreement on fixed scenarios
- campaign owner approves facts and claims
- data/privacy/retention review is complete
- telephony provider boundary is reviewed
- human handoff path is tested
- incident stop path is tested
- no unsupported claims across fixed pilot cases

This phase requires explicit approval before any real customer call.

## Go-Live Readiness Gates

### Product Gate

- one campaign only
- campaign facts approved
- buyer outcome objective defined
- prohibited outcomes defined
- fallback/handoff defined

### Runtime Gate

- runtime manifest includes every behavior-affecting file
- demo behavior and runtime behavior are not divergent
- no demo-only sales logic is required for MVP behavior
- all validators pass through current allowed checkpoint boundary

### Voice Gate

- `voice_turn_state` is transport-neutral
- audio input does not run while agent output is active
- ASR confidence or quality is recorded
- low-confidence input does not enter sales logic
- provider text/audio boundaries are explicit

### Data Gate

- no secrets in tracked files
- no raw customer audio without approval
- no private transcripts in tracked files
- retention location is documented
- deletion path is documented

### Provider Gate

- live provider use is opt-in
- provider agent is not the product brain
- no durable provider agent is created unless separately approved
- cost, timeout, cleanup, retention, and logging behavior are known

### Sales Safety Gate

- no unsupported product claims
- no pressure after disinterest
- no payment or contract collection
- no legal/medical/regulated advice
- no closing without confirmed fit and approved campaign boundary

## Recommended Next Work

The next work should not be more provider experimentation.

The next work should be:

```text
LIVE-DEMO-002 / runtime extraction plan:
record the current passing LIVE-DEMO-001 baseline, then move reusable session continuity,
ASR quality, voice_turn_state, and campaign product-answer behavior out of demo-local code
and into runtime-owned modules while preserving the baseline.
```

This directly addresses the failure pattern: fixes worked in the demo, but not all of them were properly introduced into the runtime logic.

The implementation bias should be code-first with compact regression evidence:

- record the current baseline before extraction
- write focused failing tests for runtime-owned contracts
- move one behavior family at a time
- keep the demo front end wired to the new runtime modules
- rerun the baseline validator after each extraction slice
- avoid a broad failure registry unless a current unfixed failure appears

## Approval Needed Before Execution

Before implementing the next phase, Tarik should approve:

- whether to create `LIVE-DEMO-002` as the next demo-first acceptance checkpoint
- whether runtime extraction can touch `runtime/contracts/`, `runtime/core/`, `runtime/speech/`, `runtime/campaigns/`, and `runtime/runtime_manifest.json`
- whether `RouteSignal CRM` remains the canonical MVP sandbox campaign
- whether provider work stays frozen until the runtime extraction is complete
