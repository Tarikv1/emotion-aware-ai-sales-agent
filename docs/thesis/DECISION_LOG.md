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

### DEC-034 - Keep generated experiment artifacts grouped by checkpoint folder

- Date: 2026-05-07
- Status: accepted
- Decision: move generated experiment artifacts out of the flat `research/experiments/generated/` root and keep future outputs inside milestone or run folders, with only `README.md` allowed at the generated root.
- Why:
  - the flat generated folder had become too large to audit quickly before GitHub checkpoints
  - grouped artifacts make RAG, voice, response, guard, language, and product evidence easier to review independently
  - live-provider audio must stay ignored unless it is deliberately curated
  - the drift guard needs a concrete rule that catches accidental new flat files instead of relying on manual inspection
- Alternatives considered:
  - keep all generated artifacts in the root and depend on filename prefixes
  - exclude all generated artifacts from Git
  - reorganize only new artifacts while leaving older artifacts flat
- Consequences:
  - existing generated reports/results are preserved under checkpoint folders where practical
  - `research/experiments/generated/README.md` records the convention
  - `check_project_drift.py` now fails on unexpected flat generated-root files
  - generated `.wav` and `.mp3` files under nested output folders remain ignored by default
  - thesis and product claims should cite the checkpoint folder, not an unstable flat filename

### DEC-033 - Enable guarded local RAG retrieval only as explicit opt-in

- Date: 2026-05-07
- Status: accepted
- Decision: finish RAG-016B voice/prosody acceptance, build RAG-017 as a local registry of accepted project-owned rules, and connect retrieval to RESP-001 only behind explicit CLI enablement.
- Why:
  - the remaining voice/prosody material is useful as delivery guidance but unsafe as hidden-emotion or buying-intent inference
  - source-mapping blockers and latent quote follow-ups are still unresolved and must stay out of retrieval
  - the product needs traceable runtime hints without adding a vector DB, embedding provider, private data access, or provider dependency
  - campaign guardrails, protected text, refusal handling, do-not-call, and human escalation must outrank retrieved guidance
- Alternatives considered:
  - keep all RAG artifacts review-only until every source-mapping blocker is resolved
  - enable retrieval globally once the registry exists
  - add an embedding/vector retrieval service now
- Consequences:
  - RAG-017 registry artifacts still mark runtime retrieval as disabled by default
  - RESP-001 emits retrieval status for every run, but only uses retrieval when `--retrieval-enabled` is passed
  - refusal, do-not-call, human escalation, protected text, pressure-sensitive, and private-data contexts block retrieval influence
  - voice/prosody retrieval can produce advisory hints only and cannot alter protected text or claim hidden emotion

### DEC-032 - Automate NotebookLM extraction prompts but keep local coverage gates

- Date: 2026-05-06
- Status: accepted
- Decision: implement `RAG-002` as a local NotebookLM extraction automation bridge that generates bounded per-topic prompts and rejects incomplete or small-batch outputs before any RAG promotion.
- Why:
  - Tarik already has real sources organized in NotebookLM, but manual extraction is tedious
  - NotebookLM may return a short batch or summary instead of exhaustive topic coverage
  - prompts must stay under a configurable character limit to avoid UI input failures
  - the product needs source-tracked chunks, not unverified chat notes
  - local validation should enforce completion markers, source IDs, topic IDs, and no-private-data boundaries
- Alternatives considered:
  - manually prompt NotebookLM until each topic feels complete
  - automate the personal NotebookLM UI through browser scraping
  - wait for NotebookLM Enterprise API integration before doing any extraction
- Consequences:
  - RAG-002 creates two prompts per topic: a primary exhaustive report/chunk prompt and a gap-check prompt
  - the default prompt character limit is `4500`
  - tiny outputs are rejected unless NotebookLM explicitly marks source material as insufficient
  - NotebookLM remains an extraction helper, not permanent product memory or runtime retrieval

### DEC-031 - Use NotebookLM as an extraction helper, not product memory

- Date: 2026-05-06
- Status: accepted
- Decision: implement `RAG-001` as a local NotebookLM source-intake bridge that produces source-tracked, paraphrased chunks for the Emotion Aware sales RAG base. NotebookLM is not the permanent memory store and runtime retrieval is not enabled yet.
- Why:
  - Tarik is collecting many public sources across sales, persuasion, speech, and dataset topics
  - the thesis needs a durable path from sources to references and extracted lessons
  - NotebookLM can speed up extraction, but the product should not depend on NotebookLM as its memory layer
  - every future RAG chunk needs source IDs, topic IDs, usage boundaries, compliance notes, and citation notes
  - raw copied source text, full transcripts, private call-center data, and unsourced claims must be blocked
- Alternatives considered:
  - keep a manual list of links in chat
  - use NotebookLM notebooks as the permanent product memory
  - jump directly to runtime retrieval before source validation
