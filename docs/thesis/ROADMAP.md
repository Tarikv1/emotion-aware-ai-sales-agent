# Roadmap

This roadmap is the working steering document for the thesis and product project.
It should be updated whenever the project direction changes, a phase completes, or a meaningful new constraint appears.

## Roadmap Operating Rules

This roadmap is also the project checkpoint board. It should answer three questions at any moment:

- what phase we are in now
- what checkpoint is active next
- what earlier deferred ideas have become ready to implement

Use these rules during future work:

- Every meaningful experiment, runtime feature, product design step, or thesis documentation step should appear in the roadmap before or when it becomes active.
- When a checkpoint is completed, mark it as done, record the next checkpoint, and update `METHODOLOGY_LOG.md` if the work teaches something thesis-relevant.
- If Tarik changes the product direction, update the upcoming checkpoints instead of forcing the old plan.
- If Codex recommends deferring an idea because it is too early, add it to the Deferred Implementation Queue with an unlock condition.
- When starting a new phase or checkpoint, scan the Deferred Implementation Queue and explicitly surface any idea whose unlock condition is now true.
- Keep the roadmap flexible: the current phase can change as product discovery changes, but completed checkpoints should remain visible as evidence of the path taken.

Status convention:

- `[x]` means completed.
- `[ ]` means planned, current, or deferred; the wording of the item should say which one.
- `Current` means this should be worked on before opening a new branch of effort.
- `Next` means it should become current after the current checkpoint closes, unless Tarik changes direction.

## Checkpoint Board

Active phase: voice/runtime quality and thesis evidence preservation.

Current checkpoint:

- [ ] Current: design `VOICE-020` for emotional delivery, less rigid openings, controlled randomness, bundled expressive gestures, contractions/fillers, and provider-aware ElevenLabs voice settings while preserving campaign-safe protected text.

Next checkpoints:

- [ ] Next: implement and validate `VOICE-020` as an offline/live-capable voice-emotion tuning checkpoint.
- [ ] Next: connect `RESP-003` audio output to the local demo/playback flow after dry-run, missing-key, timeout, and asset-log gates remain stable.
- [ ] Next: expand `RESP-002` from single-response segment wrapping to multi-segment runtime packets when campaign questions or disclosures are spoken in the same turn.
- [ ] Next: resume the product-learning track by strengthening the reusable sales core against universal objections before broad industry expansion.
- [ ] Next: continue dataset-grounded thesis expansion once the current voice/runtime checkpoint is stable.

Recently completed checkpoints:

- [x] `VOICE-019` dry-run harness comparing `VOICE-017`-style prosody against `VOICE-018` sales-tuned input before live provider calls.
- [x] `VOICE-019` first live ElevenLabs limited run with English/German prosody-vs-sales-tuned audio; owner preferred sales-tuned in both languages, while noting rigid openings and insufficient emotional expressiveness.
- [x] `VOICE-018` offline professional-sales tuning after listening feedback found `RESP-003` clear but too slow and still obviously AI-generated.
- [x] First bilingual `RESP-003` ElevenLabs live TTS result for German and English campaign responses.
- [x] First bilingual `RESP-003` human listening review showing the next voice quality target: faster, less robotic, better pitch/emotion, while preserving clarity.
- [x] Project-local self-containment, voice provider run-boundary, generated-audio asset-log, drift guard, and relevant-reader policies.

## Deferred Implementation Queue

Use this section whenever an idea is good but too early to build now.
When a roadmap phase reaches an idea's unlock condition, Codex should explicitly surface it again and say: "This earlier deferred idea is now ready to implement."

