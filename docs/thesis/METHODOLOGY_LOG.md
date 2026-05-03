# Methodology Log

Use this file as a chronological research journal for the thesis implementation.

## Entry Template

### YYYY-MM-DD - Short title

- Objective:
- Action taken:
- Data used:
- Output created:
- What was learned:
- Why it matters for the thesis:
- Open questions:

## Entries

### 2026-05-01 - VOICE-008 local TTS smoke test

- Objective: test the next no-key audible-output path before integrating a real cloud TTS provider
- Action taken:
  - added a bilingual local TTS smoke runner for one German and one English campaign response
  - added a validator that checks both forced fallback and normal local TTS attempt modes
  - attempted Windows SAPI local TTS and recorded fallback behavior
  - ignored generated `VOICE-008` WAV files in Git because they depend on local machine voice availability
- Data used:
  - German telecom campaign response from the active `PROD-005` runtime campaign file
  - English B2B software campaign response from the same active runtime campaign file
  - existing `VOICE-001` voice packet contract and Windows SAPI helper
- Output created:
  - `scripts/run_voice_008_local_tts_smoke.py`
  - `scripts/validate_voice_008_local_tts_smoke.py`
  - `docs/product/VOICE_008_LOCAL_TTS_SMOKE_TEST.md`
  - `research/experiments/VOICE-008-local-tts-smoke-test.md`
  - `research/experiments/generated/VOICE-008-local-tts-smoke.json`
  - `research/experiments/generated/VOICE-008-local-tts-smoke-report.md`
- What was learned:
  - the local Windows SAPI command path can be attempted without API keys or cloud providers
  - the current environment does not have a usable local SAPI voice installed or allowed by the current security setting
  - the dry-run fallback remained safe for both German and English cases
  - local OS TTS should not be assumed as the reliable audible-output path for this project
- Why it matters for the thesis:
  - this checkpoint records a negative/partial result honestly instead of hiding it
  - it supports the methodological argument that voice integration is being developed through gated experiments and fallback validation
  - it gives a concrete reason to move from generic local TTS assumptions toward provider-specific TTS research
- Limitations:
  - no audible WAV files were produced in the current environment
  - no TTS naturalness, accent quality, or production latency was measured
  - the result is machine-dependent because local SAPI voice availability varies
- Open questions:
  - which concrete TTS provider or local voice engine should be evaluated first for German and English quality
  - whether the next checkpoint should prioritize cloud low-latency TTS research or installable local TTS engines
  - how much voice naturalness evaluation should be manual listening versus structured rubric scoring

### 2026-05-01 - VOICE-007 provider readiness gate

- Objective: decide the safe next path toward real ASR/TTS providers without introducing API keys, cloud audio upload, or uncontrolled provider dependencies
- Action taken:
  - added a deterministic ASR/TTS provider-readiness candidate file
  - implemented `scripts/evaluate_voice_provider_readiness.py`
  - added `scripts/validate_voice_007_provider_readiness.py` as the regression validator
  - generated JSON and Markdown readiness artifacts
  - documented the product checkpoint as `VOICE-007`
- Data used:
  - existing `VOICE-001` dry-run and Windows SAPI TTS path
  - existing `VOICE-002` manual transcript path
  - existing `VOICE-003` ASR provider-family comparison
  - existing `VOICE-004` browser speech recognition and synthesis demo
  - low-latency runtime target of roughly 1-2 seconds for first response
- Output created:
  - `research/experiments/cases/voice-007-provider-readiness-candidates.json`
  - `scripts/evaluate_voice_provider_readiness.py`
  - `scripts/validate_voice_007_provider_readiness.py`
  - `docs/product/VOICE_007_PROVIDER_READINESS_GATE.md`
  - `research/experiments/VOICE-007-provider-readiness-gate.md`
  - `research/experiments/generated/VOICE-007-provider-readiness.json`
  - `research/experiments/generated/VOICE-007-provider-readiness-report.md`
- What was learned:
  - the next safe no-key ASR path remains the browser speech recognition demo, with manual transcript as the regression baseline
  - the next safe no-key TTS path is local Windows SAPI, with dry-run TTS packets as the regression baseline
  - cloud streaming ASR and cloud low-latency TTS are production-relevant, but they must remain blocked until key management, privacy review, retention review, provider terms, and latency measurement are handled
  - cloned voice TTS is not needed for the thesis prototype and should stay blocked behind explicit voice consent and legal review
- Why it matters for the thesis:
  - this creates a defensible methodology step between browser/local prototypes and real cloud provider integration
  - it shows that provider selection is evaluated through safety, latency, bilingual support, fallback, and reproducibility constraints rather than convenience alone
- Limitations:
  - VOICE-007 scores provider classes, not specific vendors
  - no real latency, accuracy, naturalness, or German-language provider quality is measured yet
  - vendor-specific claims must be researched later before choosing a concrete provider
- Open questions:
  - whether `VOICE-008` should first test local Windows SAPI TTS audio generation or start vendor-specific provider research
  - what privacy and data-retention rules should be required before any real customer audio leaves the local environment
  - whether provider comparisons should eventually include cost estimates and German accent robustness

### 2026-05-01 - Active bilingual runtime backfill and debugging trail

- Objective: make the active voice/runtime experiments explicitly bilingual without turning the product into separate German and English products
- Action taken:
  - backfilled active runtime checks so `PROD-005`, `VOICE-001`, `VOICE-002`, `VOICE-004`, `VOICE-005`, and `VOICE-006` validate campaign-language and response-language alignment
  - kept the architecture as one reusable sales-agent core plus configurable `SalesCampaign` profiles
  - regenerated active runtime artifacts after the validators passed
  - committed and pushed the checkpoint as `a02149e Backfill active runtime experiments with bilingual language checks`
- Data used:
  - active synthetic runtime campaigns from `research/experiments/cases/prod-005-realtime-latency-call-control.json`
  - German B2C telecom runtime examples and English B2B software runtime examples
  - prior manual browser observations that English speech could be transcribed or handled as German when the selected language/campaign path was wrong
- Output created:
  - updated active runtime validators for language checks
  - updated generated artifacts for `PROD-005`, `VOICE-001`, `VOICE-002`, `VOICE-004`, `VOICE-005`, and `VOICE-006`
  - updated product and experiment docs for bilingual runtime behavior
- Problems encountered and fixes:
  - `VOICE-002` initially passed transcript text into the realtime core without passing the selected campaign, so the response could default to the wrong language. This was fixed by routing the campaign profile into `run_turn_decision`.
  - `VOICE-004` and `VOICE-006` exposed a mixed-language response problem where German output could include the English handoff role `telecom specialist`. This was fixed by using German-safe handoff wording in the guarded response composer.
  - `VOICE-005` contained a case labeled as German while the transcript itself was English. This was corrected so the German/English latency matrix is clean rather than only technically passing.
  - `VOICE-006` English interruption cases were being sent into the German telecom campaign when they reached the sales core. This was fixed by routing interruption cases through a campaign profile that matches the case language.
  - The project needed a clear boundary between active runtime backfill and archived historical artifacts. The fix was methodological rather than technical: update active runtime paths now, and only backfill archived experiments if they become active again.
- What was learned:
  - bilingual support should be an attribute of campaign configuration and runtime routing, not a fork into separate products
  - validators must check not only final labels but also runtime language fields and generated response language
  - generated artifacts can hide language-routing mistakes unless validators assert the campaign language, response language, and spoken text together
  - debugging failures are thesis-relevant evidence because they show how product constraints were discovered and converted into repeatable checks
- Why it matters for the thesis:
  - this checkpoint strengthens the methodology chapter by showing iterative prototype refinement, validation-driven development, and multilingual product generalization
  - the recorded bugs can later support an honest limitations/debugging section instead of presenting the final prototype as if it emerged fully correct
- Open questions:
  - whether later experiments should add a third language to prove the phrase-pack/campaign-language design generalizes beyond English and German
  - how much bilingual evaluation should use manual human review versus deterministic language assertions
  - whether the final thesis should present these debugging notes in the methodology chapter, results discussion, or appendix

### 2026-04-30 - Vertical-agnostic campaign model

- Objective: clarify that the product should support many call-center sales verticals, not only the first insurance client
- Action taken:
  - added a vertical-agnostic product model based on campaign configuration
  - documented that insurance is one early campaign type, not the product boundary
  - added `SalesCampaign` to the lead database design and SQLite schema
  - updated simulation export/import to include campaign metadata
- Data used:
  - student clarification that future clients may sell many products, such as windows, glasses, SD cards, services, insurance, or B2B offers
- Output created:
  - `docs/product/VERTICAL_AGNOSTIC_PRODUCT_MODEL.md`
  - updates to product brief, B2B/B2C scope, insurance context, lead database design, SQLite schema, and import/export scripts
- What was learned:
  - the right abstraction is a reusable sales-agent core plus campaign-specific scripts, claims, guardrails, and escalation triggers
  - sensitive verticals such as insurance need stricter campaign rules, but simpler products still use the same core loop
- Why it matters for the thesis:
  - it keeps the prototype general enough to demonstrate emotion-aware adaptation across product domains while preserving realistic product constraints
- Open questions:
  - which non-insurance product vertical should be used first for mixed-vertical simulation cases
  - how detailed the campaign configuration should be before a real client onboarding flow exists

### 2026-04-30 - First concrete B2C insurance client context

- Objective: record the first real client context more accurately
- Action taken:
  - documented that the first known client is a German call center selling consumer insurance products
  - recorded dental insurance and cancer-related or serious-illness insurance as example products
  - added insurance-specific guardrails and B2C qualification wording examples
  - updated the roadmap and product docs so the product is not framed as B2B-only
- Data used:
  - student-provided client context
  - current B2B/B2C product scope docs
- Output created:
  - `docs/product/INSURANCE_CLIENT_CONTEXT.md`
  - updates to product brief, client MVP workflow, qualification flow, B2B/B2C scope, and roadmap
- What was learned:
  - the first likely product vertical is sensitive B2C insurance sales rather than generic B2B lead qualification
  - future simulations need direct-consumer insurance cases and stronger pressure/privacy/compliance guardrails
- Why it matters for the thesis:
  - it grounds the product prototype in a realistic application while preserving a broader B2B/B2C product scope
- Open questions:
  - which exact insurance scripts and claims the client is legally allowed to use
  - what German outbound calling, insurance sales, privacy, and recording constraints must be verified before live use

### 2026-04-30 - B2B and B2C product scope clarification

- Objective: clarify that the product should support both company sales and direct-to-consumer sales
- Action taken:
  - documented B2B and B2C scope explicitly
  - updated product positioning to avoid implying that the agent only sells to companies
  - added B2B/B2C question variants for qualification
  - added `customer_type` to the lead database design and SQLite schema
- Data used:
  - product direction clarification from the student
  - current product MVP workflow and qualification flow
- Output created:
  - `docs/product/B2B_B2C_SCOPE.md`
  - updated product brief, client workflow, qualification flow, roadmap, database design, and SQLite import path
- What was learned:
  - `PROD-001` should be treated as a B2B-leaning first slice, not as the full product definition
  - future product simulation cases should include B2C customer conversations