- Consequences:
  - RAG now has a 10-topic taxonomy and source-slot manifest
  - future NotebookLM output can be imported only if it validates against the chunk schema
  - RAG runtime retrieval is deferred until `RAG-002` or later
  - thesis source traceability improves because extracted knowledge can be tied back to manifest records

### DEC-030 - Correct low-pressure emphasis through provider-facing wording

- Date: 2026-05-06
- Status: accepted
- Decision: implement `VOICE-040` as a runtime layer that rewrites the provider-facing English phrase `You don't need to change anything today` to `No changes needed today` only when the text is freeform and prosody-eligible.
- Why:
  - Tarik's VOICE-039 listening review found that the selected English voice is now strong enough to keep using
  - the remaining issue is wrong emphasis inside a specific low-pressure phrase, not the guarded sales decision
  - the original phrase has too many tempting emphasis targets for a TTS model
  - shortening the phrase keeps the same sales meaning while reducing unnatural stress placement
  - protected campaign/compliance/handoff/do-not-call text and German text must stay locked
- Alternatives considered:
  - keep the VOICE-039 wording unchanged and rely on the provider voice
  - add markup or emphasis tags around the phrase
  - rewrite the guarded `final_response` directly
- Consequences:
  - RESP-002 now includes `voice_low_pressure_focus`
  - RESP-003 may speak the corrected provider-rendered text only when validation passes
  - the next checkpoint is a short live VOICE-040 listening check with the preferred English voice
  - broader semantic-emphasis expansion should wait for RAG/source-tracked sales knowledge and more listening evidence

### DEC-029 - Promote clear/simple wording as provider-facing TTS only

- Date: 2026-05-06
- Status: accepted
- Decision: implement `VOICE-039` as a runtime candidate that promotes the `VOICE-038` clear/simple worth-your-time phrase into provider-facing English TTS text while preserving the original guarded `final_response`.
- Why:
  - Tarik preferred the clear/simple VOICE-038 variant and also accepted the baseline as a control
  - the remaining issue is phrase-level naturalness, not sales policy or campaign strategy
  - changing only provider-facing TTS text lets us test naturalness without changing what the agent officially decided to say
  - protected campaign/compliance/handoff/do-not-call text must remain exact
  - German should not be rewritten by an English semantic-emphasis rule
- Alternatives considered:
  - rewrite the guarded final response directly
  - keep VOICE-038 as a diagnosis only and postpone runtime testing
  - continue searching for more voices before testing the selected wording pattern
- Consequences:
  - RESP-002 now includes `voice_semantic_emphasis`
  - RESP-003 may speak the promoted provider-rendered text only when the response is freeform and validation passes
  - the next checkpoint is a short live RESP-003 listening check with a longer script
  - future semantic-emphasis expansion should stay pattern-based and campaign-safe unless a broader RAG/LLM layer is reviewed

### DEC-028 - Keep the preferred English voice and promote clear/simple wording next

- Date: 2026-05-06
- Status: accepted
- Decision: keep the current preferred English ElevenLabs voice candidate in active use and make `clear_opening_simple_clause` the lead runtime-promotion candidate, with `baseline_original_clause` retained as an acceptable fallback/control.
- Why:
  - Tarik reported that all VOICE-038 variants sounded good and several steps above earlier outputs
  - the current preferred English voice made one of the strongest improvements in the project so far
  - roboticness is no longer the main English bottleneck for this voice
  - `clear_opening_simple_clause` is shorter and simpler, so it is less likely to create awkward emphasis in future runtime responses
  - `baseline_original_clause` also sounded good, which confirms the voice candidate solved much of the original issue
- Alternatives considered:
  - keep searching for another English voice immediately
  - promote the original baseline wording only
  - add more filler, pause, or pacing randomness before selecting a wording pattern
- Consequences:
  - the next checkpoint should test runtime promotion of the clear/simple wording pattern
  - the baseline should remain available as a control when comparing runtime changes
  - broader voice hunting should pause unless later runtime checks reveal a voice-specific limitation

### DEC-027 - Diagnose semantic emphasis before promoting new English wording

- Date: 2026-05-06
- Status: accepted
- Decision: implement `VOICE-038` as a diagnostic listening checkpoint before changing the runtime response wording or prosody rules for the preferred English voice.
- Why:
  - the preferred English voice mostly solved roboticness
  - the remaining issue is a specific rhythm/emphasis break around a single clause
  - changing runtime wording without an A/B listening diagnosis could trade one unnatural phrase for another
  - a dry-run/live-capable checkpoint keeps provider calls explicit and keeps quality claims tied to human listening
- Alternatives considered:
  - immediately rewrite the runtime response template
  - keep searching for more voices before testing wording
  - add emphasis tags or markdown-like instructions directly to TTS text
