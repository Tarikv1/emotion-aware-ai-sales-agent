# Thesis Writing Guide

Use this folder as the running memory of the thesis, not just as a place for polished final text.

## Purpose

Capture decisions, rationale, dataset choices, experiment scope, limitations, source references, implementation failures, and evaluation notes while the project is being built.

The goal is that the final thesis can be written from project artifacts instead of reconstructed from memory.

## Current Thesis Shape

The thesis is no longer only a small prompt-comparison project. It now has several connected tracks:

- emotion-aware strategy adaptation
- persuasion strategy selection
- vertical-agnostic sales-agent product architecture
- campaign-specific guardrails
- bilingual German/English runtime behavior
- realtime latency and call-control constraints
- voice/TTS provider evaluation
- speech naturalness and speech-realism design
- private call-center data policy and future learning path
- thesis/product review gates and reproducibility discipline

When writing, keep the distinction clear:

- Thesis evidence: what experiments and references support.
- Product design: what a client-usable system needs.
- Future work: what is planned but not proven yet.

## Thesis-Friendly Document Map

Core thesis documents:

- `PROJECT_BRIEF.md`: stable project definition
- `THESIS_OUTLINE.md`: chapter map and evidence map
- `THESIS_REFERENCE_REGISTRY.md`: central source registry
- `SPEECH_REALISM_REFERENCES.md`: speech realism and language-aware voice references
- `FIRST_EXPERIMENT_PLAN.md`: first experimental slice
- `BASELINE_SPEC.md`: adaptive vs non-adaptive baseline design
- `EVALUATION_RUBRIC.md`: qualitative scoring dimensions
- `PROMPT_EVAL_WORKFLOW.md`: prompt comparison workflow
- `METHODOLOGY_LOG.md`: running record of work done and why
- `DECISION_LOG.md`: accepted decisions and alternatives
- `AI_USAGE_NOTE.md`: AI-assisted work disclosure
- `COLLABORATION_NOTE.md`: collaboration and attribution boundaries

Data documents:

- `../data/DATASETS.md`: local and candidate dataset inventory
- `../data/DATA_READINESS.md`: readiness, gaps, and data risks
- `../data/DATA_USAGE_POLICY.md`: public/private data use rules
- `../data/PRIVATE_CALL_CENTER_DATA_POLICY.md`: private audio boundary
- `../data/PRIVATE_CALL_LEARNING_PIPELINE.md`: future private call pattern-mining pipeline
- `../data/MELD_LABEL_MAPPING.md`: compact emotion mapping
- `../data/PERSUASION_LABEL_MAPPING.md`: compact persuasion mapping

Product/method documents:

- `../product/PRODUCT_BRIEF.md`: product definition
- `../product/VERTICAL_AGNOSTIC_PRODUCT_MODEL.md`: campaign-driven architecture
- `../product/REALTIME_AGENT_ARCHITECTURE.md`: realtime layers and latency
- `../product/SIMULATION_CONTRACT.md`: simulation schema and expected outputs
- `../product/RESP_001_GUARDED_RESPONSE_GENERATION.md`: guarded response generation
- `../product/RESP_002_RUNTIME_VOICE_DELIVERY.md`: voice delivery layer
- `../product/RESP_003_RUNTIME_LIVE_TTS.md`: live-capable TTS boundary
- `../product/VOICE_023_SPEECH_REALISM_LAYER.md`: planned speech-realism product rules
- `../product/COMMANDS.md`: reproducibility command map

Attribution and process documents:

- `../third-party-inspirations.md`: external repos, provider docs, and tool ideas
- `../product-review-gates.md`: review workflow for product/security/QA changes

## What To Record As We Work

Record a note when:

- a dataset is chosen, rejected, or downgraded
- a source materially influences product or thesis direction
- a metric is selected or postponed
- an architecture decision is made
- a rule baseline changes
- an LLM or voice provider changes output quality
- a bug reveals a limitation
- a privacy or retention boundary changes
- a user listening review changes direction
- a future idea is deferred

Each note should answer:

- What did we try?
- What data or source did we use?
- What changed?
- What was learned?
- Why does it matter for the thesis?
- What limitation or follow-up remains?

## Source Rules

Use `THESIS_REFERENCE_REGISTRY.md` as the first stop for source links.