- Why it matters for the thesis:
  - it prevents the integrated product prototype from being framed too narrowly and keeps the customer-state adaptation idea applicable across sales contexts
- Open questions:
  - which B2C domain should be used for the first direct-consumer simulation cases
  - whether B2C requires additional safety or consumer-protection guardrails beyond the current flow

### 2026-04-30 - Deterministic product rule baseline

- Objective: create a transparent baseline for the product qualification simulation before running a live model
- Action taken:
  - implemented `scripts/run_rule_baseline.py`
  - ran the rule baseline across all 12 `PROD-001` simulation cases
  - generated detailed JSON results and a markdown summary report
- Data used:
  - `research/experiments/cases/prod-001-qualification-simulation.json`
- Output created:
  - `scripts/run_rule_baseline.py`
  - `research/experiments/generated/PROD-001-rule-baseline-results.json`
  - `research/experiments/generated/PROD-001-rule-baseline-report.md`
  - `research/experiments/PROD-001-rule-baseline.md`
- What was learned:
  - transparent rules can match all final product outcomes in the current synthetic case set
  - the rule baseline still has weak emotion-label matching, which gives future model runs a meaningful improvement target
  - the product workflow is now testable without a live model
- Why it matters for the thesis:
  - it adds a clear non-LLM baseline for the product-oriented integrated prototype path
- Open questions:
  - whether a live model can improve emotion and response naturalness while preserving the same guardrail correctness
  - whether the case set is now too easy for rule-based state classification and needs harder edge cases

### 2026-04-29 - SQLite prototype import

- Objective: create the first local persistence layer for the product MVP simulation records
- Action taken:
  - added a SQLite schema for leads, call sessions, qualification answers, turn decisions, call outcomes, appointments, and escalations
  - implemented an importer that loads `PROD-001-db-records.json` into SQLite
  - generated a query report proving retrieval of interested leads, do-not-call leads, appointments, escalations, and turn-level decisions
- Data used:
  - `research/experiments/generated/PROD-001-db-records.json`
  - `docs/product/LEAD_DATABASE_DESIGN.md`
- Output created:
  - `db/sqlite_schema.sql`
  - `scripts/import_simulation_records.py`
  - `docs/product/SQLITE_PROTOTYPE.md`
  - `research/experiments/generated/PROD-001.sqlite`
  - `research/experiments/generated/PROD-001-sqlite-report.md`
- What was learned:
  - the synthetic simulation records fit cleanly into a relational schema
  - the current records support the product queries needed for the first MVP workflow
  - SQLite is sufficient for local prototype work before a production backend is needed
- Why it matters for the thesis:
  - it demonstrates a concrete logging and outcome-storage path for the integrated prototype
- Open questions:
  - whether future live model outputs should be stored alongside reference labels
  - how production privacy, retention, and access-control rules should be implemented

### 2026-04-29 - Database-shaped simulation export

- Objective: connect the product simulation runner to the lead database design without introducing a real database yet
- Action taken:
  - added an optional `--export-records` flag to `scripts/run_product_simulation.py`
  - exported synthetic reference records for leads, call sessions, qualification answers, turn decisions, call outcomes, appointments, and escalations
  - documented the export command in the lead database design
- Data used:
  - `research/experiments/cases/prod-001-qualification-simulation.json`
  - `docs/product/LEAD_DATABASE_DESIGN.md`
  - `docs/product/SIMULATION_CONTRACT.md`
- Output created:
  - `research/experiments/generated/PROD-001-db-records.json`
- What was learned:
  - the simulation artifacts can now be shaped like future product persistence records
  - appointment and escalation records can be derived cleanly from the final `CallOutcome`
- Why it matters for the thesis:
  - it makes the integrated prototype more concrete by linking state-aware conversation simulation to auditable outcome logging
- Open questions:
  - whether the first real persistence layer should be SQLite or Postgres
  - how much transcript text should be stored once real calls exist

### 2026-04-29 - Accumulated-state simulation runner

- Objective: prevent the product simulation runner from treating each customer turn as an isolated exchange
- Action taken:
  - updated the product qualification prompt to include accumulated call state
  - updated `scripts/run_product_simulation.py` to build state across prior turns
  - regenerated the evaluation packet so later turns include prior questions, answers, states, strategies, appointment status, escalation flags, and suppression status
- Data used:
  - `research/experiments/cases/prod-001-qualification-simulation.json`
  - `packages/prompts/product-qualification-agent.txt`
  - `docs/product/SIMULATION_CONTRACT.md`
- Output created:
  - updated `scripts/run_product_simulation.py`
  - updated `research/experiments/generated/PROD-001-evaluation-packet.md`
- What was learned:
  - the simulation prompt can now represent the current customer conversation more realistically
  - the runner is closer to the eventual product database model, where `CallSession` accumulates state across turns
- Why it matters for the thesis:
  - it improves the integrated prototype path by making state-aware strategy selection explicit at the turn level
- Open questions:
  - how to export accumulated-state runs into database-shaped JSON records
  - whether future live model execution should compare each candidate turn against reference labels automatically

### 2026-04-29 - Lead database design

- Objective: define how the product should store leads, qualification answers, turn decisions, call outcomes, appointments, and escalations
- Action taken:
  - created a product database design aligned with the simulation `CallOutcome` contract
  - defined core entities for lead identity, accumulated call state, per-turn answers, agent decisions, appointment records, and escalation records
  - documented privacy boundaries so real customer data is not committed to the repository
  - updated the simulation contract to require accumulated dialogue state in future runner revisions
- Data used:
  - `docs/product/CLIENT_MVP_WORKFLOW.md`
  - `docs/product/SIMULATION_CONTRACT.md`
  - `docs/data/DATA_USAGE_POLICY.md`
  - `research/experiments/PROD-001-first-simulation-pass.md`
- Output created:
  - `docs/product/LEAD_DATABASE_DESIGN.md`
- What was learned:
  - the database should preserve both final outcomes and the turn-level reasoning trail
  - the simulation runner should eventually export records in the same shape that the product database will persist
  - accumulated call state is necessary for realistic product behavior
- Why it matters for the thesis:
  - it strengthens the integrated prototype path by connecting emotion/state estimation, strategy selection, and product outcome logging
- Open questions:
  - which database technology to use for the first prototype
  - whether raw transcripts should be stored or replaced by summaries and structured answers
  - how long production call records should be retained

### 2026-04-29 - First product simulation dry run

- Objective: test the product simulation contract on representative qualification cases before live model execution
- Action taken:
  - selected three representative cases from `PROD-001`: happy-path scheduling, do-not-call, and privacy escalation
  - manually produced candidate final outcomes using the simulation contract and product qualification prompt
  - compared candidate outcomes against expected reference labels and guardrails
- Data used:
  - `research/experiments/cases/prod-001-qualification-simulation.json`
  - `research/experiments/generated/PROD-001-evaluation-packet.md`
  - `docs/product/SIMULATION_CONTRACT.md`
- Output created:
  - `research/experiments/PROD-001-first-simulation-pass.md`
- What was learned:
  - the current schema is usable for first-pass state, strategy, scheduling, and escalation evaluation
  - the prompt and runner should eventually include accumulated dialogue state rather than treating each turn mostly in isolation
  - the final `CallOutcome` fields are strong enough to inform the planned lead database design
- Why it matters for the thesis:
  - this gives the product-prototype workflow an initial evaluation trail while keeping the limitation clear that no live model was run yet
- Open questions:
  - whether the first live execution should use a model API or a deterministic rule engine
  - how to store future candidate outputs so they can feed directly into the product lead database

### 2026-04-28 - Product simulation contract and runner

- Objective: turn the product simulation case set into a runnable evaluation workflow
- Action taken:
  - defined the structured per-turn output and final `CallOutcome` contract
  - created a product qualification prompt with compact labels and guardrails
  - implemented a runner that validates the case set and renders prompts, reference outputs, candidate-output slots, and manual checks
- Data used:
  - `research/experiments/cases/prod-001-qualification-simulation.json`
  - `docs/product/CLIENT_MVP_WORKFLOW.md`
  - `docs/product/QUALIFICATION_QUESTION_FLOW.md`
- Output created:
  - `docs/product/SIMULATION_CONTRACT.md`
  - `packages/prompts/product-qualification-agent.txt`
  - `scripts/run_product_simulation.py`
  - `research/experiments/generated/PROD-001-evaluation-packet.md`
- What was learned:
  - the product track now has a repeatable evaluation packet analogous to the thesis prompt-comparison packet
  - the first runner can validate structure and create scoring slots without committing to a model API yet
- Why it matters for the thesis:
  - it creates a concrete integrated-prototype evaluation format where emotion, strategy, interest state, scheduling, and escalation can be checked together
- Open questions:
  - whether to run the first pass with an LLM manually, a local rule engine, or an API-backed script
  - how strict confidence and guardrail scoring should be in the first automated evaluator

### 2026-04-28 - First product MVP simulation case set

- Objective: create the first runnable product-track artifact for the autonomous qualification and appointment-setting workflow
- Action taken:
  - defined twelve turn-based lead scenarios covering interest, uncertainty, disinterest, do-not-call, escalation, referral, skepticism, scheduling failure, time pressure, no-budget rejection, human requests, and privacy concerns
  - represented each scenario as structured JSON with expected state, strategy, and `CallOutcome`
  - created a renderer script that turns the JSON cases into a readable simulation packet
- Data used:
  - `docs/product/CLIENT_MVP_WORKFLOW.md`
  - `docs/product/QUALIFICATION_QUESTION_FLOW.md`
  - compact emotion and strategy labels from the phase-1 baseline
- Output created:
  - `research/experiments/cases/prod-001-qualification-simulation.json`
  - `scripts/render_product_simulation.py`
  - `research/experiments/PROD-001-qualification-simulation.md`
  - `research/experiments/generated/PROD-001-simulation-packet.md`
- What was learned:
  - the product workflow can be tested before telephony or calendar integration by checking turn-level state estimates and final outcome records
  - scheduling needs a separate confirmation check because an interested lead is not always a scheduled lead
- Why it matters for the thesis:
  - it creates a concrete product-prototype setting where emotion-aware strategy selection can later be evaluated beyond isolated response generation
- Open questions:
  - whether the first product runner should be a CLI, API endpoint, or lightweight web demo
  - how to represent confidence scores and fallback reasons in the first structured agent output

### 2026-04-27 - Initial thesis project framing

- Objective: define a realistic starting scope for the thesis project
- Action taken: created a project brief, a data usage policy, a data readiness document, and a first experiment plan
- Data used: thesis proposal and project brief answers
- Output created:
  - `docs/thesis/PROJECT_BRIEF.md`
  - `docs/data/DATA_USAGE_POLICY.md`
  - `docs/data/DATA_READINESS.md`
  - `docs/thesis/FIRST_EXPERIMENT_PLAN.md`
- What was learned:
  - the thesis proposal is directional rather than a fixed implementation contract
  - the first phase should be public-data-first
  - the smallest believable system is a turn-based adaptive pipeline rather than a full production calling agent