- Consequences:
  - VOICE-038 compares six synthetic English variants with the same voice
  - the checkpoint is dry-run by default and live only with `--live`
  - no runtime behavior changes until Tarik selects a winning variant
  - future semantic-emphasis rules should be based on the winning listening pattern, not assumptions

### DEC-026 - Prioritize English voice candidate selection before adding more prosody rules

- Date: 2026-05-06
- Status: accepted
- Decision: keep the current preferred English ElevenLabs candidate in active testing and treat the next English naturalness step as semantic emphasis diagnosis before adding more filler, pause, pacing, or emotion-smoothing rules.
- Why:
  - Tarik's live RESP-003 check with a new English ElevenLabs voice candidate reduced the obvious robotic voice quality by about 95%
  - Tarik rated sales trust as good enough to keep working with this voice
  - this suggests the previous English voice identity/model choice was a major cause of the AI-generated sound
  - the new candidate still broke rhythm/emphasis around a specific clause, so the remaining issue is semantic emphasis alignment rather than general roboticness alone
  - more local filler/pacing randomization could hide the problem without solving the actual emphasis mismatch
- Alternatives considered:
  - keep tuning VOICE-035/VOICE-036/VOICE-037 rules first
  - add a broader phrase-believability rewrite layer immediately
  - compare multiple TTS providers before selecting a better English voice
- Consequences:
  - the current preferred English candidate should be tested with the current RESP-003 runtime path before runtime-rule changes
  - voice IDs remain in environment variables or ignored local config, not tracked source
  - the next checkpoint should compare candidate voices and then decide whether `VOICE-038` needs semantic emphasis selection

### DEC-025 - Smooth vocal emotion with provider settings before rewriting text

- Date: 2026-05-06
- Status: accepted
- Decision: implement `VOICE-037` as an emotion-transition smoothing layer after VOICE-036 and before live TTS.
- Why:
  - Tarik identified that the agent's vocal emotion can jump too sharply between phrases
  - human speech usually has emotional inertia rather than instant mood changes
  - the issue should be solved as delivery control before adding more filler words or rewriting guarded sales text
  - provider settings can reduce theatrical swings while preserving speed and rendered words
- Alternatives considered:
  - change response wording to include more emotional transition phrases
  - add more filler or pause rules
  - retune the ElevenLabs voice identity again before runtime control
- Consequences:
  - VOICE-037 raises provider stability only within a bounded range when sharp transitions are detected
  - VOICE-037 caps style/exaggeration when over-emotional cues appear
  - speed, final response, and protected text stay unchanged
  - live audio still needs human listening review before claiming quality improvement

### DEC-024 - Read raw audio locally before transcription or runtime personalization

- Date: 2026-05-05
- Status: accepted
- Decision: implement `VOICE-030A` as a local WAV audio feature reader before adding local ASR transcription or mapping personal speech patterns into runtime voice settings.
- Why:
  - raw audio contains the pause, rhythm, energy, and speech-burst information that transcript text cannot capture
  - Tarik specifically wants the agent to learn from speech patterns, not just words
  - extracting acoustic features can be done without provider calls, transcription, voice cloning, or raw transcript export
  - keeping ASR as a separate checkpoint makes privacy and failure modes easier to review
- Alternatives considered:
  - jump directly to local ASR transcription
  - upload recordings to a cloud ASR provider
  - apply inferred personal style directly to runtime voice settings
- Consequences:
  - `VOICE-030A` supports WAV only until a local decoder/conversion path is reviewed
  - private raw-audio analysis requires `--allow-private-read`
  - private-input outputs must stay under `data/private/`
  - runtime personalization still requires later human review and validation

### DEC-023 - Start personal speech learning as local abstract profiles, not audio training

- Date: 2026-05-05
- Status: accepted
- Decision: implement `VOICE-029` as a local-only abstract speech-profile extractor before any raw audio transcription, voice cloning, or runtime personalization.
- Why:
  - Tarik wants the agent to learn from how he speaks, especially imperfections, phrasing, pauses, and repair patterns
  - the privacy boundary must be stronger than the feature excitement
  - raw personal recordings and transcripts should not leave `data/private/`
  - runtime changes should be reviewed before the agent starts copying a personal style
- Alternatives considered:
  - directly train/fine-tune on recordings
  - send recordings to an external ASR provider
  - immediately wire personal profile outputs into the live runtime
- Consequences:
  - default VOICE-029 runs use synthetic fixtures and generate public-safe aggregate artifacts
  - actual Tarik speech inputs require `--allow-private-read`
  - private-input outputs stay under `data/private/`
  - the profile is not applied to runtime by default
  - future checkpoints must add local transcription and reviewed runtime mapping separately

### DEC-022 - Add controlled delivery imperfections before personal speech-pattern learning