| Idea | Why Deferred | Unlock Condition | Relevant Phase | Status |
|---|---|---|---|---|
| Full-duplex real-time interruption handling | Too early before the stable voice loop and interruption policy are integrated into a live audio path | Live ASR/TTS loop exists, latency is measured, and barge-in behavior can be tested safely | Voice/runtime | Deferred |
| Live-call sub-agent orchestration | Sub-agents should not block the 1-2 second customer-facing response path until the fast core is stable | Fast core, bridge responses, and background task boundaries are measured in runtime tests | Product runtime | Deferred |
| Real customer audio ASR testing | Requires consent, privacy review, retention review, and client approval | Voice consent checklist, provider retention review, and synthetic-audio path are already stable | Voice/provider | Deferred |
| Broad campaign library expansion | The core should first handle difficult universal sales situations before breadth becomes useful evidence | Difficulty-first sales gauntlet and reusable objection-handling checks are stable | Product learning | Deferred |
| Third-language runtime support | German and English must be strong before proving language-pack extensibility | German/English campaign routing, voice quality, and validator coverage are stable | Bilingual/multilingual runtime | Deferred |
| Detailed voice ablation study | Useful for thesis evidence, but premature before the live voice quality target is good enough to compare | Provider voice quality is acceptable enough that ablation differences are meaningful | Thesis evaluation | Deferred |
| Cartesia-vs-ElevenLabs repeat comparison | Provider comparison should wait until the ElevenLabs live path and rubric are stable | `VOICE-019` ElevenLabs review is recorded and the same cases can be replayed fairly | Voice/provider | Deferred |
| Sales-expert feedback dashboard | Too much interface work before the agent behavior and review rubrics stabilize | Sales-expert rating fields and product simulation logs are stable | Product MVP | Deferred |

## Current Direction

Build and evaluate an emotion-aware AI sales agent that adapts persuasion strategy based on customer state.

The project starts with a public-data-first text baseline, then moves toward multimodal speech and voice-feature adaptation.

This is also a real product effort with a potential paying client. The first product track should turn thesis evidence into an autonomous lead-qualification and appointment-setting agent with fallback and escalation guardrails.

The product track should support both B2B and B2C sales contexts. The first product simulation is B2B-leaning, but later case sets should include direct-to-consumer customer conversations.

The first concrete B2C client example is a German call center selling consumer insurance products, including dental insurance and cancer-related or serious-illness insurance. This should inform the next product simulation expansion, but it is only one example of the broader campaign-driven product model.

The product simulation runner now supports campaign wrappers, so one reusable core can be exercised across multiple client/product profiles while preserving per-campaign guardrails. The mixed case sets are examples of that breadth, not the boundary of the product.

The next product-learning priority is difficulty-first: strengthen the reusable core against universal sales objections and edge cases before expanding aggressively into more industries.

The product runtime priority is low latency. The live call path should be a fast real-time sales-agent core with deterministic guardrails and short bridge responses when slower lookup is needed. Specialist modules or sub-agents should support background compliance, product lookup, CRM work, handoff preparation, and post-call learning rather than blocking every customer-facing reply.

The live call path also needs explicit call-control decisions. The agent should know when to continue, bridge, transfer, end, or schedule-and-end rather than treating every customer response as an invitation for another question.

The active runtime path now treats language as a campaign-level runtime property. German and English behavior should remain one product architecture: the reusable sales-agent core reads the selected `SalesCampaign`, preserves `campaign_language` and `response_language`, and the voice layer speaks the selected response language.

Runtime debugging lessons should be preserved for the thesis. When language routing, latency, interruption, or guardrail bugs are found and fixed, the issue and fix should be summarized in `METHODOLOGY_LOG.md` so the final thesis can discuss limitations and iteration honestly.

The voice-provider path now has a readiness gate before real provider integration. ASR/TTS providers must be evaluated for latency, German/English support, API-key safety, audio upload behavior, retention/privacy requirements, and fallback behavior before any live provider key or real customer audio is used.

The local no-key TTS smoke path has been tested. Windows SAPI was reachable, but the current environment had no usable local voice, so `VOICE-008` validated safe dry-run fallback rather than producing audible files. This makes concrete TTS provider research the next useful voice step.

The Emotion Aware repo should stay self-contained for client portability. If the project depends on a checklist, template, workflow, script, schema, or review gate, that material must be adapted into this repo rather than referenced from `D:\Codex\shared` or another active workspace project.