- Why it matters for the thesis:
  - this establishes the initial scope, assumptions, and constraints that can later be described in the methodology chapter
- Open questions:
  - whether the downloaded IEMOCAP material is the official corpus or a derivative export
  - what exact label mappings should be used for the first experiment

### 2026-04-27 - Public dataset acquisition and inspection

- Objective: prepare the first public datasets for baseline work
- Action taken: organized downloaded public datasets, extracted `MELD` and `Persuasion for Good`, and inspected their basic local structure
- Data used:
  - `data/public/meld/`
  - `data/public/persuasion-for-good/`
  - `data/public/iemocap/`
- Output created:
  - `docs/data/DATASETS.md`
  - project `.gitignore` rules for raw and restricted data
- What was learned:
  - `MELD` is immediately usable for label and schema work
  - `Persuasion for Good` contains a useful annotated subset for persuasion labels
  - the current local `IEMOCAP` download does not look like the canonical audio corpus layout
- Why it matters for the thesis:
  - this explains why the first experiment will rely more heavily on `MELD` and `Persuasion for Good` than on `IEMOCAP`
- Open questions:
  - what reduced emotion taxonomy is most defensible for the first baseline
  - how to compress persuasion annotations into a compact strategy set

### 2026-04-27 - Phase-1 label mapping for emotion and persuasion

- Objective: define compact label spaces that support the first adaptive baseline
- Action taken:
  - inspected `MELD` emotion and sentiment distributions
  - inspected the annotated persuader labels in `Persuasion for Good`
  - created explicit mapping documents for both datasets
- Data used:
  - `data/public/meld/MELD-master/data/MELD/train_sent_emo.csv`
  - `data/public/persuasion-for-good/persuasionforgood-master/data/AnnotatedData/300_dialog.xlsx`
- Output created:
  - `docs/data/MELD_LABEL_MAPPING.md`
  - `docs/data/PERSUASION_LABEL_MAPPING.md`
- What was learned:
  - `MELD` is easier to use through its existing `Sentiment` field than through direct collapse of all raw emotion labels
  - `Persuasion for Good` supports a compact five-part persuasion taxonomy without losing the core strategic patterns
- Why it matters for the thesis:
  - this creates the first defensible bridge between emotional state and adaptive persuasive behavior
  - these mappings can be cited later in the methodology chapter as operational simplifications for the baseline system
- Open questions:
  - whether the compact strategy categories should later be expanded once real call-center data becomes available
  - how to design the first baseline comparison condition

### 2026-04-27 - First baseline comparison definition

- Objective: convert the first experiment idea into a concrete evaluation-ready baseline spec
- Action taken:
  - defined a non-adaptive baseline
  - defined an adaptive baseline with rule-based emotion-to-strategy mapping
  - documented the expected input, strategy space, output, and qualitative comparison logic
- Data used:
  - `docs/data/MELD_LABEL_MAPPING.md`
  - `docs/data/PERSUASION_LABEL_MAPPING.md`
- Output created:
  - `docs/thesis/BASELINE_SPEC.md`
- What was learned:
  - the thesis can start with a very interpretable adaptive comparison instead of pretending the full final agent already exists
  - a rule-based adaptive policy is strong enough to test the core thesis idea early
- Why it matters for the thesis:
  - this defines the first real baseline that can later be described in the methodology and evaluation chapters
- Open questions:
  - what exact prompt format or response-generation interface should be used
  - what the fairest initial qualitative evaluation rubric should be

### 2026-04-27 - Prompt and evaluation package for the first baseline

- Objective: convert the baseline spec into reusable prompt assets and a comparison workflow
- Action taken:
  - created non-adaptive and adaptive prompt templates
  - created a lightweight evaluation rubric
  - documented the workflow for generating and comparing paired responses
- Data used:
  - `docs/thesis/BASELINE_SPEC.md`
  - `docs/data/MELD_LABEL_MAPPING.md`
  - `docs/data/PERSUASION_LABEL_MAPPING.md`
- Output created:
  - `packages/prompts/baseline-non-adaptive.txt`
  - `packages/prompts/baseline-adaptive.txt`
  - `docs/thesis/EVALUATION_RUBRIC.md`
  - `docs/thesis/PROMPT_EVAL_WORKFLOW.md`
- What was learned:
  - the first experiment can be represented cleanly as paired prompt outputs plus rubric-based comparison
  - a simple text-response setup is enough to begin testing the adaptive thesis claim
- Why it matters for the thesis:
  - this creates a reusable experimental procedure that can be described in the methodology section and reused in early result reporting
- Open questions:
  - how many initial test cases should be created for the first pass
  - whether the first cases should be synthetic, dataset-derived, or mixed

### 2026-04-27 - First seed test-case set

- Objective: create the first runnable set of prompt-comparison inputs
- Action taken:
  - defined six curated cases covering `positive`, `neutral`, and `skeptical-or-negative`
  - paired each case with an adaptive strategy label and expected adaptive behavior
  - created the first planned experiment note using the existing experiment template
- Data used:
  - `docs/thesis/BASELINE_SPEC.md`
  - `docs/thesis/PROMPT_EVAL_WORKFLOW.md`
  - phase-1 compact emotion and strategy mappings
- Output created:
  - `research/experiments/EXP-001-phase1-prompt-baseline.md`
  - `research/experiments/EXP-001-case-pack.md`
- What was learned:
  - the first evaluation pass can begin without waiting on a more complex case-extraction pipeline
  - six cases are enough to exercise all three compact emotion states in a balanced first pass
- Why it matters for the thesis:
  - this creates the first concrete evaluation inputs that can later support side-by-side examples in the methodology and results sections
- Open questions:
  - whether the first run should be executed manually or scripted
  - when to introduce dataset-derived test cases

### 2026-04-27 - Collaboration and voice-analysis concept integration

- Objective: document how the sales-agent thesis can adapt the concept of modular voice analytics from a collaborator's thesis
- Action taken:
  - recorded the collaboration and attribution position
  - defined a sales-domain voice feature module concept
  - updated the project brief, thesis outline, and decision log
- Data used:
  - collaborator thesis proposal text
  - current sales-agent thesis scope and phase plan
- Output created:
  - `docs/thesis/COLLABORATION_NOTE.md`
  - `docs/architecture/VOICE_FEATURE_MODULE.md`
- What was learned:
  - the useful shared concept is modular interpretable voice-feature extraction, not the full creative-expression pipeline
  - this module fits naturally as a phase-2 extension after the text-based baseline is runnable
- Why it matters for the thesis:
  - it gives the project a stronger path toward multi-modal emotion awareness while keeping attribution clear and the thesis distinct
- Open questions:
  - which public audio dataset should support the first voice-feature experiment
  - whether the voice module should be evaluated as text-only vs text-plus-voice adaptation

### 2026-04-27 - Supervisor-approved AI usage documentation

- Objective: record the allowed role of AI in the technical development workflow
- Action taken:
  - documented supervisor-approved AI usage for the technical part of the thesis
  - clarified the boundary between AI-assisted engineering support and final thesis authorship responsibility
- Data used:
  - supervisor guidance provided by the student
- Output created:
  - `docs/thesis/AI_USAGE_NOTE.md`
- What was learned:
  - the technical workflow can openly incorporate AI assistance without ambiguity because supervisor permission is explicit
- Why it matters for the thesis:
  - this creates a transparent process record that can be reused later in an appendix, methodology note, or defense context
- Open questions:
  - whether the final thesis should mention this in the methodology chapter, an appendix, or both

### 2026-04-27 - First prompt baseline execution

- Objective: run the first paired-response comparison for the phase-1 baseline
- Action taken:
  - generated non-adaptive and adaptive responses for six curated cases
  - scored each pair with the shared qualitative rubric
  - summarized aggregate preference and average scores
- Data used:
  - `research/experiments/EXP-001-case-pack.md`
  - `packages/prompts/baseline-non-adaptive.txt`
  - `packages/prompts/baseline-adaptive.txt`
  - `docs/thesis/EVALUATION_RUBRIC.md`
- Output created:
  - updated `research/experiments/EXP-001-phase1-prompt-baseline.md` with full case results
- What was learned:
  - the adaptive baseline consistently outperformed the non-adaptive baseline in the first six seed cases
  - the largest gains appeared in emotional appropriateness and strategy coherence
  - skeptical cases benefited most strongly from shifting from explanation to inquiry
- Why it matters for the thesis:
  - this is the first concrete result supporting the core thesis claim that emotion-aware adaptation can improve persuasive response behavior
- Open questions:
  - how robust this result remains on dataset-derived cases
  - whether a scripted execution path should be built next for repeatability

### 2026-04-27 - Dataset-derived prompt baseline execution

- Objective: test whether the adaptive advantage remains when cases are grounded in public dataset patterns
- Action taken:
  - created a dataset-derived, domain-adapted case pack grounded in `MELD` emotional patterns and `Persuasion for Good` strategy patterns
  - generated non-adaptive and adaptive responses for six derived cases
  - scored each pair with the shared qualitative rubric
- Data used:
  - `data/public/meld/MELD-master/data/MELD/train_sent_emo.csv`
  - `data/public/persuasion-for-good/persuasionforgood-master/data/AnnotatedData/300_dialog.xlsx`
  - `research/experiments/EXP-002-dataset-derived-case-pack.md`
  - prompt templates and rubric
- Output created:
  - `research/experiments/EXP-002-dataset-derived-case-pack.md`
  - `research/experiments/EXP-002-dataset-derived-baseline.md`
- What was learned:
  - the adaptive baseline remained preferred across all six dataset-derived cases
  - the strongest gains again appeared in emotional appropriateness and strategy coherence
  - dataset grounding did not erase the basic adaptive advantage observed in the first seed experiment
- Why it matters for the thesis:
  - this provides a more defensible step between synthetic examples and a future larger-scale evaluation
- Open questions:
  - how to automate prompt execution and scoring support
  - how to extract larger case sets with less manual adaptation

### 2026-04-27 - Repeatable prompt execution workflow

- Objective: replace one-off manual prompt assembly with a repeatable packet-generation workflow
- Action taken:
  - created structured JSON versions of the first two case sets
  - implemented a small runner script that renders both prompt templates for every case
  - generated a reusable markdown packet for the dataset-derived case set
- Data used:
  - `research/experiments/cases/exp-001-seed.json`
  - `research/experiments/cases/exp-002-dataset-derived.json`
  - baseline prompt templates
- Output created:
  - `scripts/run_prompt_baseline.py`
  - `research/experiments/generated/EXP-002-prompt-packet.md`
- What was learned:
  - the workflow can be made more repeatable without committing to a heavy automation stack
  - structured case files are a better long-term format than prompt-only markdown when experiments need to scale
- Why it matters for the thesis:
  - this improves methodological consistency and makes later experiment replication easier to explain
- Open questions:
  - whether to add semi-structured score capture next
  - whether to generate future experiment notes from the structured case files as well

### 2026-04-27 - Product qualification flow definition

