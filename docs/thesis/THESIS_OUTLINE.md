# Thesis Outline

This is the working chapter map for the Emotion Aware AI Sales Agent thesis.

It is not the final table of contents. It is a planning document that maps the work already done to future thesis sections, evidence files, and open gaps.

## 1. Introduction

### 1.1 Problem Context

- Call-center sales conversations are emotionally dynamic.
- A customer may sound interested, skeptical, rushed, annoyed, confused, or anxious.
- A fixed script can miss those states and respond in ways that reduce trust.
- A useful sales agent needs to adapt while staying inside approved campaign and compliance boundaries.

### 1.2 Thesis Motivation

- Emotion-aware adaptation may improve response appropriateness, objection handling, and perceived naturalness.
- Voice output creates an additional challenge: a technically correct answer can still sound robotic, slow, flat, or scripted.
- The project therefore studies both strategy adaptation and speech/voice delivery as parts of a sales-agent prototype.

### 1.3 Product Motivation

- The project is also a real product direction: a configurable AI sales agent for call centers.
- The product is not insurance-only, not B2B-only, and not limited to one product category.
- The intended architecture is one reusable sales-agent core plus configurable `SalesCampaign` profiles.
- The first real client context is German B2C outbound insurance, but this is a first vertical, not the product boundary.

### 1.4 Research Questions

Draft research questions:

- Does emotion-aware strategy selection improve persuasive response quality compared with a non-adaptive baseline?
- Can a compact emotion and persuasion taxonomy support believable sales-dialogue adaptation?
- How can the agent preserve safety and campaign guardrails while improving naturalness and objection handling?
- How should English and German voice output be shaped so speech sounds more human without relying on stereotypes?
- What are the limits of public datasets, synthetic simulations, and restricted private call-center data for this system?

### 1.5 Contributions

Likely contributions:

- a vertical-agnostic sales-agent product architecture based on `SalesCampaign` profiles
- a universal sales dialogue layer separated from campaign-owned product knowledge and wording
- source-grounded campaign claim governance for real public product facts
- a reproducible prompt and simulation workflow
- emotion-to-strategy adaptation experiments
- replay-first live failure methodology and adversarial regression matrix design
- bilingual runtime and voice checkpoints
- hosted speech-interface/tool-boundary evidence with latency limits
- privacy-first private-call learning scaffold
- language-aware speech-realism reference layer for future voice naturalness work

Evidence sources:

- `PROJECT_BRIEF.md`
- `ROADMAP.md`
- `DECISION_LOG.md`
- `METHODOLOGY_LOG.md`
- `../product/PRODUCT_BRIEF.md`
- `../product/VERTICAL_AGNOSTIC_PRODUCT_MODEL.md`

## 2. Related Work

### 2.1 Conversational AI And Sales Agents

- dialogue systems
- task-oriented agents
- LLM-based response generation
- human handoff and escalation
- guardrails for customer-facing automation

Evidence sources:

- `THESIS_REFERENCE_REGISTRY.md`
- `../../runtime/architecture/REALTIME_AGENT_ARCHITECTURE.md`
- `../product/RESP_001_GUARDED_RESPONSE_GENERATION.md`

### 2.2 Speech Emotion Recognition

- speech emotion datasets
- compact emotion taxonomy
- multimodal emotion recognition
- limitations of acted or entertainment-dialogue data

Evidence sources:

- `docs/data/DATASETS.md`
- `docs/data/DATA_READINESS.md`
- `docs/data/MELD_LABEL_MAPPING.md`
- `../architecture/VOICE_FEATURE_MODULE.md`

### 2.3 Persuasive Dialogue Systems

- persuasion strategy labels
- strategy selection
- persuasive dialogue in non-sales contexts
- ethical constraints around persuasion
- sales psychology mechanisms that are useful for live calls: adaptive selling, listening, buyer confidence, autonomy, friction diagnosis, trust repair, conversation repair, and spoken brevity
- rejected sales-psychology tactics: false scarcity, hidden emotion diagnosis, commitment traps, full customer-category echoing, and generic unsourced persuasion tricks

Evidence sources:

- `docs/data/PERSUASION_LABEL_MAPPING.md`
- `BASELINE_SPEC.md`
- `THESIS_REFERENCE_REGISTRY.md`
- `../product/PROD_053A_ENGLISH_SALES_PSYCHOLOGY_DEEP_DIVE.md`
- `../product/PROD_053B_COMPACT_ENGLISH_PSYCHOLOGY_LAYER_REVIEW.md`
- `../product/PROD_053C_ENGLISH_SPOKEN_RESPONSE_EXPANSION_REVIEW.md`
- `../product/PROD_053D_ENGLISH_REVIEW_IMPORT.md`
- `research/experiments/generated/PROD-053A-english-sales-psychology-deep-dive/`
- `research/experiments/generated/PROD-053B-compact-english-psychology-layer-review/`
- `research/experiments/generated/PROD-053C-english-spoken-response-expansion-review/`
- `research/experiments/generated/PROD-053D-english-review-import/`

### 2.4 Voice Naturalness And Speech Realism

- filled pauses and disfluencies
- English and German speech-planning markers
- pause and breath behavior
- smiled speech and audible warmth
- language-aware realism without stereotypes

Evidence sources:

- `SPEECH_REALISM_REFERENCES.md`
- `../product/VOICE_023_SPEECH_REALISM_LAYER.md`
- `../product/VOICE_012_SPEECH_NATURALNESS_LAYER.md`
- `../product/VOICE_015_PROSODY_NATURALNESS_LAYER.md`
- `../product/VOICE_022_SPOKEN_TEXT_NORMALIZATION.md`

### 2.5 Privacy, Data Governance, And Responsible Use

- public vs private data
- data minimization
- retention and deletion
- no-provider-upload default for raw private audio
- special handling for sensitive domains such as insurance

Evidence sources:

- `docs/data/DATA_USAGE_POLICY.md`
- `docs/data/PRIVATE_CALL_CENTER_DATA_POLICY.md`
- `docs/data/PRIVATE_CALL_LEARNING_PIPELINE.md`
- `THESIS_REFERENCE_REGISTRY.md`

## 3. Data

### 3.1 Public Dataset Inventory

Datasets currently considered:

- IEMOCAP
- MELD
- Persuasion for Good

For each dataset, describe:

- source
- local status
- modality
- labels
- language
- task fit
- limitations
- licensing/access uncertainty

Evidence sources:

- `docs/data/DATASETS.md`
- `docs/data/DATA_READINESS.md`
- `THESIS_REFERENCE_REGISTRY.md`

### 3.2 Public Dataset Limitations

Important limitations:

- MELD is TV dialogue, not call-center speech.
- Persuasion for Good is charity persuasion, not commercial sales.
- IEMOCAP is acted dyadic emotion data, not real sales calls.
- Public datasets may support baseline design but cannot fully represent the final deployment context.

### 3.3 Synthetic Product Simulations

Simulation case sets:

- `PROD-001`: first qualification/scheduling simulation
- `PROD-002`: strict B2C insurance simulation
- `PROD-003`: mixed campaign simulation
- `PROD-004`: sales difficulty gauntlet
- `PROD-005`: realtime latency and call-control simulation

Evidence sources:

- `research/experiments/PROD-001-qualification-simulation.md`
- `research/experiments/PROD-002-b2c-insurance-simulation.md`
- `research/experiments/PROD-003-mixed-campaigns-simulation.md`
- `research/experiments/PROD-004-sales-difficulty-gauntlet.md`
- `research/experiments/PROD-005-realtime-latency-call-control.md`

### 3.4 Private Call-Center Data Position

Current position:

- private call-center recordings are not part of public reproducible experiments
- raw private audio must stay under `data/private/`
- private identifiers are not learning signal
- pattern mining comes before fine-tuning
- safe export requires redaction and human review

Evidence sources:

- `docs/data/DATA_USAGE_POLICY.md`
- `docs/data/PRIVATE_CALL_CENTER_DATA_POLICY.md`
- `docs/data/PRIVATE_CALL_LEARNING_PIPELINE.md`
- `research/experiments/PRIVATE-CALL-LEARNING-001.md`

### 3.5 Source-Grounded Public Product Fixture

Current source-grounded public fixture:

- `public-openai-chatgpt-plans`
- official public OpenAI sources only
- source-grounded claim objects for product, pricing, plan, privacy, sign-up, API-boundary, and feature claims
- plan categories: Free, Go, Plus, Pro, Business Codex, Business ChatGPT & Codex, Enterprise
- no official OpenAI affiliation claim
- no raw private transcript source material

Evidence sources:

- `research/sources/public_openai_chatgpt_plans/source_manifest.json`
- `research/sources/public_openai_chatgpt_plans/source_notes.md`
- `runtime/campaigns/examples/public-openai-chatgpt-plans.json`
- `research/experiments/generated/PUBLIC-OPENAI-SOURCE-BUNDLE-001/`
- `research/experiments/generated/PUBLIC-OPENAI-CAMPAIGN-FIXTURE-001/`
- `research/experiments/generated/PUBLIC-OPENAI-CAMPAIGN-DIALOGUE-001/`
- `research/experiments/generated/PUBLIC-OPENAI-CLOSE-SEMANTICS-001/`
- `research/experiments/generated/PUBLIC-OPENAI-UNIVERSAL-ISOLATION-001/`

## 4. System Design And Methodology

### 4.1 Architecture Overview

Core architecture:

```text
customer input
  -> ASR or transcript
  -> customer-state estimate
  -> sales difficulty / interest state
  -> strategy selection
  -> guarded response generation
  -> speech/voice delivery
  -> logging and review
```

Product architecture:

```text
reusable sales-agent core
  + universal sales dialogue behavior
  + configurable SalesCampaign profiles
  + source-grounded campaign claim objects
  + campaign guardrails
  + bilingual runtime support
  + optional future conversation planner
  + deterministic memory/verifier/source boundary
  + backend-neutral prosody planner
  + human handoff / escalation
```

Evidence sources:

- `../../runtime/architecture/REALTIME_AGENT_ARCHITECTURE.md`
- `../product/SIMULATION_CONTRACT.md`
- `../product/VERTICAL_AGNOSTIC_PRODUCT_MODEL.md`
- `../product/RESP_001_GUARDED_RESPONSE_GENERATION.md`
- `research/experiments/generated/UNIVERSAL-BUYER-MOVE-RECOGNITION-001/`
- `research/experiments/generated/UNIVERSAL-BUYER-MOVES-CROSS-CAMPAIGN-001/`
- `research/experiments/generated/UNIVERSALIZATION-DRIFT-CLEANUP-001/`
- `research/experiments/generated/LOCAL-QWEN-TWO-HEAD-ARCHITECTURE-001/`
- `research/experiments/generated/FISH-INSPIRED-PROSODY-TAXONOMY-001/`

### 4.2 Emotion And Persuasion Taxonomies

Cover:

- compact emotion taxonomy
- compact persuasion taxonomy
- why a small taxonomy was chosen
- how strategy labels map to sales behavior
- how rule baselines and LLM responses are compared

Evidence sources:

- `BASELINE_SPEC.md`
- `docs/data/MELD_LABEL_MAPPING.md`
- `docs/data/PERSUASION_LABEL_MAPPING.md`
- `research/experiments/EXP-001-phase1-prompt-baseline.md`
- `research/experiments/EXP-002-dataset-derived-baseline.md`

### 4.3 Campaign Configuration Model

Explain `SalesCampaign` as the central product abstraction.

Fields to discuss:

- campaign id
- client/product
- product category
- fixture type
- source policy
- B2B/B2C type
- approved opening
- qualification questions
- allowed claims
- forbidden claims
- source-grounded claims
- product or offer summary
- high-level value proposition
- close modes
- disclosures
- escalation triggers
- scheduling goal
- self-serve close target
- contact-sales target
- handoff role
- compliance notes

Evidence sources:

- `../product/VERTICAL_AGNOSTIC_PRODUCT_MODEL.md`
- `../product/B2B_B2C_SCOPE.md`
- `../product/INSURANCE_CLIENT_CONTEXT.md`
- `../product/LEAD_DATABASE_DESIGN.md`
- `runtime/campaigns/examples/public-openai-chatgpt-plans.json`
- `research/experiments/generated/PUBLIC-OPENAI-CAMPAIGN-FIXTURE-001/`
- `research/experiments/generated/PUBLIC-OPENAI-CROSS-CAMPAIGN-CONTAMINATION-001/`