`GUARD-001` now provides a project-local drift guard for that rule. It checks for missing required guard files, conflict markers, secret-like values, unignored generated audio, and hidden dependencies on other local workspace projects. It reports and fails; it does not auto-edit files.

`CTX-001` now makes the project-local relevant reader the default first step for large documentation reads. Future project work should use `scripts/read_relevant.py` with `outline`, `section`, `find`, or `slice` before reading full large Markdown docs, thesis logs, roadmaps, command maps, generated reports, policy files, or review-gate files.

## Dual Track Principle

The thesis track and product track should reinforce each other without being confused.

Thesis track:

- prove and evaluate the core adaptation idea
- keep experiments reproducible and honest
- document methods, limitations, and evidence

Product track:

- define a usable client workflow
- build toward reliability, reviewability, and trust
- target autonomous launch behavior while validating it through supervised testing and sales-expert feedback

## Phase 1: Text And Strategy Baseline

Status: in progress

Goal:

- test whether emotion-conditioned strategy selection improves persuasive response behavior compared with a non-adaptive baseline

Completed:

- public-data-first scope selected
- `MELD` selected for compact emotion/sentiment grounding
- `Persuasion for Good` selected for persuasion strategy grounding
- compact emotion taxonomy defined
- compact persuasion taxonomy defined
- non-adaptive vs adaptive baseline specified
- prompt templates created
- evaluation rubric created
- `EXP-001` synthetic seed comparison completed
- `EXP-002` dataset-derived comparison completed
- repeatable prompt-packet runner created
- structured JSON case files created for phase-1 case sets

Current result:

- adaptive baseline was preferred in both early comparison passes
- strongest gains appeared in emotional appropriateness and strategy coherence
- skeptical or resistant cases showed the clearest benefit from adaptation

Next:

- expand from six-case experiments to a larger mixed case set
- reduce manual adaptation where possible
- decide how much of rubric scoring should remain manual versus semi-structured
- document limitations clearly before treating results as thesis evidence

## Phase 2: Dataset-Grounded Expansion

Status: planned

Goal:

- create a larger, more defensible case set grounded in public datasets

Likely work:

- extract more candidate emotional dialogue snippets from `MELD`
- extract more persuasion strategy examples from `Persuasion for Good`
- create a larger mixed case set
- compare adaptive and non-adaptive behavior across more examples
- decide whether rubric scoring remains sufficient or needs additional evaluator support

Open questions:

- how much manual domain adaptation is acceptable
- whether to include human evaluator judgments
- whether to add automated consistency checks

## Phase 3: Voice Feature Module

Status: planned

Goal:

- add interpretable voice features as a later multimodal customer-state signal

Planned module:

- pitch features
- energy features
- speech rate
- pause ratio
- silence ratio
- hesitation markers

Evaluation direction:

- compare text-only adaptation against text-plus-voice adaptation

Important boundary:

- this module adapts the concept of modular voice analytics from collaborative thesis work with Shehzeb Iftakhar
- it remains focused on sales-dialogue customer-state estimation, not music or creative-expression analysis

## Phase 4: Integrated Thesis Prototype

Status: planned

Goal:

- connect the thesis components into a small turn-based prototype that can also inform a product MVP

Likely components:

- input text or transcript
- compact emotion/state estimation
- strategy selection
- LLM response generation
- visible rationale for selected strategy
- logging and confidence checks
- fallback or escalation rule
- optional audio/TTS layer if time permits

Current integrated prototype evidence:

- active bilingual runtime checks for German and English campaign profiles
- deterministic language assertions across `PROD-005`, `VOICE-001`, `VOICE-002`, `VOICE-004`, `VOICE-005`, and `VOICE-006`
- safe interruption policy with English/German phrase packs
- response generation remains guarded behind campaign claims, forbidden claims, disclosures, and fallback rules
- ASR/TTS provider-readiness gate in `VOICE-007`, with cloud providers blocked until key/privacy/retention gates are documented
- local no-key TTS smoke test in `VOICE-008`, with validated fallback when local voices are unavailable
- segment-aware speech naturalness in `VOICE-012`, with protected campaign questions, disclosures, hang-up lines, and appointment confirmations kept exact
- segment-aware prosody naturalness in `VOICE-015`, with bounded professional-human pause, rate, emphasis, pitch, and rare stretch cues outside protected text
- provider-specific prosody rendering in `VOICE-016`, with offline Cartesia and ElevenLabs previews before live audio synthesis
- guarded live-capable A/B audio harness in `VOICE-017`, with dry-run default and plain-vs-prosody provider inputs
- first live VOICE-017 ElevenLabs A/B listening result, where the human listener strongly preferred prosody-shaped speech over plain speech in the two-case run
- offline professional-sales voice tuning in `VOICE-018`, with faster bounded pacing, emotion/pitch intent metadata, compressed pauses, and protected-text locks before the next live audio run
- live-capable prosody-vs-sales-tuned A/B harness in `VOICE-019`, with dry-run default, forced-missing-key validation, and no quality claim before human listening review
- runtime voice-delivery bridge in `RESP-002`, which applies prosody/provider preview metadata after guarded response generation while keeping `final_response` unchanged
- project self-containment policy plus local voice provider run-boundary and generated-audio asset-log docs for client-portable provider workflows
- runtime live-capable TTS bridge in `RESP-003`, with dry-run default, explicit live opt-in, generated-audio asset logging, and protected-text fallback to exact `final_response`
- first bilingual RESP-003 ElevenLabs live TTS run, with German and English audio created, no customer audio upload, no voice cloning, and sub-second provider latency in both cases
- first bilingual RESP-003 human listening review, finding clear pronunciation but voice still too slow and obviously AI-generated for real leads

Out of scope:

- production call-center deployment
- large-scale live customer testing
- full-duplex real-time interruption handling
- broad autonomous sales behavior outside the constrained target workflow

## Product MVP Track

Status: planned

Goal:

- define and build the smallest autonomous client-usable lead-qualification and appointment-setting workflow that comes out of the thesis work

Likely MVP:

- import lead/contact details
- place or simulate an outbound call
- start the first agent response within a 1-2 second target after the customer finishes speaking
- ask a small set of qualification questions
- estimate customer state
- select a strategy
- generate and execute the next response autonomously
- decide whether to continue, bridge, transfer, end, or schedule-and-end the call
- schedule a human follow-up call if the lead is interested
- log the strategy choice and rationale
- escalate or pause when confidence or safety boundaries require it
- collect sales-expert feedback during development and testing
- use bridge responses when approved lookup, scheduling, or human handoff preparation takes longer than the live turn budget

Scope note:

- B2B workflows may qualify business contacts, teams, decision-makers, and company needs
- B2C workflows may qualify individual consumers, personal needs, callback interest, and service appointment readiness

Open questions:

- whether the first product interface should be a CLI, dashboard, or lightweight web app
- what workflow the ready client actually needs first
- what data the client can legally and practically provide
- what claims can be made safely at launch
- how sales experts should label, correct, and rate agent behavior during development
- how calendar/availability integration should work for human sales-agent scheduling
- how much the first B2C flow should differ from the first B2B lead-qualification flow
- what German insurance-sales and outbound-calling constraints must be reviewed before any live deployment
- how to measure live-turn latency in the prototype without confusing model quality with voice-platform delay

## Phase 5: Thesis Write-Up Support

Status: ongoing

Goal:

- keep the written thesis easy to produce from project evidence

Ongoing actions:

- update `METHODOLOGY_LOG.md` after meaningful work
- update `DECISION_LOG.md` after important decisions
- keep experiment notes complete
- record limitations as they appear
- record implementation errors and fixes when they reveal useful thesis methodology or product constraints
- preserve collaboration, attribution, and AI-usage notes

Key writing sources:

