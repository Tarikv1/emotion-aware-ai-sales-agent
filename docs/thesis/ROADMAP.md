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

Active phase: source-tracked RAG foundation, voice/runtime quality, and thesis evidence preservation.

Current checkpoint:

- [ ] Current: design `RAG-011` source-mapping and quote-clearance cleanup for blocked RAG-009 queues before any runtime integration work.

Next checkpoints:

- [ ] Next: record Tarik's VOICE-040 longer-script listening review and decide whether the low-pressure focus correction stays active, needs another wording pass, or should be campaign-configurable.
- [ ] Next: test one or two additional English voice candidates only if `VOICE-038` shows the emphasis problem is mostly voice-specific rather than text/prosody-specific.
- [ ] Next: keep collecting local Tarik speech samples and use `VOICE-033` to decide when the private sample set is ready for `VOICE-030D`.
- [ ] Next: use `VOICE-032` when Tarik exports WhatsApp `.ogg` voice notes into `data/private/tarik-speech-samples/whatsapp-voice-notes/`, converting them locally to WAV before VOICE-030C/VOICE-030D review once ffmpeg is available.
- [ ] Next: run `VOICE-030D` on Tarik's real private English WAV feature set and review whether any non-pause acoustic candidates are useful.
- [ ] Next: use `VOICE-031` on the reviewed private `VOICE-030D` summary to prepare campaign-level voice-setting proposals, still without automatic runtime application.
- [ ] Next: add local transcription support for Tarik speech samples only after a local ASR option is selected and the no-provider/no-upload boundary is validated.
- [ ] Next: add local audio conversion/decoder support for manually imported MP3, M4A, AAC, OGG, FLAC, or WebM files.
- [ ] Next: map reviewed `VOICE-029` aggregate profile outputs into campaign-level voice settings only after human review confirms they improve naturalness without reducing professionalism.
- [ ] Next: implement provider pacing tuning using VOICE-027/VOICE-028 feedback as the baseline and changing pacing only before touching markers, emotion, or voice identity again.
- [ ] Next: connect `RESP-003` audio output to the local demo/playback flow after dry-run, missing-key, timeout, and asset-log gates remain stable.
- [ ] Next: expand `RESP-002` from single-response segment wrapping to multi-segment runtime packets when campaign questions or disclosures are spoken in the same turn.
- [ ] Next: after `RAG-011` reduces source-mapping and quote-clearance blockers, decide whether to wire reviewed retrieval into a runtime-off integration harness or keep RAG as review-only while strengthening universal objection handling.
- [ ] Next: resume the product-learning track by strengthening the reusable sales core against universal objections before broad industry expansion.
- [ ] Next: continue dataset-grounded thesis expansion once the current voice/runtime checkpoint is stable.

Recently completed checkpoints:

- [x] `RAG-010` reviewed expansion slice, which promoted all `4` clean RAG-009 next-promotion candidates into project-owned paraphrased review items: `3` consultative response-wording rules and `1` voice-delivery advisory rule. It rewrote impact, so-what, and timing guidance as low-pressure discovery; rewrote cadence detection as weak context only, not hidden-emotion inference; stored no source excerpt text; made no provider or NotebookLM calls; used no private customer data; auto-promoted `0` chunks; and kept runtime retrieval plus chunk import disabled.
- [x] `RAG-009` all-source review coverage, which accounted for all `95` RAG-004 sources and all `121` RAG-005 chunk candidates, carried forward the `9` manually reviewed RAG-007 chunks, identified `4` clean next-promotion candidates, blocked `63` chunks for source mapping and `42` for quote clearance, rejected `3` safety-risk chunks, stored no source excerpt text, made no provider or NotebookLM calls, used no private customer data, auto-promoted `0` chunks, and kept runtime retrieval plus chunk import disabled.
- [x] `RAG-008` guarded retrieval policy dry-run, which queried only the `RAG-007` reviewed first slice with `8` synthetic cases, produced candidate packets for `3` retrieved cases, blocked `5` hard-guard contexts, retrieved `7` packets across `6` unique knowledge items, kept Vinh-informed voice/prosody guidance advisory only, stored no source excerpt text, made no provider or NotebookLM calls, used no private customer data, auto-promoted `0` chunks, and kept runtime retrieval plus chunk import disabled.
- [x] `RAG-007` reviewed first slice, which promoted `9` manually reviewed, project-owned paraphrased knowledge items from RAG-006/RAG-005 into a review artifact only: `5` response-wording items and `4` voice-delivery items. The selected chunks were RAG-006 quote-queue candidates, so RAG-007 records `9` manual quote clearances before any retrieval-policy work. It excluded pressure tactics and sensitive demographic personalization, rewrote tone-mismatch guidance as uncertainty plus clarification rather than emotion certainty, stored no source excerpt text, made no provider or NotebookLM calls, used no private customer data, and kept runtime retrieval plus chunk import disabled.
- [x] Vinh Giang communication/voice report import and RAG refresh, which added a new NotebookLM report covering `40` Vinh Giang YouTube sources, regenerated RAG-003 through RAG-006, increased the report set to `11`, increased source candidates to `95`, increased chunk candidates to `121`, mapped chunks to `58`, and kept runtime retrieval plus chunk import disabled.
- [x] `RAG-006` chunk review packet, which grouped the refreshed `121` RAG-005 candidates into `46` source-title review groups covering `63` source-mapping chunks, `8` topic-mapping rows, `80` quote-review rows, and `20` first-slice review candidates. It tightened source suggestions to higher-confidence review hints only, auto-promoted `0` chunks, stored no source excerpt text, made no provider/NotebookLM calls, and kept runtime retrieval plus chunk import disabled.
- [x] `RAG-005` chunk normalization, which parsed the eleven imported NotebookLM reports into `121` metadata-only chunk candidates, mapped `58` candidates to RAG-004 source IDs, queued `63` for source-mapping review, flagged `8` off-taxonomy topic labels for review, flagged `80` source-excerpt references for quote review without copying excerpt text forward, detected no secret-like chunk fields, and kept runtime retrieval plus chunk import disabled.
- [x] `RAG-004` source manifest normalization, which scanned the eleven imported NotebookLM reports, extracted `95` metadata-only source candidates, assigned stable `rag004-source-*` IDs, linked every candidate to at least one topic, detected no secret-like source titles, kept runtime retrieval and chunk import disabled, and marked all candidates as needing human metadata review before chunk normalization.
- [x] `RAG-003` NotebookLM report import-readiness audit, run after Tarik imported all NotebookLM reports and pasted gap-check/continuation material into the RAG-002 imports folder. After Tarik added the missing voice/prosody source-coverage addendum and the Vinh Giang communication report, the audit found `10 / 10` topic coverage across `11` report files, source coverage on all reports, RAG appendices on all reports, `END: COMPLETE` on all reports, no `NEED_CONTINUATION`, and no secret-like strings. It deliberately kept runtime retrieval disabled and marked the imports as `review_required` because source-title mapping, pasted continuation normalization, and quote review still need cleanup before chunk import.
- [x] `RAG-002` NotebookLM extraction automation bridge, with Configure Chat custom instructions under the `10000` character UI limit, a NotebookLM Reports / Create report prompt as the first per-topic artifact, optional chat/JSON and gap-check prompts, a default `4500` character topic-prompt limit, `END: COMPLETE` and `NEED_CONTINUATION` markers, local small-batch rejection, generated prompt folders, import drop zone, no NotebookLM API calls, no raw source text, no private/customer data, and no runtime retrieval yet.
- [x] `RAG-001` NotebookLM source-intake bridge, with the 10 active source topics from Tarik, a source-slot manifest, NotebookLM extraction prompt, source-tracked chunk schema, local validator, generated knowledge-base preview, no real source URLs by default, no raw source text, no private/customer data, no NotebookLM API calls, and no runtime retrieval yet.
- [x] Tarik's `VOICE-039` longer-script listening review. The selected English voice candidate is now good enough to keep using, and the main bottleneck is no longer voice identity. The remaining issue is narrower: the phrase `You don't need to change anything today` can receive wrong TTS emphasis, so the next correction should target the provider-facing low-pressure phrase rather than search for another voice.
- [x] `VOICE-040` low-pressure focus correction, which rewrites the provider-facing English freeform phrase `You don't need to change anything today` to `No changes needed today` after VOICE-039, while preserving the guarded `final_response`, protected campaign/compliance/handoff/do-not-call text, German text, no-provider default, no private/customer audio, no voice cloning, and validation through RESP-002/RESP-003 hooks.
- [x] `VOICE-039` runtime semantic-emphasis promotion, which promotes the `VOICE-038` clear/simple worth-your-time pattern into provider-facing English TTS text only. It preserves the guarded `final_response`, leaves protected campaign/compliance/handoff/do-not-call text exact, locks German against the English rewrite rule, adds a longer full-runtime RESP-003 runner, and validates dry-run plus forced-missing-key boundaries before live listening.
- [x] Live `VOICE-038` listening review with the current preferred English ElevenLabs voice. All six variants sounded good and several steps above earlier outputs; Tarik could not clearly rank all variants because emphasis, rhythm, and pronunciation were generally strong. Preferred variants were `clear_opening_simple_clause` and `baseline_original_clause`. The clear/simple clause is the lead runtime-promotion candidate, while the baseline remains an acceptable fallback/control.
- [x] `VOICE-038` semantic emphasis/rhythm diagnosis scaffold, with six controlled English variants around the fragile clause "whether reviewing options is worth your time," dry-run by default, explicit live opt-in, no raw voice/API logging, no private/customer audio, no voice cloning, no runtime behavior change, and validation for dry-run and forced-missing-key provider boundaries.
- [x] Short `RESP-003` live English voice-candidate check after VOICE-037. The current preferred English ElevenLabs candidate reduced the obvious robotic/AI-generated sound by roughly 95% and sounded trustworthy enough to keep testing. The remaining issue is narrower: phrase-level rhythm/emphasis broke around "whether reviewing options is worth your time," so the next useful work is semantic emphasis diagnosis rather than adding more filler or pacing randomness.
- [x] `VOICE-037` emotion-transition smoothing, created after Tarik noticed that vocal emotion could change too sharply between phrases. The layer adds emotional inertia by detecting sharp delivery-intent transitions, blocking over-emotional cues, raising provider stability within a bounded range, capping style/exaggeration, preserving speed and rendered words, preserving protected text, and keeping provider/private-data boundaries offline by default.
- [x] `VOICE-036` listening-feedback calibration, created after Tarik's VOICE-035 live review found German too compressed/fast and English improved but still vulnerable to wrong-word emphasis. The layer blocks weak emphasis targets such as `practical`, restores a tiny German breath cue after connected acknowledgements, relaxes German speed to a clearer range, preserves protected text, and keeps provider/private-data boundaries offline by default.
- [x] Short `RESP-003` live listening check with `VOICE-035` active. German sounded too fast and compressed to judge pauses/fillers clearly; English sounded better than before but still somewhat robotic, with likely emphasis placement problems.
- [x] `VOICE-035` bilingual connected-speech phrase-flow tuning, with runtime integration after `VOICE-034`, English/German freeform phrase joins for obvious filler/bridge boundaries, preserved VOICE-034 speed bounds, protected campaign/compliance/do-not-call/handoff text locks, no provider calls, no generated audio, no private audio, no transcription, no voice cloning, standalone runner/report, and RESP-002/RESP-003 validation hooks.
- [x] Short `RESP-003` live listening check with `VOICE-034` active and local improved ElevenLabs voice IDs selected. German pacing and gaps sounded good; English pacing and pause timing sounded good; second listen found some roboticness in German too. Remaining roboticness appears more related to bilingual connected speech, phrase rhythm, pronunciation, or word-to-word flow than to pause length. VOICE-034 bounds stay unchanged.
- [x] `VOICE-034` pacing calibration V2, with offline provider-rendering calibration after `RESP-002`, faster bounded English/German sales-call speed, German-specific word-gap reduction after listening feedback, compressed provider break tags, protected campaign/compliance/do-not-call text locks, no new filler insertion, no provider calls, no generated audio, no private audio, no transcription, no voice cloning, and validation through runtime and standalone runner checks.
- [x] `VOICE-033` private speech sample readiness report, with explicit private metadata-read opt-in, aggregate counts for analyzed WAV features, WhatsApp OGG files waiting for conversion, legacy non-WAV files needing conversion, failed analysis/conversion records, language/source/status summaries, readiness statuses for first review versus stronger pattern review, private-only JSON/Markdown readiness outputs, no raw audio content reads, no transcription, no provider calls, no voice cloning, no runtime auto-application, and no public generated artifact from private metadata.
- [x] `VOICE-032` local WhatsApp OGG audio conversion gate, with `.ogg` as the first-class WhatsApp export format, local ffmpeg conversion to mono 16 kHz WAV when available, `converter_missing_needs_local_ffmpeg` status when ffmpeg is absent, private-only input/output under `data/private/`, a local WhatsApp drop-folder README, automatic VOICE-030C queue handoff for successful WAVs, no provider calls, no transcription, no voice cloning, no runtime auto-application, and no public generated artifact from private audio.
- [x] `VOICE-031` reviewed feature-to-runtime mapping gate, with a synthetic public default, private `VOICE-030D` summary read opt-in, private-derived output locked to `data/private/`, blocked pause-ratio and pause-duration runtime mapping, review-only rhythm/expressiveness/presence proposals, campaign override requirement, protected-text locks, no provider calls, no transcription, no raw audio reading, no voice cloning, no runtime auto-application, and a deferred WhatsApp voice-note import reminder tied to the future `VOICE-030D` review moment.
- [x] `VOICE-030D` private feature review summary, with private-read opt-in, private JSON/Markdown review outputs, aggregate English WAV feature summary, pause-ratio and pause-duration metrics excluded from runtime candidates, no raw audio paths, no public artifacts, no provider calls, no transcription, no voice cloning, and no runtime auto-application.
- [x] `VOICE-030C` private learning queue, with automatic post-capture/import hook, immediate private WAV acoustic analysis, non-WAV `needs_local_conversion` status, speaker context that learns timing/rhythm/clear English delivery without cloning or overfitting to one speaker identity, pause-ratio and pause-duration metrics marked diagnostic-only, no raw audio paths in the queue manifest, no provider calls, no transcription, no voice cloning, and no runtime auto-application.
- [x] `VOICE-030B` local speech capture/import, with localhost browser recorder, browser-side WAV encoding, existing-file import, private raw-audio storage, private JSONL manifest, no provider calls, no transcription, no voice cloning, no runtime auto-application, and validation that public artifacts are not created.
- [x] `VOICE-030A` raw WAV audio local reader, with synthetic fixture default, private-read opt-in, aggregate pause/rhythm/energy features, private-output guard, no transcription, no provider calls, no voice cloning, no runtime auto-application, and process-scoped temp audio folders after a Windows file-lock correction.
- [x] `VOICE-029` local speech profile learning scaffold, with synthetic default fixture, private-read opt-in, ignored `data/private/tarik-speech-samples/` workspace, abstract aggregate speech-pattern extraction, no raw audio reading, no provider calls, no voice cloning, and no automatic runtime use.
- [x] `VOICE-028` offline controlled delivery imperfections layer, with opt-in English/German professional imperfections, protected-text locks, unsafe-claim/stop-intent suppression, RESP-002 runtime integration, no provider calls, no private audio, and generated offline artifacts.
- [x] `VOICE-027` limited live listening review: Tarik reported the output sounds much better than earlier voice checkpoints, with pacing now the main remaining tuning target.
- [x] `VOICE-027` live-capable A/B harness comparing `voice_025_baseline` against `with_voice_026`, with English/German synthetic scripts, dry-run default, forced-missing-key fallback, raw voice-ID redaction, no private/customer audio upload, no voice cloning, protected-text locks, and unsafe-agreement guards.
- [x] `VOICE-026` interaction-prosody layer, separating lookup acknowledgements, neutral backchannels, and bounded sales-pace cues from filler placement, with English/German unsafe-agreement guards, protected-text locks, RESP-002 runtime integration, a listening rubric, and generated offline report.
- [x] `SPEECH-STYLE-003` final broad speech-realism sweep, adding general prosody, acoustic emotion, vocal first impressions, turn-taking distributions, spoken-dialogue timing, entrainment, connected speech, spoken corpora, acoustic charisma, and TTS evaluation references before `VOICE-026`.
- [x] `SPEECH-STYLE-002` deep English/German speech-pattern review, covering speaker fillers, discourse markers, listener backchannels, turn-taking timing, provider prosody controls, breath/smiled speech, and sales/call-center vocal cues.
- [x] `VOICE-025` boundary-aware filler placement implementation, with English/German rules, German-specific `also`/`äh`/`ähm` handling, protected campaign text locks, a dedicated offline case set, runner, validator, and generated report.
- [x] `VOICE-024` dry-run/live-capable A/B harness comparing the same improved English/German voice with and without VOICE-023 speech realism, including local voice-ID redaction, forced missing-key fallback, protected-text checks, generated live MP3 organization, and generated evaluation packet.
- [x] `VOICE-023` offline speech-realism layer with English/German bounded thinking-filler bundles, protected-text locks, customer stop/anger suppression, and RESP-002/RESP-003 runtime integration.
- [x] `TRACE-001` pre-push thesis traceability automation, including source-reference coverage and thesis-update gates before GitHub checkpoints.
- [x] `REF-001` central thesis reference registry and expanded thesis writing map, collecting dataset, provider, privacy, sales-objection, speech-realism, and open-source inspiration sources.
- [x] `SPEECH-STYLE-001` thesis reference capture for English/German speech realism, including fillers, pauses, breath cues, smiled speech, and the guardrail against language stereotypes.
- [x] `PRIVATE-CALL-LEARNING-001` local-only private call-center learning scaffold, with raw audio kept under `data/private/`, pattern-mining before fine-tuning, redaction and human-review gates before export, and positive/negative sales-pattern learning documented.
- [x] `VOICE-021` live custom ElevenLabs voice comparison. Improved English and German voices were clearly preferred; remaining gap is believable thinking behavior, bounded hesitation, and more natural pitch movement.
- [x] `VOICE-021` dry-run custom ElevenLabs voice comparison harness for English/German original-vs-improved voices, using local-only voice IDs and redacted generated artifacts.
- [x] `VOICE-022` bilingual spoken-text normalization for English contractions and conservative German spoken forms, wired into `RESP-002` and `RESP-003` while preserving guarded `final_response` and protected text.
- [x] `VOICE-020` offline ElevenLabs-first voice design packet with English/German voice prompts, settings candidates, emotional delivery bundles, protected-text locks, and private-audio tuning boundaries.
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
| Private call-center learning on real recordings and later fine-tuning | The local-only scaffold now exists, but real recordings, local transcription, redaction, labeling quality, retention/deletion handling, and training-data review are not implemented yet | Client-approved audio exists under local-only `data/private/`; local ASR and speaker segmentation work without provider upload; private identifiers are removed as non-training signal; sensitive fields are minimized; pattern notes pass human review; RAG baseline has been evaluated before any fine-tuning | Private-data learning | Deferred |
| Tarik personal speech-pattern learning | Raw WAV feature extraction and transcript-pattern scaffolds now exist, but actual private recordings/transcripts have not been processed and runtime mapping is not reviewed | Local audio/transcripts exist under `data/private/tarik-speech-samples/`; `VOICE-030A` and `VOICE-029` private runs create draft profiles; Tarik reviews them; runtime settings are mapped manually and validated | Voice/runtime | Partially implemented |
| Optional WhatsApp voice-note import for Tarik speech-pattern learning | Helpful extra samples, but source mixing should wait until the first local speech-sample review decision so the analysis stays interpretable | Tarik decides to run `VOICE-030D` and wants more sample coverage; selected `.ogg` files are placed under `data/private/tarik-speech-samples/whatsapp-voice-notes/`, converted by `VOICE-032`, and reviewed before runtime use | Voice/runtime private learning | Deferred, conversion path ready |

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

