# Decision Log

Record important thesis and implementation decisions here with enough context to justify them later.

## Template

### DEC-XXX - Title

- Date:
- Status: proposed | accepted | changed | dropped
- Decision:
- Why:
- Alternatives considered:
- Consequences:

## Decisions

### DEC-016 - Use turn-based simulation before product telephony integration

- Date: 2026-04-28
- Status: accepted
- Decision: create a structured turn-based simulation case set for the client MVP before building real outbound calling, calendar integration, or a UI
- Why:
  - the product workflow needs testable behavior before external integrations add complexity
  - simulation cases can exercise interest classification, strategy selection, scheduling triggers, and escalation guardrails
  - this keeps the product track aligned with the thesis habit of small, repeatable experiments
- Alternatives considered:
  - start directly with a telephony prototype
  - build a dashboard before the qualification logic is testable
  - reuse only the thesis prompt-comparison cases for product validation
- Consequences:
  - the next product implementation can target structured `CallOutcome` generation
  - the simulation is not evidence from real client calls and should be labeled as product-synthetic
  - later client or expert feedback can replace or extend these cases

### DEC-001 - Start with a public-data-first baseline

- Date: 2026-04-27
- Status: accepted
- Decision: build the first thesis baseline using public datasets before depending on private call-center data
- Why:
  - private data is not currently in hand
  - the thesis needs a reproducible baseline
  - this reduces risk and keeps early progress unblocked
- Alternatives considered:
  - wait for private data before starting
  - assume private data will become available soon and design around it
- Consequences:
  - the first experiment will optimize for clarity and feasibility rather than direct domain realism
  - later adaptation to private German call-center data remains possible as a documented extension

### DEC-002 - Treat the proposal as directional, not binding

- Date: 2026-04-27
- Status: accepted
- Decision: do not freeze the architecture, metrics, or dataset plan based solely on the initial thesis proposal
- Why:
  - parts of the methodology section were drafted as estimations rather than confirmed implementation choices
  - locking them too early would create unnecessary rigidity
- Alternatives considered:
  - mirror the proposal exactly in the repo and implementation plan
- Consequences:
  - the repo structure remains flexible
  - the written thesis will need to distinguish early proposal assumptions from final implementation choices

### DEC-003 - Use MELD and Persuasion for Good as phase-1 anchors

- Date: 2026-04-27
- Status: accepted
- Decision: use `MELD` and `Persuasion for Good` as the most actionable phase-1 public datasets while treating `IEMOCAP` as pending verification
- Why:
  - both are already available locally in usable extracted form
  - they cover the emotion and persuasion sides of the first baseline
  - the current `IEMOCAP` download appears to be a derivative export rather than the official corpus structure
- Alternatives considered:
  - delay dataset work until all three datasets are equally ready
  - start with larger phone-conversation corpora such as Switchboard or Fisher
- Consequences:
  - the first experiment will likely be text-forward or dialogue-structure-first rather than audio-first
  - an audio-focused phase may still be added later

### DEC-004 - Use MELD sentiment for the first compact emotion taxonomy

- Date: 2026-04-27
- Status: accepted
- Decision: use the `Sentiment` column in `MELD` as the primary phase-1 emotion signal instead of collapsing the raw seven-way `Emotion` labels directly
- Why:
  - it already provides a compact three-way label space
  - it avoids arbitrary treatment of `surprise`
  - it is easier to align with the first adaptive baseline
- Alternatives considered:
  - collapse the raw `Emotion` column directly into three classes
  - exclude `MELD` and wait for a cleaner speech-emotion dataset
- Consequences:
  - the first baseline will be broader in affective meaning than a fine-grained emotion classifier
  - raw emotion labels remain available for later secondary experiments

### DEC-005 - Use a five-part persuasion taxonomy for phase 1

- Date: 2026-04-27
- Status: accepted
- Decision: compress the persuader labels in `Persuasion for Good` into five strategy groups: `rapport`, `inquiry`, `evidence-or-benefit`, `emotional-appeal`, and `direct-ask-or-commitment`
- Why:
  - the original label set is too granular for the first adaptive baseline
  - the reduced taxonomy remains interpretable and close to the dataset's annotation intent
  - the dataset does not strongly justify forcing `reassurance` as a primary phase-1 category
- Alternatives considered:
  - use the full original label space
  - use a four-part taxonomy that merges emotional appeal into another category
- Consequences:
  - the first experiment stays manageable
  - later experiments may refine or expand the strategy space

### DEC-006 - Start with a rule-based adaptive baseline comparison

- Date: 2026-04-27
- Status: accepted
- Decision: define the first experiment as a comparison between a non-adaptive baseline and a rule-based adaptive baseline that changes strategy selection based on compact emotion state
- Why:
  - it creates a clear and implementable first comparison
  - it tests the core thesis idea without requiring full end-to-end agent complexity
  - it keeps the adaptation logic transparent for analysis and writing
