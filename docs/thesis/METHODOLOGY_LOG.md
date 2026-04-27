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

### 2026-04-28 - First product MVP simulation case set

- Objective: create the first runnable product-track artifact for the autonomous qualification and appointment-setting workflow
- Action taken:
  - defined eight turn-based lead scenarios covering interest, uncertainty, disinterest, do-not-call, escalation, referral, skepticism, and scheduling failure
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