- `PROJECT_BRIEF.md`
- `DATASETS.md`
- `DATA_READINESS.md`
- `BASELINE_SPEC.md`
- `EVALUATION_RUBRIC.md`
- `METHODOLOGY_LOG.md`
- `DECISION_LOG.md`
- experiment files under `research/experiments/`
- `docs/product/PRODUCT_BRIEF.md`

## Near-Term Next Step

Expand the case inventory beyond the first six-case sets and move toward a larger mixed evaluation pool with stronger dataset grounding.

Parallel product step:

Define the first autonomous lead-qualification and appointment-setting workflow before building a UI, so product decisions are grounded in the real client use case rather than a generic demo.

Immediate product artifact:

- qualification-question flow
- interest-state decision rules
- scheduling trigger
- escalation trigger
- turn-based product simulation case set
- mixed B2B/B2C simulation expansion
- B2C insurance-specific simulation cases
- mixed campaign wrappers that combine consumer and B2B product profiles
- sales difficulty gauntlet before broad industry-library expansion
- real-time agent architecture and latency budget
- call termination and hang-up policy
- PROD-005 realtime latency and call-control simulation
- realtime single-turn CLI prototype
- active bilingual runtime-language checks
- documented debugging trail for bilingual routing, guarded response language, and interruption campaign routing
- VOICE-007 ASR/TTS provider-readiness gate
- VOICE-008 local TTS smoke test with dry-run fallback
- VOICE-009 vendor-specific TTS provider research
- VOICE-010 Cartesia no-key-safe TTS smoke harness
- VOICE-011 Cartesia WebSocket smoke harness with longer German/English dry-run samples
- VOICE-012 speech naturalness layer for controlled mid-utterance fillers and protected scripted text
- VOICE-013 ElevenLabs no-key-safe streaming TTS smoke harness
- VOICE-014 provider listening comparison for Cartesia vs ElevenLabs
- VOICE-015 provider-neutral prosody naturalness layer for professional-human rhythm and pitch cues
- VOICE-016 provider-specific prosody rendering previews for Cartesia and ElevenLabs
- VOICE-017 guarded live-capable A/B audio harness for plain vs prosody-shaped text
- VOICE-017 first live ElevenLabs A/B result with prosody strongly preferred in the two-case human listening review
- VOICE-018 offline professional-sales tuning after listening feedback found RESP-003 clear but too slow and still obviously AI-generated
- VOICE-019 dry-run harness comparing VOICE-017-style prosody against VOICE-018 sales-tuned input before live provider calls
- RESP-002 runtime voice-delivery bridge from guarded response to offline ElevenLabs/Cartesia provider preview
- project-local self-containment, voice provider run-boundary, and generated-audio asset-log policies
- RESP-003 runtime live-capable TTS bridge from validated voice-delivery packet to optional provider audio
- RESP-003 first bilingual ElevenLabs live TTS result for German and English campaign responses
- RESP-003 human listening review showing the next voice quality target: faster, less robotic, better pitch/emotion, while preserving clarity

Next voice checkpoint:

- run VOICE-019 live for ElevenLabs first, ideally with `--limit 2`, then record human listening review before making any sales-tuned quality claim
- connect RESP-003 audio output to the local demo/playback flow after the dry-run and missing-key gates remain stable
- expand RESP-002 from single-response segment wrapping to multi-segment runtime packets when campaign questions or disclosures are spoken in the same turn
- expand the VOICE-017 live A/B beyond the first two ElevenLabs cases, or add a second listener before treating the result as stronger evaluation evidence
- compare original guarded text against filler-only and prosody-shaped text if the thesis needs a more detailed ablation
- rate whether rare fillers, pause/rate/pitch cues, and bounded stretches improve human-likeness without reducing trust across more cases
- optionally test Cartesia against the same VOICE-017 cases to see whether richer direct tags can match or beat the ElevenLabs result
- verify campaign qualification questions and compliance statements remain clean in audio
- keep environment-only API key and voice ID handling
- use synthetic prompts only
- upload no customer audio