- Objective: turn the product direction into a concrete lead-qualification workflow artifact
- Action taken:
  - defined the first qualification-question flow for the autonomous client MVP
  - specified the target outcome states
  - documented what counts as `interested`, `maybe-interested`, `not-interested`, `needs-human`, and `do-not-call`
  - defined scheduling and escalation triggers
- Data used:
  - `docs/product/PRODUCT_BRIEF.md`
  - `docs/product/CLIENT_MVP_WORKFLOW.md`
  - `docs/product/SALES_EXPERT_FEEDBACK.md`
- Output created:
  - `docs/product/QUALIFICATION_QUESTION_FLOW.md`
- What was learned:
  - the product scope becomes much clearer when qualification and scheduling are treated as the first real job rather than general autonomous selling
  - a small stable question skeleton is a better first product artifact than an open-ended conversation spec
- Why it matters for the thesis:
  - it creates a concrete downstream workflow where the emotion-aware adaptation logic can be applied and later evaluated
- Open questions:
  - how strict the qualification rules should be before expert review data exists
  - how calendar availability and scheduling confirmation should be represented in the first simulation

### 2026-04-27 - Product direction added as a first-class constraint

- Objective: update the project framing to reflect that this work is also intended to become a sellable client product
- Action taken:
  - created a product brief
  - updated the project brief, roadmap, README, thesis outline, and decision log
  - added a product MVP track focused on a constrained client-usable workflow that was later clarified further
- Data used:
  - student clarification that a client is ready to buy when the product launches
  - current roadmap and thesis baseline results
- Output created:
  - `docs/product/PRODUCT_BRIEF.md`
- What was learned:
  - the project should not be treated as thesis-only
  - product constraints need to be captured early even before the launch autonomy boundary is finalized
- Why it matters for the thesis:
  - product constraints make the research more grounded and help define realistic prototype boundaries
- Open questions:
  - what exact workflow the ready client needs first
  - whether the first product surface should be CLI, dashboard, or lightweight web app
  - which product claims will be defensible after the next evaluation phase

### 2026-04-27 - Autonomous launch target and sales-expert feedback loop

- Objective: correct the product framing from human-in-the-loop assistant to autonomous agent with fallback, and define how sales experts can train the agent during development
- Action taken:
  - updated product and thesis docs to use autonomous launch target with fallback/escalation guardrails
  - added a sales-expert feedback concept for ratings, rewrites, labels, and strategy corrections
  - documented a first feedback record schema
- Data used:
  - student clarification that the launch product should be completely autonomous
  - student clarification that experienced salespeople can train the agent during development
- Output created:
  - `docs/product/SALES_EXPERT_FEEDBACK.md`
- What was learned:
  - the product should not be framed as a permanent copilot or review-required tool
  - expert feedback is the most practical near-term path toward agent learning before any fine-tuning
- Why it matters for the thesis:
  - it creates a bridge between controlled academic experiments and a realistic product-learning loop
- Open questions:
  - how many sales experts can participate
  - what feedback interface they should use first
  - when feedback should become retrieval examples versus training data

### 2026-04-27 - Client MVP narrowed to qualification and appointment setting

- Objective: align the product track with the client's actual first requested use case
- Action taken:
  - documented the first client product as an autonomous lead-qualification and appointment-setting agent
  - added a concrete client MVP workflow
  - updated product, roadmap, project brief, and decision docs
- Data used:
  - student-provided client context
- Output created:
  - `docs/product/CLIENT_MVP_WORKFLOW.md`
- What was learned:
  - the first product is narrower than a full autonomous sales closer
  - the agent should ask qualification questions and schedule human follow-up when interest is detected
  - scheduling and call outcome logging are core product requirements
- Why it matters for the thesis:
  - the thesis adaptation logic can be evaluated in a realistic qualification context rather than a vague sales conversation
- Open questions:
  - what exact qualification questions the client wants
  - what scheduling system or calendar source should be used
  - what counts as enough interest to trigger human follow-up

### 2026-04-27 - Roadmap consolidation

- Objective: create a single steering document for the thesis project
- Action taken:
  - consolidated the phase plan into a dedicated roadmap
  - linked the roadmap from the project README and thesis outline
  - cleaned up the README current-focus section
- Data used:
  - `PROJECT_BRIEF.md`
  - `FIRST_EXPERIMENT_PLAN.md`
  - `METHODOLOGY_LOG.md`
  - completed experiment notes
- Output created:
  - `docs/thesis/ROADMAP.md`
- What was learned:
  - the project has moved beyond initial scoping and now needs one visible source of direction
- Why it matters for the thesis:
  - the roadmap gives the thesis work a clear sequence from text baseline to dataset expansion, voice features, prototype integration, and writing support
- Open questions:
  - how detailed the repeatable prompt-execution workflow should be before implementation begins

### 2026-04-30 - Campaign wrapper simulation expansion

- Objective: prove the product simulation runner can support multiple SalesCampaign profiles while keeping one reusable agent core
- Action taken:
  - added the strict B2C insurance campaign as `PROD-002`
  - extended the runner to accept campaign wrappers with one or many campaign profiles
  - added a mixed consumer/B2B campaign set as `PROD-003`
  - generated evaluation packets, database-shaped exports, SQLite imports, and reports for both new campaign sets
- Data used:
  - clarified product architecture for a reusable core plus configurable SalesCampaign profiles
  - synthetic campaign scenarios for windows, glasses, SD cards, and B2B workflow software
- Output created:
  - `research/experiments/PROD-002-b2c-insurance-simulation.md`
  - `research/experiments/PROD-003-mixed-campaigns-simulation.md`
- What was learned:
  - the same runner can handle both a single sensitive vertical and a mixed multi-campaign product set
  - campaign-specific guardrails belong in the wrapper, not in the reusable core
- Why it matters for the thesis:
  - the product evidence now supports the claim that the agent architecture is vertical-agnostic rather than insurance-specific
- Open questions:
  - whether future campaign libraries should be versioned separately from experiment case files
  - how much of the campaign configuration should eventually move into reusable templates

### 2026-04-30 - Sales difficulty gauntlet added

- Objective: prioritize transferable sales skill before broad industry expansion
- Action taken:
  - defined a reusable sales difficulty taxonomy
  - added `PROD-004` as a multi-campaign objection and edge-case gauntlet
  - generated an evaluation packet, database-shaped export, SQLite import, and report
- Data used:
  - public sales-objection category patterns from Apollo, Salesgenie, Proposify, and B2B Vic
  - synthetic cases rewritten for this project
- Output created:
  - `docs/product/SALES_DIFFICULTY_TAXONOMY.md`
  - `research/experiments/PROD-004-sales-difficulty-gauntlet.md`
- What was learned:
  - the agent should first be evaluated on universal sales difficulties such as price, timing, authority, trust, status quo, fit risk, competitor comparison, and claim boundaries
  - industry breadth is still important, but it should build on stronger sales behavior rather than replace it
- Why it matters for the thesis:
  - this creates a more realistic product evaluation layer for emotion-aware strategy selection under resistance
- Open questions:
  - how the rule baseline performs on the harder difficulty set
  - whether the LLM agent improves naturalness and emotion handling without weakening guardrails

### 2026-04-30 - PROD-004 rule baseline

- Objective: test the deterministic rule baseline against the harder sales difficulty gauntlet
- Action taken:
  - updated the rule baseline runner to load campaign-wrapper case files
  - ran the baseline on all 14 `PROD-004` cases
  - documented aggregate results and interpretation
- Data used:
  - `research/experiments/cases/prod-004-sales-difficulty-gauntlet.json`
- Output created:
  - `research/experiments/PROD-004-rule-baseline.md`
  - `research/experiments/generated/PROD-004-rule-baseline-results.json`
  - `research/experiments/generated/PROD-004-rule-baseline-report.md`
- What was learned:
  - the baseline preserved appointment caution with 14 / 14 final appointment matches
  - the baseline was much weaker on hard sales boundaries, with 6 / 14 final call-status matches and 7 / 14 final interest-state matches
  - common misses include competitor comparisons, guarantee requests, human requests, authority gaps, and annoyance handling
- Why it matters for the thesis:
  - `PROD-004` creates a more meaningful benchmark for showing improvement from a stronger LLM or learned agent
- Open questions:
  - whether to improve the transparent rule baseline first or use it as-is as a deliberately weak control
  - how much the next LLM agent should be allowed to use campaign context versus generic sales-difficulty patterns

### 2026-05-01 - VOICE-009 TTS provider research checkpoint

- Objective: choose the first real TTS integration candidate without introducing API keys, SDK calls, or audio uploads
- Action taken:
  - added a vendor-specific TTS provider research matrix
  - added an evaluator and validator for the VOICE-009 checkpoint
  - generated JSON and Markdown evidence from official/primary sources
  - documented the product recommendation and thesis interpretation
- Data used:
  - official/primary sources from Cartesia, ElevenLabs, OpenAI, Microsoft Azure, Google Cloud, AWS, Deepgram, and Piper/OHF GitHub
  - source retrieval date: 2026-05-01
- Output created:
  - `docs/product/VOICE_009_TTS_PROVIDER_RESEARCH.md`
  - `research/experiments/VOICE-009-tts-provider-research.md`
  - `research/experiments/cases/voice-009-tts-provider-research.json`
  - `research/experiments/generated/VOICE-009-tts-provider-research.json`
  - `research/experiments/generated/VOICE-009-tts-provider-research-report.md`
  - `scripts/evaluate_voice_009_tts_provider_research.py`
  - `scripts/validate_voice_009_tts_provider_research.py`
- What was learned:
  - Cartesia Sonic 3 is the best first TTS pilot candidate for the bilingual voice-agent path
  - ElevenLabs Flash v2.5 is a strong quality/latency alternate
  - OpenAI TTS is attractive if stack simplicity matters more than specialized TTS focus
  - Deepgram Aura should not be integrated first because German TTS support was not confirmed in the official source checked
  - Piper remains useful as a privacy/offline research lane, but needs local runtime, license, German quality, and telephony checks
- Error or risk recorded:
  - VOICE-008 showed local Windows SAPI can fail safely when no usable local voice is installed or allowed
  - VOICE-009 avoided the mistake of jumping directly from that local failure to a cloud SDK integration with an API key
  - provider claims were documented as research inputs, not as measured workspace performance
- Why it matters for the thesis:
  - the voice layer now has a documented evidence-based provider-selection step
  - the next voice experiment can measure latency and audio quality without confusing provider selection with product architecture
- Open questions:
  - whether Cartesia's measured latency in this workspace stays inside the live-call budget
  - which neutral synthetic voice should be used first
  - what provider text-retention and data-processing terms mean for German call-center use
  - whether local Piper should be evaluated after or in parallel with the first cloud TTS smoke test

### 2026-05-01 - VOICE-010 Cartesia no-key smoke harness

- Objective: prepare the first Cartesia-specific TTS smoke test without storing or using an API key yet
- Action taken:
  - added a Cartesia Sonic 3 bytes-endpoint smoke runner
  - added a validator that checks dry-run and simulated missing-key live fallback paths
  - added a Cartesia-specific case file with one German and one English synthetic runtime case
  - generated dry-run JSON and Markdown artifacts
  - ignored generated VOICE-010 audio files in Git
