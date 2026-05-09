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
- a reproducible prompt and simulation workflow
- emotion-to-strategy adaptation experiments
- bilingual runtime and voice checkpoints
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
- `../product/REALTIME_AGENT_ARCHITECTURE.md`
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

Evidence sources:

- `docs/data/PERSUASION_LABEL_MAPPING.md`
- `BASELINE_SPEC.md`
- `THESIS_REFERENCE_REGISTRY.md`

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
  + configurable SalesCampaign profiles
  + campaign guardrails
  + bilingual runtime support
  + human handoff / escalation
```

Evidence sources:

- `../product/REALTIME_AGENT_ARCHITECTURE.md`
- `../product/SIMULATION_CONTRACT.md`
- `../product/VERTICAL_AGNOSTIC_PRODUCT_MODEL.md`
- `../product/RESP_001_GUARDED_RESPONSE_GENERATION.md`

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
- B2B/B2C type
- approved opening
- qualification questions
- allowed claims
- forbidden claims
- disclosures
- escalation triggers
- scheduling goal
- handoff role
- compliance notes

Evidence sources:

- `../product/VERTICAL_AGNOSTIC_PRODUCT_MODEL.md`
- `../product/B2B_B2C_SCOPE.md`
- `../product/INSURANCE_CLIENT_CONTEXT.md`
- `../product/LEAD_DATABASE_DESIGN.md`

### 4.4 Realtime Runtime And Latency

Discuss:

- 1-2 second customer-facing response target
- bridge responses when slow lookup is needed
- sub-agents as background helpers, not blocking response path
- hang-up and call-control triggers
- interruption handling

Evidence sources:

- `../product/REALTIME_AGENT_ARCHITECTURE.md`
- `../product/CALL_TERMINATION_POLICY.md`
- `research/experiments/PROD-005-realtime-latency-call-control.md`
- `research/experiments/VOICE-006-safe-interruption.md`

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

Evidence sources:

- `research/experiments/VOICE-001-tts-response-prototype.md`
- `research/experiments/VOICE-004-browser-speech-demo.md`
- `research/experiments/VOICE-009-tts-provider-research.md`
- `research/experiments/VOICE-013-elevenlabs-tts-smoke.md`
- `research/experiments/VOICE-019-sales-tuned-live-ab-audio.md`
- `research/experiments/VOICE-021-elevenlabs-custom-voice-comparison.md`
- `research/experiments/VOICE-022-spoken-text-normalization.md`
- `SPEECH_REALISM_REFERENCES.md`

### 4.6 Guardrails And Safety

Discuss:

- no unsupported claims
- no fear pressure
- no unnecessary sensitive data collection
- detailed insurance/medical/legal/coverage questions go to human specialist
- private data stays local
- API keys stay environment-only
- provider runs require explicit `--live`

Evidence sources:

- `../product/INSURANCE_CLIENT_CONTEXT.md`
- `../product/VOICE_PROVIDER_RUN_BOUNDARY.md`
- `../product/RESP_003_RUNTIME_LIVE_TTS.md`
- `docs/data/PRIVATE_CALL_CENTER_DATA_POLICY.md`

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

Evidence sources:

- `research/experiments/PROD-001-rule-baseline.md`
- `research/experiments/PROD-004-rule-baseline.md`
- `research/experiments/PROD-004-llm-vs-rule-comparison.md`
- `research/experiments/generated/PROD-001/PROD-001-sqlite-report.md`

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

Evidence sources:

- `../product/COMMANDS.md`
- `../product/PROJECT_DRIFT_GUARD.md`
- `../product/PROJECT_SELF_CONTAINMENT_POLICY.md`
- `../product/VOICE_GENERATED_AUDIO_ASSET_LOG.md`

## 6. Results And Discussion

### 6.1 What Worked

Likely themes:

- adaptive prompts performed better than non-adaptive seed baselines
- deterministic rule baselines were strong for final decision consistency
- rule baseline was weaker on emotion detection
- voice prosody and sales tuning improved perceived quality
- custom ElevenLabs voices improved over first versions
- protected-text segmentation prevented unsafe naturalness changes

### 6.2 What Did Not Work Or Remains Weak

Likely themes:

- voice still sounds AI-generated
- flat pitch and stable pacing reduce realism
- filler and hesitation behavior needs better language-specific control
- browser speech recognition can mis-route language
- cloud provider quality and latency are provider-specific
- public datasets do not match real call-center conditions

### 6.3 Threats To Validity

Threats:

- small case sets
- synthetic cases
- owner-only listening review in early phases
- provider docs vs measured performance
- public dataset domain mismatch
- private data not yet integrated
- language proficiency and native-speaker evaluation gaps

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