- Alternatives considered:
  - jump directly to a learned strategy policy
  - delay baseline definition until full model architecture is chosen
- Consequences:
  - the first implementation can focus on interpretable strategy shifts
  - later work can replace the rule-based policy with learned components if justified

### DEC-007 - Use prompt templates plus rubric-based comparison for the first runnable evaluation

- Date: 2026-04-27
- Status: accepted
- Decision: operationalize the first baseline through paired prompt templates and a lightweight qualitative evaluation rubric
- Why:
  - it gives the project a runnable experiment format quickly
  - it keeps the first evaluation interpretable and easy to document
  - it avoids premature commitment to a heavy metric stack before the response behavior is even tested
- Alternatives considered:
  - delay prompt work until a coded pipeline exists
  - define only quantitative evaluation at this stage
- Consequences:
  - the next implementation step can focus on generating paired responses for test cases
  - early thesis evidence can include concrete side-by-side examples and rubric outcomes

### DEC-008 - Start with curated synthetic seed cases for the first prompt comparison pass

- Date: 2026-04-27
- Status: accepted
- Decision: use a small set of project-authored synthetic cases as the first evaluation inputs before moving to dataset-derived cases
- Why:
  - it lets the project test the prompt comparison workflow immediately
  - it keeps the first cases tightly aligned with the phase-1 strategy and emotion taxonomy
  - it reduces setup friction while the data-driven case extraction path is still being shaped
- Alternatives considered:
  - wait until dataset-derived cases are prepared
  - mix synthetic and dataset-derived cases from the start
- Consequences:
  - the first evaluation pass will be useful for workflow and behavior validation, not final thesis claims
  - later experiments should extend the case set with stronger empirical grounding

### DEC-009 - Adapt modular voice analytics as a later sales-agent module

- Date: 2026-04-27
- Status: accepted
- Decision: incorporate the concept of modular interpretable voice-feature analysis from collaborative thesis work with Shehzeb Iftakhar as a later module in the sales-agent emotion engine
- Why:
  - voice features are directly relevant to customer emotion and conversational state
  - the idea strengthens the multi-modal direction of the sales-agent thesis
  - the collaborator relationship and supervisor approval allow concept sharing with proper attribution
- Alternatives considered:
  - keep the sales-agent project text-only
  - import the full creative-expression analytics framework
- Consequences:
  - phase 1 remains focused on text and strategy baselines
  - phase 2 can compare text-only adaptation against text-plus-voice adaptation
  - attribution and conceptual boundaries should be documented clearly in the thesis

### DEC-010 - Document supervisor-approved AI use for the technical workflow

- Date: 2026-04-27
- Status: accepted
- Decision: explicitly document that AI usage is supervisor-approved for the technical part of the thesis project
- Why:
  - it clarifies the legitimacy of AI-assisted technical development
  - it creates a transparent record for later thesis writing and defense
  - it separates technical assistance from final thesis authorship responsibility
- Alternatives considered:
  - leave AI usage undocumented
  - document it only informally outside the project
- Consequences:
  - the thesis record now includes a clear statement on AI-assisted technical workflow
  - future write-up can reference this permission without reconstructing the policy from memory

### DEC-011 - Use structured JSON case files plus a generated prompt packet as the repeatable execution path

- Date: 2026-04-27
- Status: accepted
- Decision: operationalize repeatable prompt comparisons through structured JSON case files and a small runner script that generates markdown prompt packets
- Why:
  - it reduces manual prompt assembly
  - it keeps the case inputs explicit and reusable
  - it creates a consistent bridge between case design, prompt execution, and scoring
- Alternatives considered:
  - keep using markdown-only case packs with manual copying
  - jump directly to a heavier end-to-end automated evaluation system
- Consequences:
  - future case sets can be added more cleanly
  - the current workflow remains lightweight while becoming more reproducible

### DEC-012 - Scope the first client MVP around qualification and scheduling, not autonomous closing

- Date: 2026-04-27
- Status: accepted
- Decision: define the first client MVP as an autonomous lead-qualification and appointment-setting agent with fallback and escalation guardrails
- Why:
  - it matches the actual client need more closely than a full autonomous closer
  - it creates a more realistic early product scope
  - it lets the thesis adaptation logic support a concrete and defensible workflow
- Alternatives considered:
  - aim immediately for full sales-closing behavior
  - make the launch workflow permanently human-in-the-loop for normal cases
- Consequences:
  - qualification questions and interest classification become first-class product artifacts
  - human sales agents remain the closing path for interested leads

### DEC-013 - Treat the project as both thesis and real product

- Date: 2026-04-27
- Status: accepted
- Decision: explicitly steer the project as both an academic thesis and a real product intended for client use
- Why:
  - a potential client is ready to buy when the product launches
  - product usefulness creates constraints that pure thesis planning would miss
  - the thesis evidence can strengthen the product, while product requirements can keep the thesis grounded