- Data used:
  - existing `PROD-005` bilingual runtime campaigns
  - Cartesia official docs for the TTS bytes endpoint, WebSocket endpoint, and endpoint comparison
- Output created:
  - `docs/product/VOICE_010_CARTESIA_TTS_SMOKE_TEST.md`
  - `research/experiments/VOICE-010-cartesia-tts-smoke.md`
  - `research/experiments/cases/voice-010-cartesia-tts-smoke.json`
  - `research/experiments/generated/VOICE-010-cartesia-tts-smoke.json`
  - `research/experiments/generated/VOICE-010-cartesia-tts-smoke-report.md`
  - `scripts/run_voice_010_cartesia_tts_smoke.py`
  - `scripts/validate_voice_010_cartesia_tts_smoke.py`
- What was learned:
  - the provider adapter can be prepared safely before introducing any secret
  - a real Cartesia run needs both `CARTESIA_API_KEY` and `CARTESIA_VOICE_ID`
  - the default command should not call a provider even if an environment key exists
  - the first provider test should use bounded HTTP timeouts before moving to WebSocket streaming
- Error or risk recorded:
  - earlier long-attached shell calls made timeout guardrails mandatory for provider smoke tests
  - API key leakage remains the highest operational risk, so the script redacts authorization and voice identifiers from outputs
  - voice ID selection is now explicit because using an arbitrary example voice could distort German-quality evaluation
- Why it matters for the thesis:
  - it separates provider integration safety from provider quality evaluation
  - it preserves reproducibility by allowing no-key validation before a live cloud experiment
- Open questions:
  - which Cartesia voice ID should be selected for the first live German/English test
  - whether one voice should be used for both languages or separate voices should be compared later
  - whether measured first-audio timing will meet the `500 ms` TTS-start target
  - whether Cartesia quality is strong enough or ElevenLabs should become the next comparison provider

### 2026-05-01 - VOICE-010 live Cartesia bytes smoke result

- Objective: preserve the first live Cartesia TTS result without committing secrets or machine-local audio files
- Action taken:
  - ran the guarded Cartesia bytes-endpoint smoke test with local environment variables
  - deleted the exposed Cartesia key from the Cartesia dashboard after it had been pasted into chat
  - confirmed the generated JSON and Markdown did not contain secret-like tokens
  - kept generated WAV files ignored by Git
  - recorded the first listening impression
- Data used:
  - `research/experiments/generated/VOICE-010-cartesia-tts-smoke.json`
  - `research/experiments/generated/VOICE-010-cartesia-tts-smoke-report.md`
  - user listening feedback on the two generated WAV files
- Output updated:
  - `docs/product/VOICE_010_CARTESIA_TTS_SMOKE_TEST.md`
  - `research/experiments/VOICE-010-cartesia-tts-smoke.md`
  - `research/experiments/generated/VOICE-010-cartesia-tts-smoke.json`
  - `research/experiments/generated/VOICE-010-cartesia-tts-smoke-report.md`
- What was learned:
  - both Cartesia bytes-endpoint calls returned HTTP `200`
  - both German and English WAV files were created locally
  - English time to first audio byte was `366.492 ms`, which met the `500 ms` TTS-start target
  - German time to first audio byte was `1083.043 ms`, which did not meet the `500 ms` TTS-start target
  - first listening impression was acceptable but weak because the clips were short
- Error or risk recorded:
  - the API key was pasted into chat and had to be deleted from Cartesia before continuing
  - this reinforces the need for prompt-based local key entry and immediate key cleanup
  - bytes-endpoint latency should not be overgeneralized to WebSocket streaming latency
  - the first validator design reused the canonical output paths and overwrote live metadata during verification
  - the validator was corrected to write to `.tmp` validation artifacts so future safety checks do not erase live results
- Why it matters for the thesis:
  - this creates the first real cloud TTS measurement for the prototype
  - it shows that provider selection must consider language-specific latency, not only average provider claims
  - it creates a concrete rationale for a WebSocket streaming follow-up experiment
- Open questions:
  - whether Cartesia WebSocket streaming improves German first-audio timing
  - whether longer German and English sales responses preserve acceptable voice quality
  - whether ElevenLabs should be tested as a comparison if Cartesia WebSocket latency or quality is insufficient

### 2026-05-01 - VOICE-010 German voice-ID rerun

- Objective: test whether the weaker German audio result was caused by using an English-oriented Cartesia voice ID
- Action taken:
  - reran the guarded Cartesia bytes-endpoint smoke test with a German-suitable voice ID
  - confirmed the generated JSON and Markdown did not contain secret-like tokens
  - kept generated WAV files ignored by Git
  - compared the rerun against the first live VOICE-010 result
- Data used:
  - `research/experiments/generated/VOICE-010-cartesia-tts-smoke.json`
  - `research/experiments/generated/VOICE-010-cartesia-tts-smoke-report.md`
  - user listening feedback on the German rerun
- What was learned:
  - both Cartesia bytes-endpoint calls again returned HTTP `200`
  - both German and English WAV files were created locally
  - German time to first audio byte improved from `1083.043 ms` to `1035.629 ms`
  - German total provider latency improved from `2532.073 ms` to `2411.314 ms`
  - English time to first audio byte changed from `366.492 ms` to `347.719 ms`
  - English total provider latency changed from `1499.783 ms` to `1504.563 ms`
  - the German voice sounded better than the first run, but still sounded a little muffled
- Error or risk recorded:
  - a language-inappropriate voice ID can make a provider look worse than it may actually be
  - short audio clips are not enough for a reliable voice-quality judgment
  - bytes-endpoint German latency is still above the `500 ms` TTS-start target even with a better German voice
- Why it matters for the thesis:
  - the experiment shows that voice selection is part of the system configuration, not a neutral implementation detail
  - it supports separating provider evaluation into voice fit, language fit, endpoint type, and latency
- Open questions:
  - whether Cartesia WebSocket streaming reduces German first-audio timing enough for live calls
  - whether longer German samples still sound muffled
  - whether a different German Cartesia voice performs better
  - whether ElevenLabs gives stronger German quality or latency for the same sales-agent text

### 2026-05-02 - VOICE-011 Cartesia WebSocket dry-run harness

- Objective: prepare a WebSocket-based Cartesia TTS test for longer German and English samples without requiring a live provider key yet
- Action taken:
  - added a Cartesia Sonic 3 WebSocket smoke runner
  - added a validator that checks dry-run and simulated missing-key live fallback paths
  - added four longer synthetic quality samples, two German and two English
  - added language-specific voice ID support through `CARTESIA_VOICE_ID_DE` and `CARTESIA_VOICE_ID_EN`, with `CARTESIA_VOICE_ID` as a fallback
  - generated dry-run JSON and Markdown artifacts
  - ignored generated VOICE-011 WAV files in Git
- Data used:
  - existing `PROD-005` bilingual runtime campaigns
  - official Cartesia WebSocket, realtime TTS quickstart, endpoint-comparison, and Sonic 3 documentation
- Output created:
  - `docs/product/VOICE_011_CARTESIA_WEBSOCKET_SMOKE_TEST.md`
  - `research/experiments/VOICE-011-cartesia-websocket-smoke.md`
  - `research/experiments/cases/voice-011-cartesia-websocket-smoke.json`
  - `research/experiments/generated/VOICE-011-cartesia-websocket-smoke.json`
  - `research/experiments/generated/VOICE-011-cartesia-websocket-smoke-report.md`
  - `scripts/run_voice_011_cartesia_websocket_smoke.py`
  - `scripts/validate_voice_011_cartesia_websocket_smoke.py`
- What was learned:
  - audio-quality comparison cannot be done honestly without generated audio and human listening review
  - the WebSocket harness can still be validated safely before a live key is available
  - language-specific voice IDs are important enough to be first-class environment gates
  - provider timing and provider quality should be recorded separately
- Error or risk recorded:
  - WebSocket integration creates a new secret-handling surface, so request previews redact `X-API-Key` and voice IDs
  - generated WAV files remain machine-local and ignored
  - longer German scripts need real German characters for pronunciation testing, even though most project files stay ASCII by default
  - dry-run reports must not claim naturalness, clarity, or muffling results
- Why it matters for the thesis:
  - it preserves the low-latency voice-agent research path while keeping provider integration safe and reproducible
  - it documents that timing metrics can be automated, but perceptual voice quality requires human evaluation
- Open questions:
  - whether Cartesia WebSocket first-audio timing meets the `500 ms` target
  - whether longer German audio still sounds muffled
  - whether separate German and English voice IDs are enough, or multiple voices per language should be compared
  - whether ElevenLabs should be tested next if Cartesia WebSocket quality or latency is weak

### 2026-05-02 - VOICE-011 live Cartesia WebSocket result

- Objective: measure live WebSocket TTS timing for longer German and English synthetic sales-agent responses
- Action taken:
  - ran the guarded Cartesia WebSocket smoke harness with explicit live opt-in
  - used language-specific German and English voice IDs through environment variables
  - generated four local WAV files, two German and two English
  - verified that generated JSON/Markdown artifacts did not contain API key or voice ID values
  - confirmed the shell no longer had Cartesia environment variables set after the run
- Data used:
  - `research/experiments/generated/VOICE-011-cartesia-websocket-smoke.json`
  - `research/experiments/generated/VOICE-011-cartesia-websocket-smoke-report.md`
  - user listening feedback on the longer generated audio
- What was learned:
  - all four WebSocket calls produced audio files
  - max connection-established timing was `251.277 ms`
  - max time to first audio chunk was `417.445 ms`, which fits the `500 ms` TTS-start target
  - max total stream latency was `4580.398 ms`
  - the audio sounded decent but still recognizably AI-generated
- Error or risk recorded:
  - the live-artifact state and shell environment state can differ, so conclusions should be based on generated artifacts plus explicit secret scans, not memory of a terminal session
  - timing can be measured automatically, but human-like voice quality still requires listening review
  - provider quality alone is not enough; the text sent to TTS also affects whether the agent sounds human
- Why it matters for the thesis:
  - this creates a measured low-latency WebSocket TTS result
  - it motivates a separate speech-naturalness layer before provider comparison continues
- Open questions:
  - whether adding controlled mid-utterance fillers improves perceived human-likeness
  - whether fillers help or hurt trust in regulated product categories
  - whether the same naturalness profile should be used for German and English campaigns

### 2026-05-02 - VOICE-012 segment-aware speech naturalness

- Objective: make voice-agent speech less machine-perfect without corrupting scripted campaign questions or compliance-sensitive statements
- Action taken:
  - added a reusable `scripts/speech_naturalness.py` renderer
  - added `VOICE-012` bilingual cases for English and German freeform speech, scripted qualification questions, disclosures, strict insurance boundaries, do-not-call, hang-up, appointment confirmation, and disabled clean-script profiles
  - generated JSON and Markdown artifacts for the speech naturalness layer
  - added a validator that proves fillers stay out of protected segments
- Data used:
  - user feedback that VOICE-011 sounded decent but obviously AI-generated
  - product rule that the first MVP may need to ask a fixed set of client-provided qualification questions
  - existing campaign-profile architecture