### 4.4 Realtime Runtime And Latency

Discuss:

- 1-2 second customer-facing response target
- bridge responses when slow lookup is needed
- sub-agents as background helpers, not blocking response path
- hang-up and call-control triggers
- interruption handling
- deterministic response-shaping constraints for live calls: answer first, keep turns short, preserve low-pressure relief, ask one question, and stop
- language-lane separation: English exact phrase review can be owner-reviewed now, while German exact phrase acceptance requires native or source-backed wording review
- universal-vs-campaign boundary: response behavior and shapes are universal; product facts and customer-facing product wording are campaign-owned
- replay-first debugging: capture live evidence, classify currentness, reproduce locally, patch only current reproduced defects, then add exact regressions, generalized variants, and negative controls
- semantic-understanding shift: move from exact scenario patching toward semantic frames, buyer-state tracking, relation fidelity, ASR aliases, memory progression, and generalized intent/action planning
- local LLM boundary: a future LLM may plan conversational moves, but campaign facts, source truth, side effects, memory verification, and safety remain deterministic
- live-turn latency: any model in the live voice turn must meet roughly 2-3 second perceived latency before live wiring

Evidence sources:

- `../../runtime/architecture/REALTIME_AGENT_ARCHITECTURE.md`
- `../../runtime/policy/CALL_TERMINATION_POLICY.md`
- `research/experiments/PROD-005-realtime-latency-call-control.md`
- `research/experiments/VOICE-006-safe-interruption.md`
- `../product/PROD_052_LANGUAGE_LANE_REVIEW_SEPARATION.md`
- `../product/PROD_053B_COMPACT_ENGLISH_PSYCHOLOGY_LAYER_REVIEW.md`
- `../product/PROD_053C_ENGLISH_SPOKEN_RESPONSE_EXPANSION_REVIEW.md`
- `../product/PROD_053D_ENGLISH_REVIEW_IMPORT.md`
- `research/experiments/generated/PROD-052-language-lane-review-separation/`
- `research/experiments/generated/PROD-053B-compact-english-psychology-layer-review/`
- `research/experiments/generated/PROD-053C-english-spoken-response-expansion-review/`
- `research/experiments/generated/PROD-053D-english-review-import/`
- `research/experiments/generated/CURRENT-LIVE-TRANSCRIPT-REPLAY-001/`
- `research/experiments/generated/LIVE-INSPIRED-ADVERSARIAL-DIALOGUE-MATRIX-001/`
- `research/experiments/generated/PUBLIC-OPENAI-SEMANTIC-UNDERSTANDING-001/`
- `research/experiments/generated/PUBLIC-OPENAI-LIVE-SEMANTIC-PIPELINE-001/`
- `research/experiments/generated/LOCAL-QWEN-LIVE-ACTION-LATENCY-DECISION-001/`
- `research/experiments/generated/LOCAL-OLLAMA-SMALL-LIVE-ACTION-MODEL-DECISION-001/`

### 4.5 Voice And Speech Delivery

Discuss the evolution:

- browser speech demo
- local TTS fallback
- provider-readiness gate
- Cartesia and ElevenLabs smoke tests
- prosody naturalness
- sales-tuned speech
- custom voice comparison
- spoken text normalization
- planned speech-realism layer
- Liquid Audio feasibility and retirement after failed manual listening review
- Fish-inspired internal prosody taxonomy and deterministic planner
- no-provider ElevenLabs prosody mapping prototype
- Ultravox hosted speech-interface sandbox, manual listening review, and latency-limited conclusion
- Kokoro as optional future local TTS benchmark candidate
- ElevenLabs as the current live voice path
- live TTS gating for generic campaigns
- audio playback error separation and raw URL avoidance in spoken self-serve closes
- distinction between dry-run text validation and live ASR/TTS/latency/voice-realism evidence

Evidence sources:

- `research/experiments/VOICE-001-tts-response-prototype.md`
- `research/experiments/VOICE-004-browser-speech-demo.md`
- `research/experiments/VOICE-009-tts-provider-research.md`
- `research/experiments/VOICE-013-elevenlabs-tts-smoke.md`
- `research/experiments/VOICE-019-sales-tuned-live-ab-audio.md`
- `research/experiments/VOICE-021-elevenlabs-custom-voice-comparison.md`
- `research/experiments/VOICE-022-spoken-text-normalization.md`
- `SPEECH_REALISM_REFERENCES.md`
- `research/experiments/generated/LIQUID-AUDIO-LISTENING-REVIEW-DECISION-001/`
- `research/experiments/generated/FISH-INSPIRED-PROSODY-TAXONOMY-001/`
- `research/experiments/generated/PROSODY-TAXONOMY-QUALITY-DECISION-001/`
- `research/experiments/generated/ELEVENLABS-PROSODY-MAPPING-READINESS-001/`
- `research/experiments/generated/PROSODY-TAXONOMY-CLEANUP-001/`
- `research/experiments/generated/ELEVENLABS-PROSODY-MAPPING-PROTOTYPE-001/`
- `research/experiments/generated/ELEVENLABS-PROSODY-MAPPING-QUALITY-AUDIT-001/`
- `research/experiments/generated/ULTRAVOX-WEBSOCKET-TEXT-SANDBOX-001/`
- `research/experiments/generated/ULTRAVOX-WEBSOCKET-AUDIO-SANDBOX-001/`
- `research/experiments/generated/ULTRAVOX-AUDIO-SANDBOX-REVIEW-DECISION-001/`
- `research/experiments/generated/LIVE-DEMO-GENERIC-CAMPAIGN-LIVE-TTS-GATE-001/`
- `research/experiments/generated/LIVE-DEMO-TTS-AUDIO-PLAYBACK-001/`
- `research/experiments/generated/PUBLIC-OPENAI-CLOSE-SEMANTICS-001/`

### 4.6 Guardrails And Safety

Discuss:

- no unsupported claims
- no fear pressure
- no unnecessary sensitive data collection
- detailed insurance/medical/legal/coverage questions go to human specialist
- private data stays local
- API keys stay environment-only
- provider runs require explicit `--live`
- no fake email/calendar/CRM side effects
- no vendor affiliation claims for public-data simulations
- no unsupported product, pricing, privacy, legal, security, ROI, or model-availability claims
- raw private transcripts must not be copied into public thesis evidence

Evidence sources:

- `../product/INSURANCE_CLIENT_CONTEXT.md`
- `../../runtime/providers/VOICE_PROVIDER_RUN_BOUNDARY.md`
- `../product/RESP_003_RUNTIME_LIVE_TTS.md`
- `docs/data/PRIVATE_CALL_CENTER_DATA_POLICY.md`
- `research/experiments/generated/PUBLIC-OPENAI-UNIVERSAL-ISOLATION-001/`
- `research/experiments/generated/PUBLIC-OPENAI-SOURCE-BUNDLE-001/`

## 5. Experiments And Evaluation

### 5.1 Prompt And Strategy Experiments

Experiments:

- `EXP-001`
- `EXP-002`

Evaluation dimensions:

- emotional appropriateness
- strategy coherence
- usefulness
- safety
- naturalness

Evidence sources:

- `EVALUATION_RUBRIC.md`
- `PROMPT_EVAL_WORKFLOW.md`
- `research/experiments/EXP-001-phase1-prompt-baseline.md`
- `research/experiments/EXP-002-dataset-derived-baseline.md`

### 5.2 Product Simulations

Experiments:

- qualification simulation
- rule baseline
- LLM vs rule comparison
- sales difficulty gauntlet
- SQLite export
- realtime latency and call-control
- safe call-control softening and runtime update from `PROD-049` through `PROD-051`
- language-lane review separation in `PROD-052`
- source-backed English sales psychology research in `PROD-053A`
- compact English psychology layer review in `PROD-053B`
- broader English spoken-response expansion review in `PROD-053C`
- imported English owner review decisions in `PROD-053D`

Evidence sources:

- `research/experiments/PROD-001-rule-baseline.md`
- `research/experiments/PROD-004-rule-baseline.md`
- `research/experiments/PROD-004-llm-vs-rule-comparison.md`
- `research/experiments/generated/PROD-001/PROD-001-sqlite-report.md`
- `../product/PROD_049_SAFE_END_CALL_BRIDGE_CONTINUE_REVIEW.md`
- `../product/PROD_050_SAFE_CALL_CONTROL_SOFTENING_REGRESSION.md`
- `../product/PROD_051_SAFE_CALL_CONTROL_RUNTIME_UPDATE.md`
- `../product/PROD_052_LANGUAGE_LANE_REVIEW_SEPARATION.md`
- `../product/PROD_053A_ENGLISH_SALES_PSYCHOLOGY_DEEP_DIVE.md`
- `../product/PROD_053B_COMPACT_ENGLISH_PSYCHOLOGY_LAYER_REVIEW.md`
- `../product/PROD_053C_ENGLISH_SPOKEN_RESPONSE_EXPANSION_REVIEW.md`
- `../product/PROD_053D_ENGLISH_REVIEW_IMPORT.md`

### 5.3 Voice Experiments

Evaluation dimensions:

- latency
- German/English support
- pronunciation
- naturalness
- trust
- emotional appropriateness
- robot-detection risk
- protected-text clarity

Evidence sources:

- `research/experiments/VOICE-010-cartesia-tts-smoke.md`
- `research/experiments/VOICE-013-elevenlabs-tts-smoke.md`
- `research/experiments/VOICE-017-live-ab-audio.md`
- `research/experiments/VOICE-019-sales-tuned-live-ab-audio.md`
- `research/experiments/VOICE-021-elevenlabs-custom-voice-comparison.md`

### 5.4 Validation And Review Gates

Discuss validators as methodological controls:

- setup checker
- project drift guard
- private data boundary validator
- provider run boundary
- generated audio asset log
- context reader
- voice and response validators
- focused validation budgets
- source-bundle validators
- universal isolation validators
- cross-campaign contamination validators
- live replay validators
- adversarial matrices
- commercial and resonance review packets
- evidence validators versus quality gates
- manual live tests and listening reviews as qualitative ground truth
- quality-gate failures as useful evidence rather than automatic integration blockers

Evidence sources:

- `../product/COMMANDS.md`
- `../product/PROJECT_DRIFT_GUARD.md`
- `../product/PROJECT_SELF_CONTAINMENT_POLICY.md`
- `../../runtime/providers/VOICE_GENERATED_AUDIO_ASSET_LOG.md`
- `research/experiments/generated/CURRENT-LIVE-TRANSCRIPT-REPLAY-001/`
- `research/experiments/generated/LIVE-INSPIRED-ADVERSARIAL-DIALOGUE-MATRIX-001/`
- `research/experiments/generated/COMMERCIAL-SALES-CONVERSATION-REVIEW-001/`
- `research/experiments/generated/CONVERSATIONAL-RESONANCE-REVIEW-001/`
- `research/experiments/generated/PUBLIC-OPENAI-SOURCE-BUNDLE-001/`
- `research/experiments/generated/PUBLIC-OPENAI-UNIVERSAL-ISOLATION-001/`
- `research/experiments/generated/PUBLIC-OPENAI-CROSS-CAMPAIGN-CONTAMINATION-001/`
- `research/experiments/generated/COMMERCIAL-SALES-PERFORMANCE-GATE-001/`
- `research/experiments/generated/LOCAL-QWEN-MIXED-REPLAY-QUALITY-GATE-001/`
- `research/experiments/generated/PROSODY-TAXONOMY-QUALITY-DECISION-001/`

### 5.5 Source-Grounded Product Dialogue Evaluation

Evaluation focus:

- direct product-intro answers
- plan fit and upgrade value
- price and API-boundary answers
- privacy/training and security/admin boundaries
- self-serve close and contact-sales close
- unsupported-claim refusal
- cross-campaign contamination prevention
- sales momentum beyond FAQ behavior
- objection handling and fit-based recommendation/disqualification
- memory progression and loop prevention
- semantic preservation across paraphrases and spoken variations

Evidence sources:

- `research/experiments/generated/PUBLIC-OPENAI-CAMPAIGN-DIALOGUE-001/`
- `research/experiments/generated/PUBLIC-OPENAI-CLOSE-SEMANTICS-001/`
- `research/experiments/generated/PUBLIC-OPENAI-CROSS-CAMPAIGN-CONTAMINATION-001/`
- `research/experiments/generated/PUBLIC-OPENAI-LIVE-SALES-READINESS-001/`
- `research/experiments/generated/PUBLIC-OPENAI-DECISION-STAGE-SELLING-001/`
- `research/experiments/generated/PUBLIC-OPENAI-COMMERCIAL-CLOSING-001/`

### 5.6 Hosted Atlas Natural-Sales And Pricing Evaluation

Evaluation focus:

- hosted ElevenLabs text/simulation behavior for Atlas Web Studio
- natural sales behavior from 036: email confirmation, scheduling, CRM/payment capability, custom dashboard scope, visual mockup limits, CTA fatigue, guarantee-only disqualification, and stale goodbye/future-pricing conflicts
- terminal-control behavior from 039: hard stop, delivery-timing deduplication, gatekeeper callback, gatekeeper note, one built-in `end_call`, and no post-terminal activity
- detailed pricing behavior from 040: buyer-triggered pricing, one active price lane, CRM repetition-safe scope follow-up, portal proof/scope control, no unsupported fixed quote or ceiling, and no CTA reopening during active price or scope follow-up
- provider label versus deterministic independent trace result versus manual transcript review
- discrepancy classification: product defect, provider evaluator defect, stale test-contract defect, or incomplete simulation
- structural readback after provider writes: prompt/KB write success, 17 ordered KB attachments, 30 Analysis criteria, one built-in `end_call`, inactive Procedures, and unrelated-tool/configuration preservation
- credit-aware evidence collection: targeted repair reruns first, broad reruns only when they answer a real evidence question

Evidence sources:

- `research/experiments/generated/ELEVENLABS-036-natural-sales-scenarios/report.md`
- `research/experiments/generated/ELEVENLABS-036-natural-sales-scenarios/llm_gpt55_behavior4_full1_independent.json`
- `research/experiments/generated/ELEVENLABS-036-natural-sales-scenarios/credit_capped_broad_ready_final_20260713_independent.json`
- `research/experiments/generated/ELEVENLABS-036-natural-sales-scenarios/credit_capped_crm_capability_lock_final_20260713_independent.json`
- `research/experiments/generated/ELEVENLABS-039-end-call-edge-case-hardening/report.md`
- `research/experiments/generated/ELEVENLABS-039-end-call-edge-case-hardening/gpt55_regression_independent.json`
- `research/experiments/generated/ELEVENLABS-040-detailed-pricing-control/report.md`
- `research/experiments/generated/ELEVENLABS-040-detailed-pricing-control/live_agent_patch_result.json`
- `research/experiments/generated/ELEVENLABS-040-detailed-pricing-control/live_test_independent_full_credit_capped_final.json`
- `research/experiments/generated/ELEVENLABS-040-detailed-pricing-control/live_test_multi_feature_atomic_scope_final_independent.json`
- `research/experiments/generated/ELEVENLABS-040-detailed-pricing-control/live_test_crm_repetition_safe_final_independent.json`
- `research/experiments/generated/ELEVENLABS-040-detailed-pricing-control/live_test_portal_proof_scope_final_independent.json`

Claim boundaries:

- targeted 040 repair traces passed independent validation; full 036/040 credit-capped captures remain mixed and must not be described as universally green
- the last CRM repetition patch received structural readback but no fresh post-write simulation; targeted traces support the repaired behavior classes but do not transcript-verify the final live fingerprint
- the earlier broad-readiness checkpoint remained blocked; later detailed-pricing evidence superseded its product configuration and structural facts, not the missing post-final-write behavioral proof
- no dashboard criterion or Analysis definition was weakened to manufacture a pass, but new 040 regression tests were added
- no outbound call was placed
- accumulated evidence supports targeted hosted Atlas text/simulation behavior; it does not establish broad live readiness, final-fingerprint transcript verification, PSTN audio, ASR, latency, interruption handling, buyer perception, conversion impact, or real-customer performance

## 6. Results And Discussion

### 6.1 What Worked