Run the pre-push thesis traceability gate before a GitHub checkpoint:

```powershell
python scripts\check_thesis_reference_registry.py
python scripts\check_thesis_update_gate.py
```

The reference guard catches external URLs that were used in project files but not captured in the registry or third-party inspiration log. The update gate catches product, runtime, data, prompt, or experiment changes that did not touch any thesis tracking document.

Separate source roles:

- Academic papers support related work and methodology.
- Dataset docs support data chapter claims.
- Provider docs support implementation decisions.
- Sales-practice articles support product context only.
- GitHub repos support attribution and inspiration only unless code is actually reused.
- Private call-center data, if later used, supports restricted findings only.

Do not:

- treat provider marketing claims as measured results
- cite sales blogs as peer-reviewed evidence
- claim private-data-derived improvements are public-only
- copy proprietary or third-party text into the thesis
- include raw private transcripts, private audio, names, phone numbers, addresses, or health/financial facts

If a checkpoint is too small for a full methodology entry, still update the roadmap or decision log when the change affects thesis structure, evidence, scope, tooling, or future writing assumptions.

## Writing From Evidence

Before writing a claim, find the artifact that supports it.

Examples:

- Claim: "The rule baseline was strong for final decisions but weaker on emotion detection."
  - Evidence: `research/experiments/PROD-004-rule-baseline.md`
- Claim: "Voice quality improved after sales-tuned prosody."
  - Evidence: `research/experiments/VOICE-019-sales-tuned-live-ab-audio.md`
- Claim: "Improved custom ElevenLabs voices were preferred."
  - Evidence: `research/experiments/VOICE-021-elevenlabs-custom-voice-comparison.md`
- Claim: "Private audio is not uploaded or committed."
  - Evidence: `../data/PRIVATE_CALL_CENTER_DATA_POLICY.md`
- Claim: "Speech realism is language-aware but avoids stereotypes."
  - Evidence: `SPEECH_REALISM_REFERENCES.md` and `../product/VOICE_023_SPEECH_REALISM_LAYER.md`

If no artifact supports the claim, write it as future work or do not write it.

## Suggested Chapter Workflow

Recommended order:

1. Draft the Introduction from `PROJECT_BRIEF.md`, `ROADMAP.md`, and `PRODUCT_BRIEF.md`.
2. Draft Data from `DATASETS.md`, `DATA_READINESS.md`, and `DATA_USAGE_POLICY.md`.
3. Draft Methodology from `BASELINE_SPEC.md`, `SIMULATION_CONTRACT.md`, `REALTIME_AGENT_ARCHITECTURE.md`, and voice docs.
4. Draft Experiments from `research/experiments/`.
5. Draft Related Work from `THESIS_REFERENCE_REGISTRY.md` and source notes.
6. Draft Discussion from `METHODOLOGY_LOG.md`, `DECISION_LOG.md`, and known limitations.
7. Draft Conclusion from completed roadmap checkpoints and deferred work.

Why this order:

- it starts from project evidence, not abstract theory
- it avoids writing related work before the actual scope is stable
- it helps prevent overclaiming

## Limitations To Preserve

Do not hide these:

- public datasets do not match real call-center sales perfectly
- early experiments use small and synthetic case sets
- initial voice quality review is owner-listening, not a formal user study
- provider documentation is not the same as measured production performance
- private call-center data has not yet been processed
- German/English speech-realism profiles are literature-informed but need listener validation
- the product is not yet production deployed
- legal/compliance review is not complete for live insurance deployment

These limitations make the thesis stronger when framed honestly.

## Citation And Reference Preparation

Before final thesis writing:

- convert registry entries into the university-required citation style
- verify each source URL still resolves
- confirm dataset licenses and access terms
- separate academic references from provider/product documentation
- add retrieval dates for web/provider docs
- avoid citing generated reports as external sources; cite them as project artifacts

## Writing Rule Of Thumb

If a future thesis sentence would begin with:

- `We decided to...`
- `The system was designed to...`
- `The dataset was selected because...`
- `A limitation of this approach is...`
- `This provider was chosen because...`
- `The voice layer was changed after...`
- `Private data was handled by...`

then that thought probably belongs in one of the thesis docs now.