- Output created:
  - `docs/product/VOICE_012_SPEECH_NATURALNESS_LAYER.md`
  - `research/experiments/VOICE-012-speech-naturalness.md`
  - `research/experiments/cases/voice-012-speech-naturalness.json`
  - `research/experiments/generated/VOICE-012-speech-naturalness.json`
  - `research/experiments/generated/VOICE-012-speech-naturalness-report.md`
  - `scripts/speech_naturalness.py`
  - `scripts/run_voice_012_speech_naturalness.py`
  - `scripts/validate_voice_012_speech_naturalness.py`
- What was learned:
  - humanization must be segment-aware, not a global text rewrite
  - freeform empathy, transitions, and objection handling can safely receive rare fillers
  - campaign qualification questions, disclosures, strict insurance boundaries, do-not-call, hang-up, and appointment-confirmation text should remain exact
  - casual fillers such as `you know` can exist, but they need contextual checks so they do not weaken meaning
- Error or risk recorded:
  - an early renderer produced awkward punctuation in German (`also, , dass`), showing why naturalness needs validation, not vibes
  - a casual English filler selected in a meaning-sensitive slot could weaken the response, so the renderer now contextually prefers safer hesitation sounds before `that` / `dass`
  - a validator assertion had an error-message bug that tried to inspect a missing secret-match object; the validator was fixed and rerun
- Why it matters for the thesis:
  - this gives the project a concrete design for human-like voice delivery that still respects compliance and campaign source-of-truth boundaries
  - it supports the broader product claim that the agent is campaign-configurable rather than hard-coded for one vertical
- Open questions:
  - whether VOICE-012 text improves perceived audio naturalness once synthesized through Cartesia or another provider
  - whether different campaigns should use `clean`, `warm-professional`, `casual`, or `strict-regulated` naturalness profiles
  - how sales experts should rate filler frequency and trustworthiness

### 2026-05-02 - VOICE-013 ElevenLabs no-key streaming TTS harness

- Objective: prepare a safe ElevenLabs provider test so Cartesia can be compared against a second high-quality voice candidate
- Action taken:
  - reviewed current ElevenLabs streaming, WebSocket, and latency documentation
  - selected HTTP streaming as the first ElevenLabs smoke path because the test scripts are available upfront
  - added a guarded ElevenLabs TTS runner with explicit `--live` opt-in
  - added language-specific voice ID support through `ELEVENLABS_VOICE_ID_DE` and `ELEVENLABS_VOICE_ID_EN`, with `ELEVENLABS_VOICE_ID` as a fallback
  - generated dry-run JSON and Markdown artifacts
  - ignored generated VOICE-013 MP3 files in Git
  - added a validator that checks dry-run and simulated missing-key live fallback paths
- Data used:
  - existing `PROD-005` bilingual runtime campaigns
  - the same longer synthetic scripts used for `VOICE-011`
  - official ElevenLabs docs for stream speech, WebSocket, and latency
- Output created:
  - `docs/product/VOICE_013_ELEVENLABS_TTS_SMOKE_TEST.md`
  - `research/experiments/VOICE-013-elevenlabs-tts-smoke.md`
  - `research/experiments/cases/voice-013-elevenlabs-tts-smoke.json`
  - `research/experiments/generated/VOICE-013-elevenlabs-tts-smoke.json`
  - `research/experiments/generated/VOICE-013-elevenlabs-tts-smoke-report.md`
  - `scripts/run_voice_013_elevenlabs_tts_smoke.py`
  - `scripts/validate_voice_013_elevenlabs_tts_smoke.py`
- What was learned:
  - the ElevenLabs adapter can be prepared safely without a key
  - provider comparison should use identical scripts before testing naturalized VOICE-012 variants
  - dry-run request previews should still show language-specific voice env gates, even when no voice IDs are present
  - ElevenLabs has a privacy-related `enable_logging=false` option, but live behavior may depend on account plan support
- Error or risk recorded:
  - the first dry-run preview fell back to generic `ELEVENLABS_VOICE_ID` when no env vars were set, which made setup less clear
  - the resolver was changed so missing language-specific voices still report `ELEVENLABS_VOICE_ID_DE` or `ELEVENLABS_VOICE_ID_EN`; generic fallback is used only when that env var actually exists
  - `enable_logging=false` may fail for non-enterprise accounts, so a live provider error should be recorded rather than silently switching to provider logging
- Why it matters for the thesis:
  - this creates a second provider path for a more credible voice-quality comparison
  - it preserves the research discipline of separating provider adapter safety from live provider quality claims
- Open questions:
  - whether ElevenLabs accepts the privacy-oriented live request on the available account
  - whether ElevenLabs German quality sounds more natural than Cartesia for the same script
  - whether ElevenLabs latency meets the `500 ms` first-audio target from this local environment

### 2026-05-02 - VOICE-013 first live ElevenLabs attempt

- Objective: run the guarded ElevenLabs streaming TTS harness with local environment-only key and voice IDs
- Action taken:
  - ran `VOICE-013` with explicit `--live`
  - confirmed four provider API calls were attempted
  - confirmed no customer audio was uploaded
  - confirmed no API key or voice ID values were present in generated artifacts
  - removed provider request IDs from stored error bodies while keeping the useful error category and message
- Data used:
  - `research/experiments/generated/VOICE-013-elevenlabs-tts-smoke.json`
  - `research/experiments/generated/VOICE-013-elevenlabs-tts-smoke-report.md`
- What was learned:
  - ElevenLabs returned HTTP `402` for all four cases
  - provider error code was `paid_plan_required`
  - provider message stated that free users cannot use library voices via the API
  - no MP3 files were created, so no ElevenLabs audio-quality comparison can be made from this attempt
  - max recorded provider error latency was `1635.438 ms`, but this is not a valid first-audio latency because no audio was returned
- Error or risk recorded:
  - a provider may be technically integrated but blocked by account/plan/voice licensing constraints
  - request IDs are useful for provider support but do not need to be committed in research artifacts
  - provider-business-rule failures should be recorded separately from latency or quality failures
- Why it matters for the thesis:
  - this is evidence that provider selection includes operational/account constraints, not only model quality
  - it reinforces the safe-fallback architecture: the system made no customer-audio upload and fell back when provider audio was unavailable
- Open questions:
  - whether a paid-compatible ElevenLabs plan or permitted voice ID resolves the block
  - whether `enable_logging=false` remains accepted once the account/voice issue is resolved
  - whether ElevenLabs quality is meaningfully better than Cartesia when audio can be generated

### 2026-05-02 - VOICE-013 successful live ElevenLabs run

- Objective: rerun the guarded ElevenLabs streaming TTS harness after resolving the earlier provider/account voice block
- Action taken:
  - reran `VOICE-013` with explicit `--live`
  - generated four MP3 files, two German and two English
  - verified that generated JSON and Markdown artifacts did not contain API key or voice ID values
  - confirmed no customer audio was uploaded
  - confirmed generated MP3 files remain ignored by Git
- Data used:
  - `research/experiments/generated/VOICE-013-elevenlabs-tts-smoke.json`
  - `research/experiments/generated/VOICE-013-elevenlabs-tts-smoke-report.md`
  - user listening feedback on the generated MP3 files
- What was learned:
  - all four ElevenLabs streaming requests returned HTTP `200`
  - all four MP3 files were created
  - max time to first audio byte was `507.54 ms`
  - max total provider latency was `1112.927 ms`
  - one German case was slightly above the `500 ms` first-audio target
  - user listening impression was that there is still room for improvement, but ElevenLabs sounded much better than the previous provider audio
- Error or risk recorded:
  - informal listening impressions are useful but not enough for a final provider decision
  - provider latency and perceived naturalness can point in different directions, so both need to be recorded
  - the first-audio target should be treated as a design target, not as a single-run absolute pass/fail
- Why it matters for the thesis:
  - this creates a successful second-provider voice result for comparison against Cartesia
  - it supports the product architecture decision to keep TTS providers as swappable adapters
- Open questions:
  - whether ElevenLabs remains better after structured German/English ratings
  - whether VOICE-012 naturalized text improves ElevenLabs output further
  - whether the slightly slower German first-audio case can be improved by model, voice, or request settings

### 2026-05-02 - VOICE-014 provider listening comparison packet

- Objective: convert the informal Cartesia-vs-ElevenLabs listening impression into a structured comparison artifact
- Action taken:
  - added a VOICE-014 comparison case file pairing the four Cartesia VOICE-011 samples with the four ElevenLabs VOICE-013 samples
  - added a runner that reads existing provider artifacts and local audio files without making provider calls
  - generated JSON, Markdown, and HTML listening comparison artifacts
  - added a validator that checks all audio pairs exist and that no quality claim is allowed before ratings are recorded
- Data used:
  - `research/experiments/generated/VOICE-011-cartesia-websocket-smoke.json`
  - `research/experiments/generated/VOICE-013-elevenlabs-tts-smoke.json`
  - local ignored WAV and MP3 files from the successful live runs
- Output created:
  - `docs/product/VOICE_014_PROVIDER_LISTENING_COMPARISON.md`
  - `research/experiments/VOICE-014-provider-listening-comparison.md`
  - `research/experiments/cases/voice-014-provider-listening-comparison.json`
  - `research/experiments/generated/VOICE-014-provider-listening-comparison.json`
  - `research/experiments/generated/VOICE-014-provider-listening-comparison-report.md`
  - `research/experiments/generated/VOICE-014-provider-listening-comparison.html`
  - `scripts/run_voice_014_provider_listening_comparison.py`
  - `scripts/validate_voice_014_provider_listening_comparison.py`
- What was learned:
  - all four comparison pairs have both Cartesia and ElevenLabs audio available
  - ElevenLabs has lower total latency in all four pairs
  - first-audio timing is mixed: Cartesia starts faster in one German case, ElevenLabs starts faster in the other three cases
  - a provider decision should combine timing and structured listening ratings, not only informal preference
- Error or risk recorded:
  - the validator initially repeated the earlier assertion-message bug around missing regex matches; it was fixed and rerun
  - local audio files are intentionally ignored by Git, so the comparison artifact is reproducible only on machines where the generated audio exists
- Why it matters for the thesis:
  - this adds an evaluation bridge between raw provider smoke tests and a defensible provider choice
  - it preserves the distinction between measured latency and subjective-but-structured human listening quality
- Open questions:
  - how ElevenLabs and Cartesia score under the full rubric
  - whether VOICE-012 naturalized text improves the stronger provider further
  - whether German quality should receive heavier weight for the first client context

### 2026-05-02 - VOICE-015 prosody naturalness layer

- Objective: reduce robotic voice delivery caused by flat pitch, uniform pacing, equal word spacing, and no human thinking holds
- Action taken:
  - added a provider-neutral prosody planner for pause, rate, emphasis, pitch, and rare stretch cues
  - kept the default style as `professional-human`
  - added eight bilingual cases that cover English and German freeform speech, protected campaign questions, disclosures, do-not-call, hangup, strict insurance boundaries, and disabled clean-script mode
  - generated JSON and Markdown artifacts
  - added a validator that checks deterministic seeded output, bounded cue ranges, clean TTS text, and zero cues inside protected segments