Speech realism should now be language-aware without becoming stereotype-driven. `SPEECH_REALISM_REFERENCES.md` records sources for English and German fillers, pauses, breath cues, and audible warmth. `VOICE-023` should use those references to create bounded speech profiles while keeping campaign persona separate from language mechanics.

The thesis reference trail is centralized in `THESIS_REFERENCE_REGISTRY.md`. Future source-backed work should add sources there or point to the specific detailed source note.

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
- VOICE-021 dry-run ElevenLabs custom voice comparison for English/German original-vs-improved voices with local-only voice IDs
- VOICE-021 live comparison result: improved English/German voices preferred; next target is thinking-time fillers and less theatrical pitch behavior
- VOICE-022 bilingual spoken-text normalization for English contractions and conservative German spoken forms, wired into RESP-002/RESP-003 with protected-text locks
- PRIVATE-CALL-LEARNING-001 local-only private call learning scaffold for future positive/negative sales-pattern mining without exporting raw audio or identifiers
- RESP-002 runtime voice-delivery bridge from guarded response to offline ElevenLabs/Cartesia provider preview
- project-local self-containment, voice provider run-boundary, and generated-audio asset-log policies
- RESP-003 runtime live-capable TTS bridge from validated voice-delivery packet to optional provider audio
- RESP-003 first bilingual ElevenLabs live TTS result for German and English campaign responses
- RESP-003 human listening review showing the next voice quality target: faster, less robotic, better pitch/emotion, while preserving clarity
- VOICE-034 pacing calibration V2 and VOICE-035 connected-speech phrase-flow tuning as separate bounded runtime layers before RESP-003 live TTS
- VOICE-036 listening-feedback calibration for German over-compression and conservative emphasis-target filtering
- VOICE-037 emotion-transition smoothing for abrupt vocal mood changes
- VOICE-038 semantic-emphasis diagnosis and VOICE-039 runtime promotion for the preferred English clear/simple worth-your-time wording pattern

Next voice checkpoint:

- run a short RESP-003 live listening check with VOICE-039 active and a longer English script before changing voice IDs, filler placement, or broader semantic emphasis behavior again
- compare the VOICE-039 promoted wording against the VOICE-038 baseline/control impression
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
