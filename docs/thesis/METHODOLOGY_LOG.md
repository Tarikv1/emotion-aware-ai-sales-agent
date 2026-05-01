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