- Data used:
  - user listening feedback that provider audio still sounded too robotic because pacing was stable and pitch was flat
  - existing VOICE-012 segment-aware protection boundaries
  - existing VOICE-014 provider-comparison context
- Output created:
  - `scripts/prosody_naturalness.py`
  - `scripts/run_voice_015_prosody_naturalness.py`
  - `scripts/validate_voice_015_prosody_naturalness.py`
  - `research/experiments/cases/voice-015-prosody-naturalness.json`
  - `research/experiments/generated/VOICE-015-prosody-naturalness.json`
  - `research/experiments/generated/VOICE-015-prosody-naturalness-report.md`
  - `docs/product/VOICE_015_PROSODY_NATURALNESS_LAYER.md`
  - `research/experiments/VOICE-015-prosody-naturalness.md`
- What was learned:
  - human-like speech needs more than fillers; it also needs controlled variation in pauses, rate, emphasis, pitch, and rare thinking holds
  - raw Markdown bold should not be treated as the provider contract because TTS providers may ignore or misread it
  - structured prosody cues keep provider adapters swappable and auditable
  - seeded randomization gives natural variation without losing reproducibility
- Error or risk recorded:
  - during TDD, the strict one-cue insurance case initially used its only cue budget on a comma pause instead of the intended empathy pitch cue
  - cue priority was changed so pitch is planned before pauses when the campaign allows only a tiny prosody budget
  - VOICE-015 does not prove improved audio quality yet; it only proves safe cue planning
- Why it matters for the thesis:
  - this adds a concrete bridge between text-response generation and perceived voice naturalness
  - it shows how qualitative listening observations were converted into testable system constraints
  - it preserves compliance boundaries while improving the realism of the voice layer
- Open questions:
  - how ElevenLabs and Cartesia should render the structured cue plan
  - whether prosody-shaped audio scores higher than plain guarded text in human listening review
  - whether German pronunciation and trustworthiness improve or worsen when subtle pitch/rate cues are applied

### 2026-05-02 - VOICE-016 provider prosody rendering

- Objective: translate the provider-neutral VOICE-015 prosody plan into inspectable provider-specific TTS inputs before live synthesis
- Action taken:
  - added an offline provider-prosody renderer
  - rendered Cartesia and ElevenLabs variants for all eight VOICE-015 cases
  - mapped Cartesia pause, rate, emphasis, and stretch cues to SSML-style break, speed, volume, and break behavior
  - mapped ElevenLabs pause cues to break tags and rate cues to request-level speed settings
  - recorded unsupported pitch and emphasis cues instead of forcing unreliable provider tricks
  - added validation that provider tags do not enter protected segments
- Data used:
  - `research/experiments/generated/VOICE-015-prosody-naturalness.json`
  - current provider documentation for Cartesia Sonic 3 SSML-style tags and ElevenLabs pause controls
- Output created:
  - `scripts/provider_prosody_rendering.py`
  - `scripts/run_voice_016_provider_prosody_rendering.py`
  - `scripts/validate_voice_016_provider_prosody_rendering.py`
  - `research/experiments/cases/voice-016-provider-prosody-rendering.json`
  - `research/experiments/generated/VOICE-016-provider-prosody-rendering.json`
  - `research/experiments/generated/VOICE-016-provider-prosody-rendering-report.md`
  - `docs/product/VOICE_016_PROVIDER_PROSODY_RENDERING.md`
  - `research/experiments/VOICE-016-provider-prosody-rendering.md`
- What was learned:
  - provider support is uneven: Cartesia can represent more cue types directly, while ElevenLabs should remain conservative for this checkpoint
  - pitch is still not safely mapped for either provider in the current implementation
  - per-segment rendering is necessary because global text replacement could accidentally alter protected questions or disclosures
  - a provider preview layer makes future live synthesis auditable and easier to debug
- Error or risk recorded:
  - the first VOICE-016 validator version expected Cartesia break tags for a strict insurance case that had only a pitch cue and no pause cue
  - the validator was corrected to assert break tags only when pause cues are present
  - unsupported cues must be reported honestly so the project does not claim provider control that has not been proven
- Why it matters for the thesis:
  - this checkpoint connects the human-like prosody concept to concrete implementation boundaries
  - it gives evidence that provider integration is being handled through safe, testable adapters rather than ad hoc prompt tricks
- Open questions:
  - whether Cartesia's richer direct cue rendering sounds more human or too mechanical in live audio
  - whether ElevenLabs' conservative break/speed rendering is enough to improve naturalness
  - whether a later provider or model supports direct pitch/emphasis controls suitable for live sales calls

### 2026-05-02 - VOICE-017 guarded live A/B audio harness

- Objective: prepare a safe live A/B test that compares plain guarded text against VOICE-016 prosody-shaped text
- Action taken:
  - added a VOICE-017 case config selecting two German and two English cases from VOICE-016
  - added a live-capable runner that prepares plain and prosody variants for ElevenLabs and Cartesia
  - kept dry-run as the default behavior
  - added forced-missing-key fallback validation for both providers
  - blocked accidental live calls to both providers unless `--allow-both-live` is explicitly set
  - ignored generated VOICE-017 MP3 and WAV files in Git
- Data used:
  - `research/experiments/generated/VOICE-016-provider-prosody-rendering.json`
  - previously validated ElevenLabs HTTP streaming and Cartesia WebSocket provider paths
- Output created:
  - `scripts/run_voice_017_live_ab_audio.py`
  - `scripts/validate_voice_017_live_ab_audio.py`
  - `research/experiments/cases/voice-017-live-ab-audio.json`
  - `research/experiments/generated/VOICE-017-live-ab-audio.json`
  - `research/experiments/generated/VOICE-017-live-ab-audio-report.md`
  - `docs/product/VOICE_017_LIVE_AB_AUDIO.md`
  - `research/experiments/VOICE-017-live-ab-audio.md`
- What was learned:
  - live audio comparison needs a smaller case set than the full prosody suite to keep provider calls and listening work manageable
  - dry-run artifacts can verify request structure and safety boundaries before keys are provided
  - live A/B testing should start with one provider, likely ElevenLabs, before spending calls on both providers
- Error or risk recorded:
  - live `--provider both` could create many calls at once, so the runner blocks it unless `--allow-both-live` is set
  - dry-run cannot judge whether prosody-shaped input sounds better; it only proves that the live test is safely prepared
  - generated audio remains local and ignored by Git, so listening comparison depends on the local machine's generated files
- Why it matters for the thesis:
  - this creates the first direct path from voice naturalness design to measurable listening evidence
  - it preserves the methodology rule that perceptual quality claims require human listening ratings
- Open questions:
  - whether prosody-shaped audio actually sounds more human than plain guarded text
  - whether provider tags improve rhythm or make speech sound more artificial
  - whether ElevenLabs or Cartesia should be preferred after plain-vs-prosody scoring

### 2026-05-02 - VOICE-017 first live prosody listening result

- Objective: record the first human listening result for the plain-vs-prosody audio comparison
- Action taken:
  - ran VOICE-017 live with ElevenLabs only and `--limit 2`
  - generated two plain MP3 files and two prosody MP3 files
  - confirmed there were no provider fallbacks
  - confirmed no customer audio was uploaded and no voice cloning was used
  - recorded the project owner's listening judgment that prosody sounded much better than plain speech
- Data used:
  - `research/experiments/generated/VOICE-017-live-ab-audio.json`
  - `research/experiments/generated/VOICE-017-live-ab-audio-report.md`
  - local ignored VOICE-017 ElevenLabs MP3 files
- Output created:
  - `research/experiments/generated/VOICE-017-human-listening-review.md`
  - updated `research/experiments/generated/VOICE-017-live-ab-audio.json`
  - updated `research/experiments/generated/VOICE-017-live-ab-audio-report.md`
  - updated `research/experiments/VOICE-017-live-ab-audio.md`
  - updated `docs/product/VOICE_017_LIVE_AB_AUDIO.md`
- What was learned:
  - the prosody-shaped variants were strongly preferred in this first two-case ElevenLabs live A/B run
  - the VOICE-015/VOICE-016 prosody stack should be kept because it appears directionally valuable in live synthesized speech
  - the next useful question is how much prosody is optimal, not whether prosody matters at all
- Error or risk recorded:
  - this is an internal one-listener result, not a broad customer-preference result
  - the claim must stay scoped to the two-case ElevenLabs live A/B run until more cases, voices, or listeners are tested
  - generated audio remains local and ignored by Git, so future reviewers need either regenerated audio or a preserved local artifact package
- Why it matters for the thesis:
  - this turns earlier voice-naturalness design work into an actual perceptual result
  - it gives a concrete example of how qualitative listening feedback can become bounded evaluation evidence
  - it supports the product direction of using configurable prosody controls while preserving compliance-protected text
- Open questions:
  - whether the same preference holds on the remaining VOICE-017 cases
  - whether a second listener agrees with the strong prosody preference
  - whether Cartesia's richer direct tags can match or beat the ElevenLabs prosody result

### 2026-05-02 - RESP-002 runtime voice delivery bridge

- Objective: connect guarded response generation to the voice prosody stack without allowing the voice layer to change meaning or compliance behavior
- Action taken:
  - added a RESP-002 runtime voice-delivery module
  - added a CLI that mirrors the RESP-001 guarded response command and appends `voice_delivery` metadata
  - classified guarded final responses as either prosody-eligible freeform speech or protected text
  - applied the VOICE-015 prosody planner to eligible freeform text
  - rendered an offline VOICE-016 provider preview, defaulting to ElevenLabs
  - added a validator proving `final_response` stays unchanged and protected cases receive no prosody/provider tags
- Data used:
  - `RESP-001` guarded response output for a German B2C telecom price objection
  - active `PROD-005` runtime campaign wrapper
  - existing VOICE-015 and VOICE-016 prosody/provider rendering modules
- Output created:
  - `scripts/runtime_voice_delivery.py`
  - `scripts/generate_runtime_voice_delivery.py`
  - `scripts/validate_resp_002_runtime_voice_delivery.py`
  - `docs/product/RESP_002_RUNTIME_VOICE_DELIVERY.md`
  - `research/experiments/RESP-002-runtime-voice-delivery.md`
  - `research/experiments/generated/RESP-002-runtime-voice-delivery-result.json`
  - `research/experiments/generated/RESP-002-runtime-voice-delivery-report.md`
- What was learned:
  - the runtime path can now prepare approved responses for voice delivery while preserving the exact guarded final response
  - prosody belongs after safety and response generation, not inside the compliance or call-control layer
  - protected runtime outcomes such as do-not-call, claim-boundary, human handoff, and appointment confirmation need explicit delivery protection
- Error or risk recorded:
  - the first validator run failed correctly because the RESP-002 runner was missing
  - the first implementation attempt omitted an explicit `eligible_for_prosody` segment field; the schema was clarified and validation reran successfully
  - the validator initially wrote to official artifact paths, so it was moved to `.tmp` to preserve clean generated evidence