- Date: 2026-05-05
- Status: accepted
- Decision: implement an opt-in `VOICE-028` controlled delivery imperfection layer before building a local Tarik speech-pattern learning workflow.
- Why:
  - listening feedback showed that machine-perfect delivery is still a realism problem even after better custom voices, spoken-text normalization, filler placement, and interaction prosody
  - imperfections must be bounded and professional, not random stutters or sloppy delivery
  - protected campaign questions, disclosures, handoff scripts, hangup lines, and regulated claim boundaries must stay exact
  - the later Tarik speech-learning idea needs a clear local-only privacy boundary before any samples are collected
- Alternatives considered:
  - tune provider pacing first
  - jump directly into learning from Tarik speech samples
  - rely on ElevenLabs voice remixing alone
- Consequences:
  - `VOICE-028` is campaign opt-in and disabled by default for existing campaigns
  - visible imperfections are suppressed in unsafe claim, stop-intent, anger, and protected-text contexts
  - future Tarik speech samples should live only under `data/private/tarik-speech-samples/`
  - only reviewed abstract speech-pattern notes may leave `data/private/`; no raw audio, no raw transcript export, no provider upload, and no voice cloning by default

### DEC-021 - Add interaction-prosody separation before the next live voice comparison

- Date: 2026-05-04
- Status: accepted
- Decision: implement a `VOICE-026` interaction-prosody/backchannel checkpoint before treating VOICE-025 as ready for the next serious live ElevenLabs comparison
- Why:
  - the deep English/German speech-pattern review showed that filler placement alone cannot solve robotic speech
  - speaker fillers, discourse markers, listener backchannels, latency acknowledgments, speech rate, pitch/intonation, and provider prosody controls have different conversational functions
  - German tokens such as `ja`, `okay`, `genau`, and `also` can sound natural but can also imply agreement if used in the wrong context
  - regulated or campaign-exact text must remain protected from casual hesitation, emotion, and speed variation
- Alternatives considered:
  - run VOICE-025 live audio immediately
  - keep adding more fillers to VOICE-023/VOICE-025
  - rely on ElevenLabs custom voice/remixing alone
- Consequences:
  - the next voice checkpoint should add separate English/German rules for backchannels, discourse markers, pause/prosody cues, and faster-but-bounded sales pace
  - live audio comparison should include `VOICE-026` output against boundary-aware fillers and pause-only cues
  - thesis claims should frame this as literature-informed design until native/proficient listening evaluation and private call-pattern analysis support stronger conclusions
- Implementation note: `VOICE-026` was implemented on 2026-05-04 as an offline/runtime layer for lookup acknowledgements, neutral backchannels, bounded sales-pace cues, unsafe-agreement guards, protected-text locks, and a listening rubric.
- Follow-up note: `VOICE-027` was added on 2026-05-05 as the live-capable A/B harness for comparing the current `VOICE-025` baseline against `VOICE-026` interaction prosody.

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

### DEC-019 - Insert speech realism after spoken-text normalization and before prosody

- Date: 2026-05-04
- Status: accepted
- Decision: apply VOICE-023 after VOICE-022 spoken-text normalization, then pass the resulting realistic freeform text into prosody and provider rendering
- Why:
  - fillers and thinking behavior should operate on the text that will actually be spoken
  - protected text must already be identified and preserved before naturalness layers run
  - prosody should see the final delivery text so pauses and provider tags align with filler placement
- Alternatives considered:
  - add fillers before spoken-text normalization
  - fold VOICE-023 into VOICE-015 prosody only as metadata
  - rely only on ElevenLabs voice design/remixing instead of local guardrails
- Consequences:
  - provider `plain_text` may differ from VOICE-022 `tts_text` when VOICE-023 inserts safe fillers
  - validators must compare provider input against the latest runtime delivery layer, not only the spoken-normalization layer
  - `final_response` remains unchanged and is still the guarded source of truth

### DEC-020 - Evaluate VOICE-023 with an A/B listening harness before claiming quality

- Date: 2026-05-04
- Status: accepted
- Decision: compare the same improved ElevenLabs English/German voices with and without VOICE-023 before deciding whether speech realism should be strengthened, reduced, or moved partly into provider voice design
- Why:
  - user listening feedback is currently the strongest signal for perceived naturalness
  - provider voice quality and local speech-realism rules must not be mixed into one unclear result
  - live provider calls need explicit API-key, timeout, local voice-ID, and redaction gates
- Alternatives considered:
  - immediately tune VOICE-023 based on dry-run text only
  - rely only on ElevenLabs remixing prompts
  - compare multiple providers before isolating the local speech-realism layer
- Consequences:
  - `VOICE-024` becomes the current listening checkpoint
  - default runs remain dry-run and provider-safe
  - live MP3s are local ignored artifacts and are not thesis evidence until Tarik records listening observations