- Alternatives considered:
  - continue treating productization as a distant future step
  - focus only on the client product and weaken the thesis evidence trail
- Consequences:
  - the roadmap now includes a product MVP track
  - early implementation should target autonomous behavior while preserving fallback and escalation guardrails
  - product claims must remain separate from thesis experiment claims until evidence supports them

### DEC-014 - Use sales-expert feedback as a product training loop

- Date: 2026-04-27
- Status: accepted
- Decision: incorporate feedback from experienced salespeople during development so the agent can learn from expert ratings, rewrites, labels, and strategy corrections
- Why:
  - sales experts can provide domain judgment that public datasets cannot capture
  - expert feedback can improve response quality before client launch
  - this creates a practical learning path beyond static prompt comparisons
- Alternatives considered:
  - rely only on public datasets and synthetic cases
  - attempt model fine-tuning before collecting expert preference data
- Consequences:
  - the product track should include a feedback capture format
  - early learning should start with prompt/rule updates and example retrieval before fine-tuning
  - expert feedback data must be stored and attributed carefully

### DEC-015 - Define the first product as lead qualification and appointment setting

- Date: 2026-04-27
- Status: accepted
- Decision: scope the first client-facing product to autonomous outbound lead qualification and appointment setting with human sales-agent follow-up
- Why:
  - this matches the client's actual initial request
  - it is narrower and more launchable than a full autonomous closing agent
  - it still benefits from emotion-aware strategy adaptation
- Alternatives considered:
  - build directly toward a full autonomous sales closer
  - build only a human-reviewed sales copilot
- Consequences:
  - the first product workflow should focus on call initiation, qualification questions, interest detection, and scheduling
  - the thesis baseline remains relevant because strategy adaptation supports qualification and objection handling
  - calendar/availability integration becomes a product requirement

### DEC-016 - Treat English/German voice naturalness as speech mechanics, not stereotypes

- Date: 2026-05-04
- Status: accepted
- Decision: design future English and German speech-realism profiles around fillers, pauses, breath, rhythm, repairs, and warmth cues, while keeping language mechanics separate from campaign persona and cultural stereotypes
- Why:
  - the agent needs to sound less robotic in both English and German
  - human speech uses language-specific timing, filler, and interaction patterns
  - random fillers would reduce trust and could make the system sound fake
  - stereotype-like language behavior would be product-risky and academically weak
- Alternatives considered:
  - use one generic filler system for all languages
  - rely only on provider voice remixing and avoid local speech-realism rules
  - make the voice more casual without language-specific constraints
- Consequences:
  - `VOICE-023` should use language-aware profiles
  - protected campaign text remains exact and filler-free
  - English and German profile rules should cite `SPEECH_REALISM_REFERENCES.md`
  - future listening evaluation should include naturalness, trust, professionalism, and overacting risk

### DEC-017 - Maintain a central thesis reference registry

- Date: 2026-05-04
- Status: accepted
- Decision: keep a thesis-level source registry that separates academic sources, dataset sources, provider documentation, sales-practice articles, privacy references, and open-source inspiration
- Why:
  - many useful sources were found across different checkpoints
  - chat history is not a reliable bibliography
  - not all sources have the same evidential weight
  - thesis writing needs fast access to source URLs and usage boundaries
- Alternatives considered:
  - keep references only inside each experiment note
  - put all sources into `SPEECH_REALISM_REFERENCES.md`
  - rely on `third-party-inspirations.md` only
- Consequences:
  - `THESIS_REFERENCE_REGISTRY.md` becomes the first stop for source lookup
  - `SPEECH_REALISM_REFERENCES.md` stays focused on speech-realism literature
  - product engineering implications belong in product docs such as `VOICE_023_SPEECH_REALISM_LAYER.md`
  - final thesis citations still need formatting and source verification before submission

### DEC-018 - Use visible thesis traceability checks instead of a hidden Git hook

- Date: 2026-05-04
- Status: accepted
- Decision: add explicit local scripts that check source-reference coverage and thesis-documentation coverage before GitHub checkpoints, but do not install a Git hook by default
- Why:
  - the project is both a product and a thesis workspace
  - meaningful changes should remain explainable later during thesis writing
  - hidden hooks are local-only, easy to forget across machines, and can become frustrating if they block work invisibly
  - visible scripts make the rule auditable and portable
- Alternatives considered:
  - rely on manual memory during each push
  - install a pre-push hook immediately
  - auto-edit thesis docs from a script
- Consequences:
  - `check_thesis_reference_registry.py` should pass before pushing source-backed work
  - `check_thesis_update_gate.py` should pass before GitHub checkpoints
  - scripts report and recommend, but do not auto-write thesis content
  - an optional hook can be added later if the command-based workflow proves stable