- Why it matters for the thesis:
  - this shows a full bridge from sales-state decision to guarded text to voice-delivery preparation
  - it supports the thesis argument that naturalness improvements can be added without weakening deterministic guardrails
  - it keeps the product architecture vertical-agnostic and campaign-configurable
- Open questions:
  - whether RESP-002 should later synthesize live audio directly or continue handing off to explicit live TTS checkpoints
  - whether multi-segment responses should represent campaign questions and disclosures separately before TTS
  - how much runtime prosody should be enabled by default for regulated campaigns

### 2026-05-02 - Project self-containment policy for client portability

- Objective: ensure the Emotion Aware repo remains portable and does not depend on other local workspace folders for required workflows
- Action taken:
  - added a project-local self-containment policy
  - adapted voice provider run-boundary and generated-audio asset-log templates into Emotion Aware docs
  - added a validator that checks required local docs exist and Python scripts do not hard-depend on `D:\Codex\shared` or other active workspace projects
  - updated setup checks and third-party inspiration notes
- Data used:
  - workspace-level voice consent, generated asset log, and media provider workflow ideas as inspiration only
  - user requirement that any dependency needed by Emotion Aware must live inside the Emotion Aware folder
- Output created:
  - `docs/product/PROJECT_SELF_CONTAINMENT_POLICY.md`
  - `docs/product/VOICE_PROVIDER_RUN_BOUNDARY.md`
  - `docs/product/VOICE_GENERATED_AUDIO_ASSET_LOG.md`
  - `scripts/validate_self_contained_project_policy.py`
- What was learned:
  - future client handoff requires the product repo to carry its own policies, templates, and review gates
  - workspace-level materials can inspire product docs, but they should not become hidden dependencies
  - RESP-003 should use local provider-run and generated-audio logging docs, not shared workspace templates
- Error or risk recorded:
  - the first self-containment validator run failed because the local docs did not exist yet
  - the validator initially flagged its own forbidden-reference examples, so it was adjusted to exclude itself from that script scan
- Why it matters for the thesis:
  - this strengthens reproducibility and handoff quality because project evidence and safety procedures live inside the project
  - it supports the product framing as a client-portable sales-agent system rather than a workspace-only prototype
- Open questions:
  - whether future client packs should include a separate `handoff/` folder
  - whether setup validation should later detect non-Python references to external workspace paths as warnings

### 2026-05-02 - RESP-003 runtime live-capable TTS bridge

- Objective: connect the validated runtime voice-delivery packet to optional live TTS while preserving offline default behavior and provider safety boundaries
- Action taken:
  - added a RESP-003 runtime TTS delivery module
  - added a project-local TTS provider client helper so runtime code does not import directly from experiment runners
  - added a CLI that builds RESP-001, RESP-002, and then appends `tts_delivery`
  - used validated RESP-002 provider-rendered text only for prosody-eligible freeform segments
  - forced protected outcomes such as do-not-call to use exact `final_response`
  - added generated-audio asset-log metadata to the runtime packet
  - added dry-run, forced-missing-key, protected-text, redaction, and no-secret validation
  - wired the checkpoint into setup docs and setup validation
- Data used:
  - active `PROD-005` German B2C telecom campaign wrapper
  - RESP-002 runtime voice-delivery output
  - local provider boundary and generated-audio asset-log docs
  - existing ElevenLabs and Cartesia provider-call discipline from VOICE-017
- Output created:
  - `scripts/runtime_tts_delivery.py`
  - `scripts/tts_provider_clients.py`
  - `scripts/generate_runtime_tts_delivery.py`
  - `scripts/validate_resp_003_runtime_live_tts.py`
  - `docs/product/RESP_003_RUNTIME_LIVE_TTS.md`
  - `research/experiments/RESP-003-runtime-live-tts.md`
  - `research/experiments/generated/RESP-003-runtime-live-tts-result.json`
  - `research/experiments/generated/RESP-003-runtime-live-tts-report.md`
- What was learned:
  - live TTS can remain a separate opt-in layer after guarded response and delivery shaping
  - provider audio generation does not need to become part of default setup or validation
  - protected text needs a simpler rule than freeform speech: speak the exact guarded response
- Error or risk recorded:
  - the first RESP-003 validator run failed correctly because the runner did not exist yet
  - live audio quality remains unproven by dry-run validation and needs human listening review
  - provider latency and provider-side text handling remain external variables during live runs
- Why it matters for the thesis:
  - this turns the response stack into an end-to-end architecture from customer transcript to optional audio output
  - it preserves the thesis/product distinction between safety decisions, wording, delivery shaping, and provider synthesis
  - it documents another concrete iteration where a missing component was caught by a failing validator before implementation
- Open questions:
  - which provider and voice should be used for the next live RESP-003 run
  - how to connect generated audio to the local demo/playback loop without adding latency or unsafe provider defaults
  - how to represent multi-segment turns where a freeform bridge, campaign question, and disclosure may all be spoken in one response

### 2026-05-02 - RESP-003 bilingual ElevenLabs live TTS run

- Objective: verify that RESP-003 can generate live ElevenLabs audio for both German and English campaign responses using separate language-specific voice IDs
- Action taken:
  - ran RESP-003 live TTS for the German B2C telecom campaign
  - ran RESP-003 live TTS for the English B2B software campaign
  - verified generated JSON artifacts for safety flags, latency, audio output, and redacted provider metadata
  - added a Git ignore rule for RESP-003 MP3 audio artifacts so generated audio stays local
- Data used:
  - German transcript: `Das klingt zu teuer und ich weiss nicht, ob sich der Aufwand lohnt.`
  - English transcript: `That sounds expensive, and I am not sure it is worth changing our workflow.`
  - environment-only `ELEVENLABS_API_KEY`
  - environment-only `ELEVENLABS_VOICE_ID_DE`
  - environment-only `ELEVENLABS_VOICE_ID_EN`
- Output created:
  - `research/experiments/generated/RESP-003-live-elevenlabs-de-result.json`
  - `research/experiments/generated/RESP-003-live-elevenlabs-de-report.md`
  - `research/experiments/generated/RESP-003-live-elevenlabs-en-result.json`
  - `research/experiments/generated/RESP-003-live-elevenlabs-en-report.md`
  - local ignored German MP3 audio artifact
  - local ignored English MP3 audio artifact
- Technical result:
  - German live call: HTTP 200, audio created, 119581 bytes, time to first audio 723.09 ms, total provider latency 901.017 ms
  - English live call: HTTP 200, audio created, 112894 bytes, time to first audio 488.206 ms, total provider latency 670.137 ms
  - customer audio uploaded: false
  - voice cloning used: false
  - API key value logged: false
  - voice ID value logged: false
  - validation passed: true
- What was learned:
  - RESP-003 can route German and English runtime responses to language-specific ElevenLabs voice IDs
  - technical provider latency was under one second in this two-case run
  - generated audio evidence needs the same local-ignore treatment as earlier voice experiments
- Error or risk recorded:
  - the first attempt to let Codex run live calls could not see the environment variables because they were set in a different PowerShell process
  - the workaround was to run the live commands in the same terminal where the environment variables were set
  - audio quality is still not claimed because human listening review has not been recorded for these two RESP-003 files
- Why it matters for the thesis:
  - this provides the first bilingual live TTS evidence for the runtime response stack
  - it shows a practical implementation detail: environment-scoped secrets are safer, but process boundaries can affect live-provider testing
  - it keeps quality claims separate from technical success claims
- Open questions:
  - how the German and English audio sound in human listening review
  - whether longer scripts keep latency and naturalness within the product target
  - whether the same bilingual flow should be connected to the local browser demo next

### 2026-05-03 - RESP-003 bilingual human listening review

- Objective: record the first human quality review of the bilingual RESP-003 ElevenLabs live audio
- Action taken:
  - reviewed the German and English MP3 outputs from RESP-003
  - recorded qualitative product feedback without forcing uncertain numeric ratings
  - documented the result as listening evidence, not as a production-readiness claim
- Data used:
  - `research/experiments/generated/RESP-003-campaign-prod-005-b2c-telecom-de-elevenlabs-efb86453.mp3`
  - `research/experiments/generated/RESP-003-campaign-prod-005-b2b-software-en-elevenlabs-00aae825.mp3`
- Output created:
  - `research/experiments/generated/RESP-003-bilingual-human-listening-review.md`
- What was learned:
  - both outputs are clear and pronunciation is good
  - the voices still sound obviously AI-generated
  - the delivery is too slow for a sales-agent call
  - pacing has improved, but naturalness, pitch, and emotion still need work
  - the audio is not ready for real leads yet
- Error or risk recorded:
  - trust and artifact scores were not forced because the reviewer was unsure how to score them reliably
  - the correct conclusion is not "voice failed"; it is "technical live TTS works, quality is not product-ready yet"
- Why it matters for the thesis:
  - this creates an honest qualitative evaluation point after technical live TTS success
  - it separates latency/synthesis success from perceived sales-readiness
  - it defines the next voice-improvement hypothesis: faster professional sales pacing plus better pitch/emotion variation
- Open questions:
  - what speed range sounds like a professional sales agent without becoming pushy
  - whether provider voice settings alone can improve naturalness, or whether wording/prosody markup needs to change too
  - how to score trust and artifacts more clearly in later listening rubrics

### 2026-05-03 - GUARD-001 project drift guard

- Objective: prevent the Emotion Aware product repo from quietly drifting into hidden external dependencies, leaked secrets, or unsafe generated artifacts
- Action taken:
  - added a project-local drift guard runner
  - added a validator with dirty and clean fixtures
  - wired the guard into setup checks and the product command map
  - documented that the guard reports failures but does not automatically edit files
- Data used:
  - current Emotion Aware repo structure
  - existing self-containment policy
  - generated voice/audio artifact patterns
  - known local-workspace inspiration and internal-tool documentation boundaries
- Output created:
  - `scripts/check_project_drift.py`
  - `scripts/validate_project_drift_guard.py`
  - `docs/product/PROJECT_DRIFT_GUARD.md`
- What was learned:
  - the first validator run failed correctly because the guard runner did not exist yet
  - the first guard run found a real missing documentation file from the new checkpoint
  - the guard also surfaced the difference between product dependency risk and allowed provenance/internal-tool notes
  - generated audio needs explicit ignore or curation rules because provider outputs are easy to create during voice experiments
- Error or risk recorded:
  - a guard that auto-fixes files too early could hide important architectural decisions
  - broad external-path checks can create noise unless allowed documentation areas are clearly separated from runtime dependencies
  - secret scanning should report locations and rules, not values
- Why it matters for the thesis:
  - it preserves reproducibility and portability as the project grows from experiments toward a client-ready product
  - it documents another engineering-control layer created because of issues encountered during iterative voice/provider work
  - it supports honest reporting of privacy, dependency, and artifact-handling practices
- Open questions:
  - whether GUARD-001 should later run in CI or remain local until the deployment target is clearer
  - whether deployment preflight should reuse this guard or become a stricter separate gate
  - whether remediation suggestions should be added while keeping automatic fixes disabled