Likely themes:

- adaptive prompts performed better than non-adaptive seed baselines
- deterministic rule baselines were strong for final decision consistency
- rule baseline was weaker on emotion detection
- voice prosody and sales tuning improved perceived quality
- custom ElevenLabs voices improved over first versions
- protected-text segmentation prevented unsafe naturalness changes
- source-grounded public-product fixture improved claim governance
- semantic frame mapping reduced reliance on exact dialogue patches
- prosody planning became an internal/backend-neutral design layer
- Atlas 039 terminal-control traces reached independently validated atomic `end_call` behavior for hard stops, delivery timing, and gatekeeper outcomes
- Atlas 040 targeted repair traces showed that buyer-triggered pricing, one-lane scope control, CRM repetition handling, and portal proof/scope control can be validated after real product defects are fixed

### 6.2 What Did Not Work Or Remains Weak

Likely themes:

- voice still sounds AI-generated
- flat pitch and stable pacing reduce realism
- filler and hesitation behavior needs better language-specific control
- browser speech recognition can mis-route language
- cloud provider quality and latency are provider-specific
- public datasets do not match real call-center conditions
- Qwen2.5-7B and tested small local models are not live-ready for per-turn voice use
- QLoRA training pipeline is mechanically valid but current local model strategy is insufficient
- Liquid Audio generated unintelligible TTS and is retired as a voice backend
- Fish-inspired prosody taxonomy needs cleanup before any ElevenLabs mapping prototype
- provider dashboard labels can disagree with deterministic trace review or active product contracts
- full Atlas 036/040 credit-capped captures contain mixed or stale-contract evidence and should be used as limitations, not universal green results
- the final Atlas fingerprint lacks a post-last-write behavior run; structural readback does not replace transcript verification
- targeted hosted text/simulation evidence does not establish broad live readiness, PSTN audio, ASR, latency, interruption handling, buyer perception, conversion impact, or real-customer performance

### 6.3 Threats To Validity

Threats:

- small case sets
- synthetic cases
- owner-only listening review in early phases
- provider docs vs measured performance
- public dataset domain mismatch
- private data not yet integrated
- language proficiency and native-speaker evaluation gaps
- provider evaluator defects, stale test contracts, and incomplete simulations can be mistaken for product quality if trace adjudication is skipped
- targeted repair passes may not generalize to full-suite or real-buyer behavior without broader reruns and supervised call evidence
- credit-aware verification can preserve budget but must be reported plainly when broad reruns were not performed

### 6.4 Ethical And Product Discussion

Discuss:

- persuasion vs manipulation
- avoiding fear pressure
- avoiding unsupported claims
- human handoff for sensitive contexts
- private-data minimization
- transparency around AI-generated speech
- limits of autonomous sales behavior

Evidence sources:

- `METHODOLOGY_LOG.md`
- `DECISION_LOG.md`
- `docs/data/DATA_USAGE_POLICY.md`
- `../product/INSURANCE_CLIENT_CONTEXT.md`

## 7. Conclusion And Future Work

### 7.1 Summary Of Findings

Summarize:

- adaptive strategy selection
- campaign-driven product architecture
- bilingual runtime and voice work
- guardrail-first design
- evidence from simulations and listening tests

### 7.2 Product Future Work

Future work:

- `VOICE-023` speech realism layer
- `RAG-001` source-tracked sales knowledge base
- private call-center pattern mining
- sales-expert feedback dashboard
- broader campaign library
- local demo playback integration
- eventually real supervised call-center pilot

### 7.3 Thesis Future Work

Future work:

- larger dataset-grounded evaluation
- native/proficient speaker listening study
- stronger ablation of voice naturalness layers
- public-only vs restricted-private evidence comparison
- real-call pattern analysis after redaction and review
- non-LLM classifier/action selector baseline
- action-id-only small model or distillation path if it can meet quality and latency gates
- ElevenLabs prosody mapping prototype without provider calls after taxonomy cleanup

## Appendix Candidates

Possible appendices:

- prompt templates
- SalesCampaign schema
- simulation case examples
- evaluation rubric
- provider-readiness matrix
- private-data policy
- command map
- AI usage note
- third-party inspiration and attribution log
