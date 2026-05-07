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

### 2026-05-07 - Generated artifact folderization and drift guard

- Objective: make the accumulated experiment evidence easier to audit before pushing the full project checkpoint to GitHub.
- Action taken: grouped prior flat generated artifacts under milestone folders, added `research/experiments/generated/README.md`, expanded generated-audio ignore rules, and extended the project drift guard to fail on unexpected flat generated-root files.
- Data used: existing generated experiment outputs only. No provider call, NotebookLM API call, LLM call, private audio, private transcript, API key, or new source gathering was used.
- Output created: grouped `research/experiments/generated/<checkpoint>/` artifact folders, updated `.gitignore`, updated `scripts/check_project_drift.py`, updated `scripts/validate_project_drift_guard.py`, and this thesis trace.
- What was learned: artifact organization is part of thesis method quality. If evidence folders are hard to scan, generated files can hide stale outputs, source excerpts, live-audio leakage, or mixed checkpoint claims.
- Why it matters for the thesis: the final write-up should be able to point to reproducible checkpoint folders and explain which outputs are public-safe generated evidence versus local ignored provider audio.
- Open questions: whether later live listening artifacts should get a separate curated-public-evidence folder after privacy, provider-retention, and source-audio review.

### 2026-05-07 - RAG-016B through RAG-018 guarded live retrieval

- Objective: finish the remaining voice/prosody RAG review and enable local guarded retrieval as an explicit opt-in runtime path.
- Action taken: added RAG-016B voice-delivery acceptance, RAG-017 runtime knowledge registry, RAG-018 guarded runtime retrieval validation, and RESP-001 retrieval metadata/CLI integration.
- Data used: existing accepted RAG artifacts through RAG-016A and local generated review artifacts only. No new sources, NotebookLM API call, LLM call, embedding provider, vector database, TTS/ASR provider call, private customer data, raw audio, API key, or source excerpt text was used.
- Output created: `docs/product/RAG_016B_VOICE_DELIVERY_DECISION_SLICE.md`, `docs/product/RAG_017_RUNTIME_KNOWLEDGE_REGISTRY.md`, `docs/product/RAG_018_GUARDED_RUNTIME_RETRIEVAL.md`, RAG-016B/RAG-017 generated artifacts, new validators, and guarded-response retrieval flags.
- What was learned: the remaining `19` voice-delivery candidates can be preserved as advisory-only project-owned rules if hidden-emotion inference, protected-trait inference, pressure escalation, and protected-text changes are hard-blocked. The runtime registry contains `59` accepted items and keeps `58` source-mapping chunks, `43` source-mapping groups, and `21` latent quote follow-ups excluded.
- Why it matters for the thesis: this creates the first live retrieval path without weakening the safety architecture. Retrieval is local, deterministic, traceable, opt-in, and subordinate to campaign guardrails, refusal handling, protected text, and human escalation.
- Open questions: which reviewed campaigns should explicitly enable retrieval first, and whether future source-mapping cleanup should expand the registry or remain advisory-only until more live-call evaluation exists.

### 2026-05-07 - RAG-016A quote-clearance decision slice

- Objective: accept the first RAG-016 quote-clearance decision slice by converting the ethical-persuasion batch into project-owned low-pressure response rules and one rational-agency safety guardrail.
- Action taken: added the RAG-016A quote-clearance decision-slice builder, runner, case config, product documentation, validator, and official JSON/Markdown artifacts.
- Data used: existing RAG-016 quote-clearance batch artifact and RAG-009 all-source review coverage artifact under `research/experiments`. No NotebookLM API call, LLM call, TTS/ASR provider call, private customer data, raw call-center audio, API key, source excerpt text, chunk import, embedding job, vector database, runtime retrieval, or new source gathering was used.
- Output created: `docs/product/RAG_016A_QUOTE_CLEARANCE_DECISION_SLICE.md`, `research/experiments/cases/rag-016a-quote-clearance-decision-slice.json`, `research/experiments/generated/RAG-016A-quote-clearance-decision-slice/result.json`, `research/experiments/generated/RAG-016A-quote-clearance-decision-slice/report.md`, `scripts/rag_quote_clearance_decision_slice.py`, `scripts/run_rag_016a_quote_clearance_decision_slice.py`, and `scripts/validate_rag_016a_quote_clearance_decision_slice.py`.
- What was learned: the ethical-persuasion queue can be cleared safely when each candidate is rewritten as truthful, consent-aware, vertical-agnostic guidance. RAG-016A accepts `11` items, leaves `19` voice-delivery quote-clearance blockers, and keeps `58` source-mapping chunks plus `21` latent quote follow-ups pending.
- Why it matters for the thesis: RAG-016A demonstrates that RAG readiness is not a binary import step. Quote-dependent persuasion material can be converted into reviewed product-owned policy while runtime retrieval remains off.
- Open questions: whether RAG-016B should accept all remaining voice-delivery cards as advisory-only rules in one slice or split speech/prosody and emotion-recognition limitations into separate reviews.

### 2026-05-07 - RAG-016 quote-clearance batches

- Objective: organize the remaining original quote-clearance blockers into human-review batches after RAG-015, including voice/prosody candidates where they make sense as advisory-only delivery guidance.
- Action taken: added the RAG-016 quote-clearance batch builder, runner, case config, product documentation, validator, and official JSON/Markdown artifacts.
- Data used: existing RAG-015 source-mapping batch artifact, RAG-013 cleanup strategy artifact, RAG-012 accepted cleanup artifact, and RAG-009 all-source review coverage artifact under `research/experiments`. No NotebookLM API call, LLM call, TTS/ASR provider call, private customer data, raw call-center audio, API key, source excerpt text, chunk import, embedding job, vector database, runtime retrieval, or new source gathering was used.
- Output created: `docs/product/RAG_016_QUOTE_CLEARANCE_BATCHES.md`, `research/experiments/cases/rag-016-quote-clearance-batches.json`, `research/experiments/generated/RAG-016-quote-clearance-batches/result.json`, `research/experiments/generated/RAG-016-quote-clearance-batches/report.md`, `scripts/rag_quote_clearance_batches.py`, `scripts/run_rag_016_quote_clearance_batches.py`, and `scripts/validate_rag_016_quote_clearance_batches.py`.
- What was learned: the remaining original quote-clearance queue has `30` chunks across `15` source-title groups: `11` ethical-persuasion response-wording candidates, `10` speech/prosody advisory candidates, and `9` emotion-recognition delivery advisory candidates. RAG-015 still leaves `58` source-mapping chunks and `21` latent quote follow-ups outside this batch.
- Why it matters for the thesis: RAG-016 separates quote-dependent wording review from runtime retrieval and shows that voice/prosody knowledge can be preserved safely as advisory-only material instead of being promoted as emotion inference or buying-intent logic.
- Open questions: which RAG-016 batch should be accepted or rejected first in `RAG-016A`, and whether the clean-candidate re-audit should wait until all three quote-clearance batches have a first accepted/rejected slice.

### 2026-05-07 - RAG-015 source-mapping batches

- Objective: organize all remaining source-mapping blockers into human-review batches after RAG-014, without adding new resources or enabling runtime retrieval.
- Action taken: added the RAG-015 source-mapping batch builder, runner, case config, product documentation, validator, and official JSON/Markdown artifacts.
- Data used: existing RAG-014 source-mapped quote follow-up artifact, RAG-013 cleanup strategy artifact, RAG-006 chunk review packet, and RAG-009 all-source review coverage artifact under `research/experiments`. No NotebookLM API call, LLM call, TTS/ASR provider call, private customer data, raw call-center audio, API key, source excerpt text, chunk import, embedding job, vector database, runtime retrieval, or new source gathering was used.
- Output created: `docs/product/RAG_015_SOURCE_MAPPING_BATCHES.md`, `research/experiments/cases/rag-015-source-mapping-batches.json`, `research/experiments/generated/RAG-015-source-mapping-batches/result.json`, `research/experiments/generated/RAG-015-source-mapping-batches/report.md`, `scripts/rag_source_mapping_batches.py`, `scripts/run_rag_015_source_mapping_batches.py`, and `scripts/validate_rag_015_source_mapping_batches.py`.
- What was learned: adding new source material later is feasible because the RAG intake/refresh path already exists, so RAG-015 can proceed on the current corpus. The remaining source-mapping queue has `43` source-title groups and `58` chunks, with `3` high-impact groups, `6` medium groups, `34` singleton groups, `7` candidate source suggestions, and `21` latent quote follow-ups after future mapping.
- Why it matters for the thesis: RAG-015 separates source-accounting readiness from source-decision acceptance. This preserves the thesis claim that retrieved knowledge needs staged provenance cleanup before runtime admission.
- Open questions: which RAG-015 source-mapping groups should be human-accepted first, and whether RAG-016 should focus on the `30` original quote-clearance chunks before returning to source-mapping acceptance.

### 2026-05-07 - RAG-014 source-mapped quote follow-up

- Objective: clear the five quote follow-ups created by RAG-012 accepted source mappings before moving to broader source-mapping batches.
- Action taken: added the RAG-014 source-mapped quote follow-up builder, runner, case config, product documentation, validator, and official JSON/Markdown artifacts.
- Data used: existing RAG-013 cleanup strategy artifact and RAG-009 all-source review coverage artifact under `research/experiments`. No NotebookLM API call, LLM call, TTS/ASR provider call, private customer data, raw call-center audio, API key, source excerpt text, chunk import, embedding job, vector database, or runtime retrieval was used.
- Output created: `docs/product/RAG_014_SOURCE_MAPPED_QUOTE_FOLLOWUP.md`, `research/experiments/cases/rag-014-source-mapped-quote-followup.json`, `research/experiments/generated/RAG-014-source-mapped-quote-followup/result.json`, `research/experiments/generated/RAG-014-source-mapped-quote-followup/report.md`, `scripts/rag_source_mapped_quote_followup.py`, `scripts/run_rag_014_source_mapped_quote_followup.py`, and `scripts/validate_rag_014_source_mapped_quote_followup.py`.
- What was learned: four source-mapped quote follow-ups can be safely preserved as low-pressure, vertical-agnostic response-wording rules. The fixed talk-time dominance candidate should be rejected because it optimizes control over listening. The source-mapped follow-up queue is now `0`.
- Why it matters for the thesis: RAG-014 shows that source cleanup can create a second quote-clearance dependency, and that the system needs explicit accept/reject review before any retrieved knowledge becomes runtime-eligible.
- Open questions: which `RAG-015` source-title groups should be reviewed first, and how many new quote-clearance follow-ups will be created by the remaining source-mapping decisions.

### 2026-05-07 - RAG-013 cleanup strategy

- Objective: choose the cleanup order for the remaining RAG blockers after RAG-012 before any runtime retrieval work.
- Action taken: added the RAG-013 cleanup strategy builder, runner, case config, product documentation, validator, and official JSON/Markdown artifacts.
- Data used: existing RAG-012 accepted cleanup artifact, RAG-009 all-source review coverage artifact, and RAG-006 chunk review packet under `research/experiments`. No NotebookLM API call, LLM call, TTS/ASR provider call, private customer data, raw call-center audio, API key, source excerpt text, chunk import, embedding job, vector database, or runtime retrieval was used.
- Output created: `docs/product/RAG_013_CLEANUP_STRATEGY.md`, `research/experiments/cases/rag-013-cleanup-strategy.json`, `research/experiments/generated/RAG-013-cleanup-strategy/result.json`, `research/experiments/generated/RAG-013-cleanup-strategy/report.md`, `scripts/rag_cleanup_strategy.py`, `scripts/run_rag_013_cleanup_strategy.py`, and `scripts/validate_rag_013_cleanup_strategy.py`.
- What was learned: after RAG-012, the active cleanup queue is `58` source-mapping chunks, `30` original quote-clearance chunks, and `5` quote follow-ups created by accepted source mappings. The known cleanup work count before runtime is therefore `93`, with `21` additional latent quote follow-ups likely to appear behind remaining source mappings.
- Why it matters for the thesis: RAG-013 records that retrieval readiness is not only about having reviewed rules; the project must track staged cleanup dependencies so metadata review, quote clearance, and final runtime admission remain separate.
- Open questions: whether `RAG-014` should clear all five source-mapped quote follow-ups in one slice or reject unsafe pressure-oriented chunks while preserving only low-pressure, vertical-agnostic guidance.

### 2026-05-07 - RAG-012 accepted cleanup

- Objective: apply the human-accepted first cleanup slice from RAG-011 while keeping RAG review separate from runtime retrieval.
- Action taken: added the RAG-012 accepted cleanup builder, runner, case config, product documentation, validator, and official JSON/Markdown artifacts.
- Data used: existing RAG-011 blocker cleanup packet and RAG-009 all-source review coverage artifact under `research/experiments`. No NotebookLM API call, LLM call, TTS/ASR provider call, private customer data, raw call-center audio, API key, source excerpt text, chunk import, embedding job, vector database, or runtime retrieval was used.
- Output created: `docs/product/RAG_012_ACCEPTED_CLEANUP.md`, `research/experiments/cases/rag-012-accepted-cleanup.json`, `research/experiments/generated/RAG-012-accepted-cleanup/result.json`, `research/experiments/generated/RAG-012-accepted-cleanup/report.md`, `scripts/rag_accepted_cleanup.py`, `scripts/run_rag_012_accepted_cleanup.py`, and `scripts/validate_rag_012_accepted_cleanup.py`.
- What was learned: RAG-012 accepted `17` cleanup decisions: `5` source-mapping chunks and `12` quote-clearance rewrites. Source-mapping blockers fall from `63` to `58`; the original quote-clearance queue falls from `42` to `30`; and `5` accepted source mappings still need quote-clearance follow-up before any future promotion.
- Why it matters for the thesis: this checkpoint records how human review turns extracted sales and voice knowledge into safer project-owned rules without confusing cleanup with runtime use. It also preserves the distinction between metadata cleanup, quote clearance, and final runtime admission.
- Open questions: whether `RAG-013` should continue with source-mapping cleanup, quote-clearance rewrite cleanup, or a combined cleanup slice before any runtime-off retrieval integration harness.

### 2026-05-07 - RAG-011 blocker cleanup packet

- Objective: narrow the remaining source-mapping and quote-clearance cleanup work before any runtime integration work.
- Action taken: added the RAG-011 blocker cleanup builder, runner, case config, product documentation, validator, and official JSON/Markdown artifacts.
- Data used: existing RAG-009 all-source review coverage artifact and RAG-006 chunk review packet under `research/experiments`. No NotebookLM API call, LLM call, TTS/ASR provider call, private customer data, raw call-center audio, API key, source excerpt text, chunk import, embedding job, vector database, or runtime retrieval was used.
- Output created: `docs/product/RAG_011_BLOCKER_CLEANUP_PACKET.md`, `research/experiments/cases/rag-011-blocker-cleanup-packet.json`, `research/experiments/generated/RAG-011-blocker-cleanup-packet/result.json`, `research/experiments/generated/RAG-011-blocker-cleanup-packet/report.md`, `scripts/rag_blocker_cleanup_packet.py`, `scripts/run_rag_011_blocker_cleanup_packet.py`, and `scripts/validate_rag_011_blocker_cleanup_packet.py`.
- What was learned: the remaining blockers are still `63` source-mapping chunks and `42` quote-clearance chunks. RAG-011 found `3` high-confidence source-mapping proposal groups covering `5` chunks and created `12` quote-clearance review cards, for `17` possible blocker reductions after human acceptance. It intentionally resolved `0` blockers now.
- Why it matters for the thesis: RAG-011 separates cleanup planning from automatic knowledge admission. It shows that a source-tracked sales RAG can prioritize human review work while preserving no-runtime, no-private-data, no-source-excerpt, and no-auto-promotion boundaries.
- Open questions: whether `RAG-012` should apply only the `5` source-mapping proposals first, only the `12` quote-clearance cards first, or a mixed human-accepted cleanup slice that records exact accepted/rejected decisions.

### 2026-05-07 - RAG-010 reviewed expansion slice

- Objective: manually review the four clean RAG-009 next-promotion candidates before considering any runtime integration work.
- Action taken: added the RAG-010 reviewed expansion builder, runner, case config, product documentation, validator, and official JSON/Markdown artifacts.
- Data used: existing RAG-009 all-source review coverage artifact under `research/experiments`. No NotebookLM API call, LLM call, TTS/ASR provider call, private customer data, raw call-center audio, API key, source excerpt text, chunk import, embedding job, vector database, or runtime retrieval was used.
- Output created: `docs/product/RAG_010_REVIEWED_EXPANSION_SLICE.md`, `research/experiments/cases/rag-010-reviewed-expansion-slice.json`, `research/experiments/generated/RAG-010-reviewed-expansion-slice/result.json`, `research/experiments/generated/RAG-010-reviewed-expansion-slice/report.md`, `scripts/rag_reviewed_expansion_slice.py`, `scripts/run_rag_010_reviewed_expansion_slice.py`, and `scripts/validate_rag_010_reviewed_expansion_slice.py`.
- What was learned: all `4` clean RAG-009 candidates can be promoted as project-owned paraphrases if bounded carefully. Impact discovery, "so what" clarification, and timing checks are useful only as low-pressure evidence gathering. Cadence detection is useful only as advisory voice/prosody context and must not become hidden-emotion or intent inference.
- Why it matters for the thesis: RAG-010 shows how retrieved sales-knowledge candidates can be converted into safer, vertical-agnostic agent rules before runtime use. It also preserves a key emotion-aware boundary: vocal signals may guide pacing or a clarification question, but they cannot become certainty about a customer's internal state.
- Open questions: whether `RAG-011` should reduce the `63` source-mapping blockers first, reduce the `42` quote-clearance blockers first, or run a small blocker-cleanup slice across both queues before any runtime-off integration harness.

### 2026-05-07 - RAG-009 all-source review coverage

- Objective: confirm that every imported RAG source and chunk is accounted for before any runtime retrieval work continues.
- Action taken: added the RAG-009 all-source coverage builder, runner, case config, product documentation, validator, and official JSON/Markdown artifacts.
- Data used: existing RAG-004 source manifest, RAG-005 chunk normalization result, RAG-006 review packet, and RAG-007 reviewed first-slice artifact under `research/experiments`. No NotebookLM API call, LLM call, TTS/ASR provider call, private customer data, raw call-center audio, API key, source excerpt text, chunk import, or runtime retrieval was used.
- Output created: `docs/product/RAG_009_ALL_SOURCE_REVIEW_COVERAGE.md`, `research/experiments/cases/rag-009-all-source-review-coverage.json`, `research/experiments/generated/RAG-009-all-source-review-coverage/result.json`, `research/experiments/generated/RAG-009-all-source-review-coverage/report.md`, `scripts/rag_all_source_review_coverage.py`, `scripts/run_rag_009_all_source_review_coverage.py`, and `scripts/validate_rag_009_all_source_review_coverage.py`.
- What was learned: the full RAG inventory currently has `95` sources and `121` chunk candidates; `9` chunks are already manually reviewed, `4` are clean next-promotion candidates, `63` need source mapping, `42` need quote clearance, and `3` are safety rejections. The Vinh-informed voice/prosody material is included in coverage but remains advisory and non-runtime.
- Why it matters for the thesis: RAG-009 turns "include all sources before retrieval" into a measurable gate. It separates source accounting from runtime use, showing that a vertical-agnostic sales-agent RAG layer needs inventory coverage, manual promotion, quote clearance, and safety rejection before it can become part of an autonomous workflow.
- Open questions: whether the four clean next-promotion candidates should become a RAG-010 reviewed slice, how aggressively the project should resolve the `63` source-mapping blocks, and whether runtime-off integration should wait until quote clearance is materially smaller.

### 2026-05-06 - RAG-008 guarded retrieval policy dry-run

- Objective: test whether the manually reviewed RAG-007 slice can produce safe retrieval candidate packets without enabling runtime retrieval.
- Action taken: added a failing RAG-008 validator first, implemented `scripts/rag_guarded_retrieval_policy.py`, added `scripts/run_rag_008_guarded_retrieval_policy.py`, added synthetic dry-run cases, generated JSON/Markdown artifacts, documented the checkpoint, and added it to setup gates.
- Data used: the RAG-007 reviewed first-slice artifact and synthetic RAG-008 cases under `research/experiments`. No NotebookLM API call, LLM call, TTS/ASR provider call, private customer data, raw call-center audio, API key, raw source text import, chunk import, or runtime retrieval was used.
- Output created: `docs/product/RAG_008_GUARDED_RETRIEVAL_POLICY.md`, `research/experiments/cases/rag-008-guarded-retrieval-policy.json`, `research/experiments/generated/RAG-008-guarded-retrieval-policy/result.json`, `research/experiments/generated/RAG-008-guarded-retrieval-policy/report.md`, `scripts/rag_guarded_retrieval_policy.py`, `scripts/run_rag_008_guarded_retrieval_policy.py`, and `scripts/validate_rag_008_guarded_retrieval_policy.py`.
- What was learned: the first reviewed slice can support deterministic candidate packets for ordinary objections, broad-answer structure, and tone-uncertainty clarification, but hard context flags must block retrieval before style guidance is considered. Voice/prosody rules belong in the packet only as advisory delivery guidance; tone remains a weak signal and cannot become emotion certainty.
- Why it matters for the thesis: RAG-008 records a concrete middle gate between reviewed knowledge and runtime use. It shows that a persuasive sales RAG layer needs retrieval blocking, citation traces, advisory-only voice guidance, and no-runtime defaults before it can be evaluated as part of an autonomous agent.
- Open questions: what `RAG-009` runtime integration gate should require before the sales agent can consult reviewed retrieval, how retrieved packet citations should appear in runtime traces, and whether product/campaign guardrails should always run before and after retrieval.

### 2026-05-06 - RAG-007 reviewed first slice

- Objective: move from RAG-006 review queues to one manually reviewed, source-tracked first knowledge slice without enabling runtime retrieval.
- Action taken: added a failing RAG-007 validator first, implemented `scripts/rag_reviewed_first_slice.py`, added `scripts/run_rag_007_reviewed_first_slice.py`, generated the reviewed-slice JSON/Markdown artifact, documented the checkpoint, and added it to setup gates.
- Data used: the RAG-006 review packet, the RAG-005 chunk-normalization result, and the RAG-004 source manifest under `research/experiments/generated`. No NotebookLM API call, LLM call, TTS/ASR provider call, private customer data, raw call-center audio, API key, raw source text import, chunk import, or runtime retrieval was used.
- Output created: `docs/product/RAG_007_REVIEWED_FIRST_SLICE.md`, `research/experiments/cases/rag-007-reviewed-first-slice.json`, `research/experiments/generated/RAG-007-reviewed-first-slice/result.json`, `research/experiments/generated/RAG-007-reviewed-first-slice/report.md`, `scripts/rag_reviewed_first_slice.py`, `scripts/run_rag_007_reviewed_first_slice.py`, and `scripts/validate_rag_007_reviewed_first_slice.py`.
- What was learned: the first safe slice should combine response-wording guidance and voice-delivery guidance, but voice/prosody rules must stay non-diagnostic. Tone mismatch is only a weak uncertainty signal that can trigger a gentle clarification; it cannot override explicit customer intent, compliance, campaign scripts, refusal handling, or human escalation.
- Error or correction preserved: final review found that the selected chunks were RAG-006 quote-queue candidates, not automatically runtime-ready first-slice candidates. The implementation was tightened to record manual quote clearance for every selected item as a project-owned paraphrase with no source excerpt text copied.
- Why it matters for the thesis: RAG-007 documents a human-review gate between source extraction and any retrieval/runtime use, showing that persuasion and voice guidance are treated as reviewed, bounded knowledge rather than automatically trusted model memory.
- Open questions: what retrieval policy should query these reviewed items, how retrieved items should be cited in decision traces, and which campaign guardrails must block or override retrieval before any runtime use.

### 2026-05-06 - Vinh Giang communication report import and RAG refresh

- Objective: add Tarik's new NotebookLM extraction from the Vinh Giang YouTube communication corpus into the existing review-only RAG pipeline.
- Action taken: saved the NotebookLM output as `research/experiments/generated/RAG-002-notebooklm-extraction-automation-bridge/imports/Vinh Giang Communication and Human Voice Behavior RAG Extraction Report.md`, regenerated RAG-003, RAG-004, RAG-005, and RAG-006 outputs, and updated the product docs plus roadmap with refreshed counts.
- Data used: Tarik's pasted NotebookLM report covering `40` Vinh Giang YouTube sources. No direct YouTube download, NotebookLM API call, LLM call, TTS/ASR provider call, private customer data, raw call-center audio, API key, runtime retrieval, or chunk import was used.
- Output created: refreshed `research/experiments/generated/RAG-003-report-import-readiness/result.json`, `research/experiments/generated/RAG-004-source-manifest-normalization/result.json`, `research/experiments/generated/RAG-005-chunk-normalization/result.json`, `research/experiments/generated/RAG-006-chunk-review-packet/result.json`, corresponding Markdown reports, and the imported Vinh Giang Markdown report file.
- What was learned: the Vinh Giang report added `11` mapped chunk candidates around voice delivery, pacing, pausing, resonance, concise response structure, PREP, 3-2-1, empathy echo, emotion reflection, and "Yes, And" objection framing. The refreshed pipeline now has `11` reports, `95` source candidates, `121` chunk candidates, `58` mapped chunks, `63` source-mapping chunks, `8` topic-mapping chunks, and `80` quote-review chunks. The first-slice queue now begins with several Vinh-derived response wording candidates because they are source-mapped and topic-clean.
- Error or correction preserved: the Vinh report used `source_excerpt_present: true`; RAG-005 originally only detected fields named `source_excerpt` or `short_excerpt`. A failing validator case was added, then the parser was corrected so explicit `source_excerpt_present` fields also become quote-review flags without storing source excerpt text.
- Why it matters for the thesis: this records a realistic iterative RAG expansion loop where a new expert communication source pack enters the same gated pipeline, improves the candidate pool for voice/response naturalness, and still remains review-only before any autonomous persuasive behavior can use it.
- Open questions: whether the first reviewed promotion slice should start with Vinh-derived response wording (`Yes, And`, `3-2-1`, PREP), voice delivery guidance, or broader ethical persuasion chunks, and whether Tarik can later provide exact YouTube URLs for source metadata completeness.

### 2026-05-06 - RAG-006 chunk review packet

- Objective: reduce the human review burden after RAG-005 by grouping chunk candidates into source-mapping, topic-mapping, quote-review, and first-slice review queues without promoting knowledge into runtime.
- Action taken: added a failing RAG-006 validator first, implemented `scripts/rag_chunk_review_packet.py`, added `scripts/run_rag_006_chunk_review_packet.py`, generated the real review-packet JSON/Markdown report, tightened source suggestions to avoid weak fuzzy matches, documented the checkpoint, and added it to setup/drift gates.
- Data used: the RAG-005 chunk-normalization result under `research/experiments/generated/RAG-005-chunk-normalization/result.json` and the RAG-004 source manifest under `research/experiments/generated/RAG-004-source-manifest-normalization/result.json`. No NotebookLM API call, LLM call, TTS/ASR provider call, private customer data, raw call-center audio, API key, raw source text import, chunk import, or runtime retrieval was used.
- Output created: `docs/product/RAG_006_CHUNK_REVIEW_PACKET.md`, `research/experiments/cases/rag-006-chunk-review-packet.json`, `research/experiments/generated/RAG-006-chunk-review-packet/result.json`, `research/experiments/generated/RAG-006-chunk-review-packet/report.md`, `scripts/rag_chunk_review_packet.py`, `scripts/run_rag_006_chunk_review_packet.py`, and `scripts/validate_rag_006_chunk_review_packet.py`.
- What was learned: the `110` RAG-005 candidates can be reduced into `46` source-title review groups for the `63` source-mapping chunks, `8` topic-mapping rows, `69` quote-review rows, and `20` first-slice review candidates. The first clean review slice currently leans toward ethical persuasion and speech/prosody because those have mapped source IDs and no topic-mapping flags, but they still require quote, safety, compliance, and campaign-guardrail review.
- Error or correction preserved: the first validator failed because the module was missing. The first implementation exposed an over-strict validator assertion that accidentally rejected the allowed `source_excerpt_present` flag; the test was corrected to reject raw excerpt text instead. The first real review packet also produced weak fuzzy source suggestions, so the suggestion threshold was tightened to keep hints conservative and human-reviewed.
- Why it matters for the thesis: this checkpoint shows that RAG construction is not just retrieval engineering. For a persuasive sales agent, knowledge ingestion needs review queues, conservative mapping hints, quote/copyright boundaries, and an explicit no-promotion state before the agent can safely use extracted sales tactics.
- Open questions: which source-title groups should be resolved first, whether Tarik wants ethical persuasion or speech/prosody as the first reviewed promotion slice, and what minimum metadata/review fields should be required before `RAG-007`.

### 2026-05-06 - RAG-005 chunk normalization

- Objective: convert Tarik's imported NotebookLM report appendices into source-tracked, review-only RAG chunk candidates without enabling runtime retrieval.
- Action taken: added and verified a RAG-005 validator contract, implemented `scripts/rag_chunk_normalization.py`, added `scripts/run_rag_005_chunk_normalization.py`, generated a real metadata-only chunk-candidate JSON/Markdown report, documented the checkpoint, and added it to setup/drift gates.
- Data used: Tarik's manually imported NotebookLM Markdown reports under `research/experiments/generated/RAG-002-notebooklm-extraction-automation-bridge/imports` and the RAG-004 source manifest under `research/experiments/generated/RAG-004-source-manifest-normalization/result.json`. No NotebookLM API call, LLM call, TTS/ASR provider call, private customer data, raw call-center audio, API key, raw source text import, chunk import, or runtime retrieval was used.
- Output created: `docs/product/RAG_005_CHUNK_NORMALIZATION.md`, `research/experiments/cases/rag-005-chunk-normalization.json`, `research/experiments/generated/RAG-005-chunk-normalization/result.json`, `research/experiments/generated/RAG-005-chunk-normalization/report.md`, `scripts/rag_chunk_normalization.py`, `scripts/run_rag_005_chunk_normalization.py`, and `scripts/validate_rag_005_chunk_normalization.py`.
- What was learned: the imported reports contain `110` candidate sales-knowledge chunks. `47` mapped automatically to RAG-004 source IDs, `63` need source-mapping review, `8` used narrower NotebookLM topic labels that were routed back to approved report topics with review flags, and `69` chunks contained source-excerpt references that were represented only as `source_excerpt_present` flags. No secret-like chunk fields were detected, and source excerpt text was not copied forward.
- Error or correction preserved: the first validator failed because the RAG-005 module was missing. After a partial module existed, the validator caught unstable chunk ordering because file sorting placed `closing.md` before `cold-calling.md`; chunk ordering was corrected to follow the project RAG topic taxonomy. A second correction preserved off-taxonomy NotebookLM topic labels as `original_topic_id` while assigning candidates to approved taxonomy topics and flagging them for review.
- Why it matters for the thesis: this checkpoint records a practical, auditable middle layer between NotebookLM-assisted research extraction and any autonomous sales-agent memory. It shows that RAG ingestion needs source mapping, topic normalization, quote/copyright review, and human approval before a persuasive sales agent can safely use extracted tactics.
- Open questions: which unmapped sources should be merged or added to the RAG-004 manifest, which `110` chunks are safe enough to promote first, and whether `RAG-006` should start with objection handling, ethical persuasion, active listening, or speech/prosody.

### 2026-05-06 - RAG-004 source manifest normalization

- Objective: convert the source-title references inside Tarik's imported NotebookLM reports into stable local source IDs before any chunk import or runtime retrieval.
- Action taken: added a failing RAG-004 validator first, implemented `scripts/rag_source_manifest_normalization.py`, added `scripts/run_rag_004_source_manifest_normalization.py`, generated a metadata-only source manifest and Markdown review report, documented the checkpoint, and added it to setup/drift gates.
- Data used: Tarik's manually imported NotebookLM Markdown reports under `research/experiments/generated/RAG-002-notebooklm-extraction-automation-bridge/imports`. No NotebookLM API call, LLM call, TTS/ASR provider call, private customer data, raw call-center audio, API key, raw source text, chunk import, or runtime retrieval was used.
- Output created: `docs/product/RAG_004_SOURCE_MANIFEST_NORMALIZATION.md`, `research/experiments/cases/rag-004-source-manifest-normalization.json`, `research/experiments/generated/RAG-004-source-manifest-normalization/result.json`, `research/experiments/generated/RAG-004-source-manifest-normalization/report.md`, `scripts/rag_source_manifest_normalization.py`, `scripts/run_rag_004_source_manifest_normalization.py`, and `scripts/validate_rag_004_source_manifest_normalization.py`.
- What was learned: the imported report set contains a broad source universe. The first real run produced `74` source candidates from `10` reports, with every source candidate linked to at least one RAG topic, no secret-like source titles, no provider calls, no runtime retrieval, and no chunk import. All source candidates still require human metadata review for URLs, authors/channels, source types, language, rights status, and thesis citation notes.
- Error or correction preserved: the first validator failed because the RAG-004 module was missing. The first real scanner then over-collected noisy appendix rows, producing `237` candidates including non-source fields. The extractor was tightened twice: first to ignore obvious JSON/field fragments and then to parse source-coverage sections instead of all RAG appendix tables. A final hygiene pass removed obvious false positives such as customer phrases, `404` pages, and single-word concepts.
- Why it matters for the thesis: this creates an auditable source-normalization step between NotebookLM-assisted extraction and a future source-tracked sales knowledge base. It also records that automated source extraction from AI-generated reports is useful but must remain human-reviewed before it can support thesis references or product RAG behavior.
- Open questions: which of the `74` source candidates should be merged or removed, how Tarik wants to fill missing URL/author metadata, and whether the first chunk-normalization pass should start with objection handling, ethical persuasion, active listening, or speech/prosody.

### 2026-05-06 - RAG-003 NotebookLM report import-readiness audit

- Objective: verify whether Tarik's imported NotebookLM report artifacts are complete enough for later RAG normalization without confusing report files, pasted chat continuations, and gap-check results with runtime-ready knowledge.
- Action taken: added a failing RAG-003 validator first, implemented `scripts/rag_report_import_readiness.py`, added `scripts/run_rag_003_report_import_readiness.py`, generated a real import-readiness JSON/Markdown audit, documented the checkpoint, and added it to setup/drift gates.
- Data used: Tarik's manually imported NotebookLM Markdown reports under `research/experiments/generated/RAG-002-notebooklm-extraction-automation-bridge/imports`. No NotebookLM API call, LLM call, TTS/ASR provider call, private customer data, raw call-center audio, API key, or runtime retrieval was used.
- Output created: `docs/product/RAG_003_REPORT_IMPORT_READINESS.md`, `research/experiments/cases/rag-003-report-import-readiness.json`, `research/experiments/generated/RAG-003-report-import-readiness/result.json`, `research/experiments/generated/RAG-003-report-import-readiness/report.md`, `scripts/rag_report_import_readiness.py`, `scripts/run_rag_003_report_import_readiness.py`, and `scripts/validate_rag_003_report_import_readiness.py`.
- What was learned: the imported report set covers all ten active RAG topics, all reports contain `END: COMPLETE`, no report contains `NEED_CONTINUATION`, and no secret-like string was detected. After Tarik added a voice/prosody source-coverage addendum, every report has source coverage and a RAG-ready appendix. The set is useful research intake, but not ready for automatic import because source titles still need stable source IDs, pasted gap-check/chat continuations need normalization, and source excerpts need quote review.
- Error or correction preserved: the first RAG-003 validator failed because the module was missing, then the implementation failed because the duplicate-section regex used inline flags in the middle of an alternation. The regex was corrected before running the real import audit.
- Why it matters for the thesis: this creates a repeatable evidence gate between NotebookLM-assisted extraction and product RAG behavior. It also preserves a realistic data-ingestion issue: AI-generated reports may be complete at the topic level while still requiring source normalization, copyright/quote review, and human-governed promotion before use by an autonomous sales agent.
- Open questions: which source-ID manifest format should be used for the real sources, how aggressively pasted gap-check continuations should be split into separate chunk candidates, and which reviewed topic should become the first runtime retrieval experiment.

### 2026-05-06 - RAG-002 NotebookLM extraction automation bridge

- Objective: reduce the tedious manual NotebookLM extraction loop by generating bounded per-topic prompts and rejecting incomplete or tiny sample-batch outputs before RAG promotion.
- Action taken: added a failing RAG-002 validator first, implemented `scripts/rag_notebooklm_automation.py`, added `scripts/run_rag_002_notebooklm_extraction_automation.py`, generated two prompts per topic, added an import drop zone, and documented the coverage gate.
- Data used: synthetic source-slot metadata only. No real YouTube links, websites, books, private customer data, call-center audio, transcripts, provider calls, NotebookLM API calls, API keys, or raw source text were used in the default run.
- Output created: `docs/product/RAG_002_NOTEBOOKLM_EXTRACTION_AUTOMATION_BRIDGE.md`, `research/experiments/cases/rag-002-notebooklm-extraction-automation-bridge.json`, `research/experiments/generated/RAG-002-notebooklm-extraction-automation-bridge/result.json`, `research/experiments/generated/RAG-002-notebooklm-extraction-automation-bridge/report.md`, generated per-topic prompt files, `scripts/rag_notebooklm_automation.py`, `scripts/run_rag_002_notebooklm_extraction_automation.py`, and `scripts/validate_rag_002_notebooklm_extraction_automation.py`.
- What was learned: NotebookLM should be treated as a source-grounded extraction helper with explicit completion contracts. The local project must not accept "small batch" answers as training material unless coverage is complete or source material is explicitly insufficient.
- Error or correction preserved: the initial validator failed because the RAG-002 automation module was missing, then failed because the runner was missing. After Tarik tested the first generated prompt in NotebookLM, the output contained useful chunks but compressed the "tailored report" into short JSON fields because the prompt said to return exactly one JSON object. RAG-002 was corrected twice: first to generate Configure Chat custom instructions plus a two-part chat output, then to match Tarik's actual intended workflow by generating a NotebookLM Reports / Create report prompt as the first per-topic artifact.
- Why it matters for the thesis: this creates an auditable method for converting large curated sales/source notebooks into structured, source-tracked RAG candidates while controlling prompt length, coverage completeness, and copyright/privacy boundaries.
- Open questions: whether real NotebookLM outputs from Tarik's source notebooks pass the coverage gate on the first primary prompt or require gap-check prompts for some topics.

### 2026-05-06 - RAG-001 NotebookLM source-intake bridge

- Objective: create the first source-tracked intake bridge for a sales RAG knowledge base, using NotebookLM as an extraction helper rather than permanent product memory.
- Action taken: added a failing RAG-001 validator first, implemented `scripts/rag_knowledge_base.py`, added `scripts/run_rag_001_notebooklm_source_intake.py`, created a 10-topic source manifest template, generated a NotebookLM extraction prompt, validated source-tracked demo chunks, and added a local RAG workspace README.
- Data used: synthetic demo source slots and synthetic demo chunks only. No real YouTube links, websites, books, private customer data, call-center audio, transcripts, provider calls, NotebookLM API calls, API keys, or raw source text were used in the default run.
- Output created: `docs/product/RAG_001_NOTEBOOKLM_SOURCE_INTAKE_BRIDGE.md`, `data/rag/README.md`, `research/experiments/cases/rag-001-notebooklm-source-intake-bridge.json`, `research/experiments/generated/RAG-001-notebooklm-source-intake-bridge/result.json`, `research/experiments/generated/RAG-001-notebooklm-source-intake-bridge/report.md`, `scripts/rag_knowledge_base.py`, `scripts/run_rag_001_notebooklm_source_intake.py`, and `scripts/validate_rag_001_notebooklm_source_intake.py`.
- What was learned: RAG should start as a source-management and extraction-quality problem before runtime retrieval. The first durable value is the schema: every future sales lesson must have a topic, source ID, when-to-use boundary, when-not-to-use boundary, compliance note, and citation note.
- Error or correction preserved: the initial validator failed because the RAG module was missing, then failed because the product doc was missing. This kept the checkpoint honest: code, docs, source traceability, and thesis trace had to land together.
- Why it matters for the thesis: this creates a repeatable method for transforming public sources into auditable sales-agent knowledge while avoiding untracked chat memory, copied source text, and unsafe NotebookLM dependency lock-in.
- Open questions: when Tarik has NotebookLM extraction notes for the real collected sources, which chunks should be promoted into a runtime retrieval experiment first: objection handling, semantic emphasis, or ethical persuasion.

### 2026-05-06 - VOICE-040 low-pressure focus correction

- Objective: correct the VOICE-039 listening issue where `You don't need to change anything today` could receive awkward TTS emphasis even though the selected English voice candidate is now strong enough to keep.
- Action taken: added a failing VOICE-040 validator first, implemented `scripts/voice_low_pressure_focus.py`, wired it into `RESP-002` after VOICE-039, added a live-capable runner/case set, and updated RESP validators plus setup/drift guards.
- Data used: synthetic English B2B software and German B2C telecom runtime turns only. No customer/private audio, transcription, voice cloning, provider call, API key logging, or raw voice-ID logging was used in the default run.
- Output created: `docs/product/VOICE_040_LOW_PRESSURE_FOCUS.md`, `research/experiments/cases/voice-040-low-pressure-focus.json`, `research/experiments/generated/VOICE-040-low-pressure-focus/result.json`, `research/experiments/generated/VOICE-040-low-pressure-focus/report.md`, `scripts/voice_low_pressure_focus.py`, `scripts/run_voice_040_low_pressure_focus.py`, and `scripts/validate_voice_040_low_pressure_focus.py`.
- What was learned: after the voice identity improved, the remaining voice problem became narrower: a sentence can be safe and strategically correct while still creating unnatural emphasis targets for TTS. Rewriting the provider-facing phrase to `No changes needed today` keeps the low-pressure sales meaning while reducing awkward emphasis opportunities.
- Error or correction preserved: the VOICE-039 live review showed that adding semantic emphasis is not enough if a phrase contains too many tempting stress points. VOICE-040 fixes the delivery wording only for eligible English freeform TTS text, while preserving the guarded `final_response`, protected text, German text, and provider/private-data boundaries.
- Why it matters for the thesis: this checkpoint shows a human-in-the-loop refinement cycle where subjective listening feedback is converted into a narrow, testable runtime correction rather than a broad rewrite of the sales policy or response logic.
- Open questions: whether a live VOICE-040 listening check confirms that the phrase now sounds natural in the longer guarded response.

### 2026-05-06 - VOICE-039 runtime semantic-emphasis promotion

- Objective: promote the preferred `VOICE-038` clear/simple wording pattern into the full guarded runtime path and test it with a longer script before another live listening review.
- Action taken: added a failing VOICE-039 validator first, implemented `scripts/voice_semantic_emphasis.py`, wired it into `RESP-002` after emotion smoothing and before `RESP-003`, added a live-capable longer-script runner, and updated RESP validators plus setup/drift guards.
- Data used: synthetic English B2B software and German B2C telecom runtime turns only. No customer/private audio, transcription, voice cloning, provider call, API key logging, or raw voice-ID logging was used in the default run.
- Output created: `docs/product/VOICE_039_RUNTIME_SEMANTIC_EMPHASIS.md`, `research/experiments/cases/voice-039-runtime-semantic-emphasis.json`, `research/experiments/generated/VOICE-039-runtime-semantic-emphasis/result.json`, `research/experiments/generated/VOICE-039-runtime-semantic-emphasis/report.md`, `research/experiments/generated/VOICE-039-runtime-semantic-emphasis/live-result.json`, `research/experiments/generated/VOICE-039-runtime-semantic-emphasis/live-report.md`, `scripts/voice_semantic_emphasis.py`, `scripts/run_voice_039_runtime_semantic_emphasis.py`, and `scripts/validate_voice_039_runtime_semantic_emphasis.py`.
- What was learned: the VOICE-038 clear/simple phrase can be promoted as provider-facing TTS text while preserving the original guarded `final_response`. The layer rewrites only eligible English freeform text, leaves protected text locked, and leaves German text untouched.
- Error or correction preserved: the validator first failed because the module was missing, then the runner failed because the guarded-response builder required `silence_count`; the runner was corrected to pass the same default used by RESP scripts. The validator was also adjusted to accept lower-case `we` when connected-speech joins the promoted phrase after a comma. A live-gated run inside the Codex shell safely fell back with `missing-elevenlabs-api-key`, confirming that the provider boundary works when the current shell lacks the API key.
- Why it matters for the thesis: this checkpoint records how qualitative listening feedback becomes a narrow runtime candidate with explicit safety boundaries, rather than an unconstrained rewrite of sales policy text.
- Open questions: whether the live longer-script RESP-003 check confirms that the promoted clear/simple wording sounds natural with the preferred English voice in the full guarded response path.

### 2026-05-06 - VOICE-038 live listening review

- Objective: evaluate whether semantic-emphasis variants with the current preferred English voice improve the previously weak "worth your time" phrase.
- Action taken: Tarik ran the live VOICE-038 ElevenLabs audio generation, listened to all six English MP3 variants, and gave qualitative feedback.
- Data used: synthetic English listening text only. No customer/private audio, transcription, voice cloning, or raw secret/voice-ID logging was used.
- Output created: `research/experiments/generated/VOICE-038-semantic-emphasis-diagnosis/audio/` MP3 files and `research/experiments/generated/VOICE-038-semantic-emphasis-diagnosis/human-listening-review.md`.
- What was learned: all six variants sounded good and several steps better than earlier English voice outputs. Tarik found it hard to pick a single winner because emphasis, rhythm, and pronunciation were generally strong. The preferred variants were `clear_opening_simple_clause` and `baseline_original_clause`.
- Interpretation: changing the English voice candidate was one of the strongest improvements so far. The next step should not be more broad voice hunting or random filler/pacing changes. The safer runtime candidate is the clear/simple wording pattern, while the baseline remains useful as a control because it also now performs well with the preferred voice.
- Why it matters for the thesis: this records a human-in-the-loop listening evaluation where the project separated voice identity quality from semantic wording quality and used controlled audio variants to guide the next runtime step.
- Open questions: whether to promote the clear/simple wording pattern into runtime as the default response shaping rule and keep the baseline as a comparison fallback.

### 2026-05-06 - VOICE-038 semantic emphasis diagnosis scaffold

- Objective: turn Tarik's listening feedback on the preferred English voice into a controlled semantic-emphasis and rhythm diagnosis before changing runtime behavior.
- Action taken: added a failing VOICE-038 validator first, then implemented `scripts/run_voice_038_semantic_emphasis_diagnosis.py`, a focused English case file, a product doc, command-map entries, setup/drift guard entries, and a default dry-run report folder.
- Data used: synthetic English listening text only. The target failure phrase is "whether reviewing options is worth your time." No provider call was made during the default run, and no customer/private audio, transcription, voice cloning, or raw secret/voice-ID logging was used.
- Output created: `docs/product/VOICE_038_SEMANTIC_EMPHASIS_DIAGNOSIS.md`, `research/experiments/cases/voice-038-semantic-emphasis-diagnosis.json`, `research/experiments/generated/VOICE-038-semantic-emphasis-diagnosis/results.json`, `research/experiments/generated/VOICE-038-semantic-emphasis-diagnosis/report.md`, `scripts/run_voice_038_semantic_emphasis_diagnosis.py`, and `scripts/validate_voice_038_semantic_emphasis_diagnosis.py`.
- What was learned: after switching voice candidates, the remaining English issue is specific enough to isolate with text variants instead of broad filler/pacing changes. VOICE-038 compares baseline wording, simpler wording, phrase chunking, benefit-first wording, semantic focus questions, and an opening alternative.
- Error or correction preserved: the checkpoint intentionally does not promote any wording into runtime yet. A human listening review is required because a TTS provider may emphasize text differently than the written semantics imply.
- Why it matters for the thesis: this records a clean diagnosis step between subjective listening feedback and runtime design, showing how product voice quality is improved through controlled ablation rather than guesswork.
- Open questions: which VOICE-038 variant sounds most natural with the preferred English candidate, and whether the winning pattern should become a runtime semantic-emphasis rule.

### 2026-05-06 - RESP-003 new English voice candidate check

- Objective: test whether the persistent English roboticness after VOICE-037 was caused primarily by the selected ElevenLabs English voice identity rather than the local prosody pipeline.
- Action taken: Tarik ran a live RESP-003 English runtime TTS check with a newly selected English ElevenLabs voice ID supplied through environment/local ignored voice configuration. The runtime path kept the current guarded response and voice-delivery layers active.
- Data used: synthetic English B2B software runtime text only. No customer/private audio, transcription, voice cloning, or raw provider secret logging was used.
- Output created: generated RESP-003 live audio artifacts under the local generated experiment workspace, plus a local-only ignored voice-ID config update.
- What was learned: changing the English voice candidate substantially reduced the obvious robotic voice quality. Tarik estimated that the roboticness was roughly 95% gone and that sales trust was good enough to keep working with this candidate. The remaining issue is narrower: the opening sounded slightly unclear, and the natural rhythm/emphasis broke around the clause "whether reviewing options is worth your time."
- Error or correction preserved: updating `config/local/voice_ids.json` from Windows PowerShell wrote UTF-8 with a BOM. Python rejected the file during VOICE-027 with `JSONDecodeError: Unexpected UTF-8 BOM`. The local voice-config loader was hardened to accept `utf-8-sig`, and a regression check was added so ignored local voice config remains usable after PowerShell edits.
- Why it matters for the thesis: this checkpoint separates provider/voice identity effects from local prosody-rule effects and preserves a practical engineering failure from the voice-evaluation workflow.
- Open questions: whether this English candidate should become the preferred MVP voice, and whether a later semantic emphasis layer should choose important words or simplify fragile clauses before provider rendering.

### 2026-05-06 - VOICE-037 emotion-transition smoothing

- Objective: convert Tarik's listening feedback about sharp vocal emotion jumps into a bounded runtime correction.
- Action taken: added a failing VOICE-037 validator first, implemented `scripts/voice_emotion_smoothing.py`, wired the layer into `RESP-002` after VOICE-036, added a standalone runner/case set/report path, and updated RESP-002/RESP-003 validators plus setup/drift guards.
- Data used: synthetic German B2C telecom and English B2B software runtime turns only. A synthetic direct test also checks that theatrical or excited-high cues are blocked/capped. No customer/private audio, transcription, provider call, generated audio, or voice cloning was used.
- Output created: `docs/product/VOICE_037_EMOTION_TRANSITION_SMOOTHING.md`, `research/experiments/cases/voice-037-emotion-smoothing.json`, `research/experiments/generated/VOICE-037-emotion-smoothing/results.json`, `research/experiments/generated/VOICE-037-emotion-smoothing/report.md`, `scripts/voice_emotion_smoothing.py`, `scripts/run_voice_037_emotion_smoothing.py`, and `scripts/validate_voice_037_emotion_smoothing.py`.
- What was learned: emotional expressiveness needs inertia. The runtime should avoid instant jumps between warm, confident, low, or theatrical delivery states, and provider settings should smooth the transition before adding more filler or rewriting text.
- Error or correction preserved: previous voice layers improved pace and phrase flow but did not govern emotional continuity. VOICE-037 adds that missing boundary by raising provider stability within a bounded range and capping style/exaggeration while preserving speed and rendered words.
- Why it matters for the thesis: this checkpoint records how qualitative listening feedback becomes a measurable delivery-control layer, separating sales policy, spoken wording, provider rendering, and live listening evaluation.
- Open questions: whether a fresh live RESP-003 listening check with VOICE-037 confirms smoother emotional motion without making the voice flatter or more robotic.

### 2026-05-06 - VOICE-036 listening-feedback calibration

- Objective: convert Tarik's VOICE-035 live listening feedback into a bounded runtime correction without changing the guarded sales answer.
- Action taken: added a failing VOICE-036 validator first, implemented `scripts/voice_listening_calibration.py`, filtered weak emphasis targets before provider rendering, relaxed German connected speech after VOICE-035, added a standalone runner/case set/report path, and updated RESP-002/RESP-003 validators plus setup/drift guards.
- Data used: synthetic German B2C telecom and English B2B software runtime turns only. The listening feedback came from live ElevenLabs outputs generated from synthetic prompts with local ignored voice IDs. No customer/private audio, transcription, or voice cloning was used.
- Output created: `docs/product/VOICE_036_LISTENING_CALIBRATION.md`, `research/experiments/cases/voice-036-listening-calibration.json`, `research/experiments/generated/VOICE-036-listening-calibration/results.json`, `research/experiments/generated/VOICE-036-listening-calibration/report.md`, `research/experiments/generated/RESP-003/voice-035-listening-check/human-listening-review.md`, `scripts/voice_listening_calibration.py`, `scripts/run_voice_036_listening_calibration.py`, and `scripts/validate_voice_036_listening_calibration.py`.
- What was learned: connected speech can improve English phrase flow but over-compress German if the breath cue is removed entirely. Emphasis should be conservative; wrong emphasis is worse than no emphasis.
- Error or correction preserved: VOICE-035's German output was too fast/compressed for clear review. VOICE-036 restores a tiny `0.08s` breath and relaxes German speed to `1.065` for eligible freeform text only.
- Why it matters for the thesis: this checkpoint shows a listening-evaluation loop where a previous naturalness fix created a new intelligibility issue, then a narrower follow-up layer corrected the issue while preserving safety boundaries.
- Open questions: whether a fresh live RESP-003 listening check with VOICE-036 confirms German intelligibility and whether English still needs semantic emphasis modeling beyond the conservative guard.

### 2026-05-06 - RESP-003 VOICE-035 live listening check

- Objective: evaluate whether VOICE-035 connected-speech phrase flow improved the English/German live audio after VOICE-034 pacing calibration.
- Action taken: Tarik ran the German and English RESP-003 live ElevenLabs commands with VOICE-035 active, listened to both MP3 outputs, and gave qualitative feedback.
- Data used: synthetic German B2C telecom and English B2B software runtime turns only. No customer/private audio, transcription, or voice cloning was used.
- Output created: `research/experiments/generated/RESP-003/voice-035-listening-check/de-live.json`, `research/experiments/generated/RESP-003/voice-035-listening-check/en-live.json`, their generated MP3 files under `research/experiments/generated/RESP-003/voice-035-listening-check/audio/`, and `research/experiments/generated/RESP-003/voice-035-listening-check/human-listening-review.md`.
- What was learned: German was too fast/compressed to judge pauses or fillers clearly. English sounded better than before, but still somewhat robotic, likely because emphasis can land on the wrong words.
- Interpretation: the next layer should not add more filler by default. It should relax German connected speech and add an emphasis-target guard.
- Why it matters for the thesis: this is an example of human-in-the-loop voice evaluation producing a concrete, reproducible follow-up checkpoint.
- Open questions: whether VOICE-036 resolves the German intelligibility issue without reducing the connected-speech improvement.

### 2026-05-05 - VOICE-035 connected speech phrase flow

- Objective: address Tarik's VOICE-034 listening feedback that both English and German still sounded slightly robotic because spoken phrases felt too isolated, with weak word-to-word flow and written punctuation artifacts.
- Action taken: added a failing VOICE-035 validator first, implemented `scripts/voice_connected_speech.py`, wired it into `RESP-002` after VOICE-034 pacing calibration, added a standalone runner/case set/report path, and updated RESP-002/RESP-003 validators and setup/drift guards.
- Data used: synthetic German B2C telecom and English B2B software runtime turns only. No provider key, generated audio, customer/private audio, transcription, or voice cloning was used.
- Output created: `docs/product/VOICE_035_CONNECTED_SPEECH_PHRASE_FLOW.md`, `research/experiments/cases/voice-035-connected-speech-phrase-flow.json`, `research/experiments/generated/VOICE-035-connected-speech/results.json`, `research/experiments/generated/VOICE-035-connected-speech/report.md`, `scripts/voice_connected_speech.py`, `scripts/run_voice_035_connected_speech.py`, and `scripts/validate_voice_035_connected_speech.py`.
- What was learned: connected speech should be treated as a separate provider-facing delivery layer, not as a change to the guarded sales answer or a change to speed bounds. VOICE-034 owns speed/break calibration; VOICE-035 owns safe phrase-flow joins for eligible freeform TTS text.
- Error or correction preserved: the implementation intentionally avoids broad cultural/accent imitation. English and German rules target punctuation and filler/bridge boundaries only, keeping protected campaign, compliance, handoff, hangup, and do-not-call text exact.
- Why it matters for the thesis: this checkpoint records a concrete example of listening-driven iterative design: after pacing improved, the next naturalness bottleneck became connected-speech realism.
- Open questions: whether a short live RESP-003 listening check confirms that VOICE-035 improves naturalness without making English or German too rushed, and whether further tuning should happen in provider voice settings rather than more text rewriting.

### 2026-05-05 - RESP-003 VOICE-034 live listening check

- Objective: evaluate whether VOICE-034 pacing calibration improved German and English RESP-003 audio enough to avoid further pacing-bound changes.
- Action taken: Tarik reran RESP-003 live generation with local improved ElevenLabs voice IDs after removing environment voice-ID overrides, listened to the German and English outputs, and provided qualitative feedback.
- Data used: synthetic German B2C telecom and English B2B software runtime turns only. The run used live ElevenLabs TTS, local voice IDs from ignored config, no customer/private audio, no transcription, and no voice cloning.
- Output created: `research/experiments/generated/RESP-003/voice-034-listening-check/de-live-local-config.json`, `research/experiments/generated/RESP-003/voice-034-listening-check/en-live-local-config.json`, and `research/experiments/generated/RESP-003/voice-034-listening-check/human-listening-review.md`.
- What was learned: German pacing and word gaps sound good, and English pacing and pause timing also sound good. On second listen, German still has some robotic quality too, so the remaining issue is bilingual rather than English-only.
- Interpretation: the remaining issue is probably not simple latency, pause length, or speaking speed. Tarik described it as a lack of natural connected speech: humans tend to link the end of one word into the start of the next, giving spoken language a flowing rhythm rather than isolated written-word spacing. VOICE-035 should therefore handle English and German phrase flow together.
- Why it matters for the thesis: this is a useful example of iterative listening evaluation. A successful pacing fix exposed a more specific naturalness limitation: connected-speech realism and phrase flow.
- Open questions: whether bilingual `VOICE-035` should encode connected-speech hints as provider text normalization, phrase grouping metadata, punctuation shaping, or provider-side prompt/voice-setting guidance.

### 2026-05-05 - VOICE-034 pacing calibration V2

- Objective: tighten runtime voice pacing after listening feedback found the German outputs had too much gap between words and the overall sales-agent pace still needed more movement.
- Action taken: added a failing VOICE-034 validator first, implemented `scripts/voice_pacing_calibration.py`, wired it into `RESP-002` after provider rendering, added a standalone runner and bilingual/protected case set, and documented the checkpoint.
- Data used: synthetic English/German runtime cases from `PROD-005` only. No provider key, generated audio, customer/private audio, transcription, or voice cloning was used.
- Output created: `docs/product/VOICE_034_PACING_CALIBRATION_V2.md`, `research/experiments/cases/voice-034-pacing-calibration-v2.json`, `research/experiments/generated/VOICE-034-pacing-calibration-v2/results.json`, `research/experiments/generated/VOICE-034-pacing-calibration-v2/report.md`, `scripts/voice_pacing_calibration.py`, `scripts/run_voice_034_pacing_calibration.py`, and `scripts/validate_voice_034_pacing_calibration.py`.
- What was learned: pacing should be calibrated as provider-facing delivery metadata after the response is safe, not by rewriting the sales answer. German needed a tighter gap profile than English, while protected campaign and compliance text should keep exact delivery.
- Error or correction preserved: the first standalone runner used the older `build_guarded_response_packet` call shape and missed the newer `silence_count` argument. The runner now passes `silence_count` with a default of `0`, keeping VOICE-034 compatible with the current call-control/silence API.
- Why it matters for the thesis: this records how human listening feedback becomes a reproducible bounded runtime intervention, separating subjective audio-quality iteration from policy-owned sales text.
- Open questions: whether the next live/listening run confirms the tighter German gaps, and whether pacing bounds should be adjusted before working on voice identity, emotion strength, or filler placement again.

### 2026-05-05 - VOICE-033 private speech sample readiness

- Objective: create a private metadata-only checkpoint that tells us when Tarik's local speech samples are ready for VOICE-030D.
- Action taken: added a failing VOICE-033 validator first, implemented `scripts/private_sample_readiness.py`, added the private readiness runner, documented thresholds and commands, and updated roadmap/check guards.
- Data used: synthetic private metadata fixtures only during validation. No real private Tarik audio, WhatsApp recording, customer audio, provider key, transcription, voice clone, or runtime personalization was used.
- Output created: `docs/product/VOICE_033_PRIVATE_SAMPLE_READINESS.md`, `research/experiments/cases/voice-033-private-sample-readiness.json`, `scripts/private_sample_readiness.py`, `scripts/run_voice_033_private_sample_readiness.py`, and `scripts/validate_voice_033_private_sample_readiness.py`.
- What was learned: the project needs a readiness gate between collecting private samples and running aggregate review. The useful decision signal is not just raw file count; it is analyzed feature count, conversion backlog, failed queue records, and source/language coverage.
- Why it matters for the thesis: this creates a reproducible stopping rule for when private speech-learning evidence is mature enough to review, while preserving local-only privacy and avoiding premature personalization.
- Open questions: when Tarik wants to run the first real VOICE-033 check, and whether the first VOICE-030D review should happen around 10 analyzed samples or wait closer to the stronger 100-sample target.

### 2026-05-05 - VOICE-032 local WhatsApp OGG conversion gate

- Objective: make WhatsApp voice-note imports practical without uploading private audio or broadening the converter before it is needed.
- Action taken: added a failing VOICE-032 validator first, implemented `scripts/private_audio_conversion.py`, added the OGG-first conversion runner, created a local ignored WhatsApp drop-folder README, documented the command workflow, and wired successful WAV conversions into VOICE-030C.
- Data used: synthetic fake `.ogg` fixtures and a fake local converter during validation. No real WhatsApp recording, private Tarik recording, customer audio, provider key, transcription, voice clone, or runtime personalization was used.
- Output created: `docs/product/VOICE_032_LOCAL_AUDIO_CONVERSION.md`, `research/experiments/cases/voice-032-local-audio-conversion.json`, `scripts/private_audio_conversion.py`, `scripts/run_voice_032_local_audio_conversion.py`, and `scripts/validate_voice_032_local_audio_conversion.py`.
- What was learned: WhatsApp exports voice notes as `.ogg`, so the safest immediate conversion scope is OGG-first rather than broad multimedia support. Missing local tooling should become an explicit status, `converter_missing_needs_local_ffmpeg`, instead of a confusing failure.
- Error or correction preserved: the first validator version tried to delete a synthetic `.ogg` fixture between test scenarios and hit a Windows access-denied file cleanup issue. The validator now uses fresh private fixture folders per scenario, matching the earlier Windows file-lock lesson from raw audio tests.
- Why it matters for the thesis: this checkpoint documents a privacy-preserving path for expanding owner speech samples from real-world local voice-note exports while preserving local-only processing and human review before runtime learning.
- Open questions: whether Tarik will want to mix WhatsApp samples into the first VOICE-030D review, and whether local ffmpeg should be installed or bundled later for smoother private conversion.

### 2026-05-05 - VOICE-031 feature-to-runtime mapping gate

- Objective: create a safe bridge from reviewed private speech features to future runtime voice settings without automatically changing the speaking agent.
- Action taken: added a failing VOICE-031 validator first, implemented `scripts/voice_feature_runtime_mapping.py`, added a synthetic/public runner, added private-summary read and private-output guards, documented the checkpoint, and recorded the deferred WhatsApp voice-note reminder.
- Data used: synthetic VOICE-030D-style aggregate feature fixtures only during validation. No real private Tarik audio, WhatsApp voice note, customer audio, provider key, transcript, voice clone, or runtime personalization was used.
- Output created: `docs/product/VOICE_031_FEATURE_RUNTIME_MAPPING.md`, `research/experiments/cases/voice-031-feature-runtime-mapping.json`, `scripts/voice_feature_runtime_mapping.py`, `scripts/run_voice_031_feature_runtime_mapping.py`, and `scripts/validate_voice_031_feature_runtime_mapping.py`.
- What was learned: private speech-learning needs a proposal gate between aggregate review and runtime behavior. Speech-burst count, energy variation, and mean speech RMS can be represented as review-only hints, while pause ratio and pause duration remain diagnostic-only because long owner pauses may reflect formulation time.
- Why it matters for the thesis: this preserves a reproducible privacy and safety boundary before personalization, and it documents how subjective voice-naturalness feedback becomes auditable runtime configuration rather than automatic copying of one speaker.
- Open questions: when enough owner samples exist, whether reviewed `VOICE-031` proposals should adjust provider speed, expressiveness, filler placement, or campaign voice profiles first.

### 2026-05-05 - VOICE-030D private feature review summary

- Objective: create a private human-review summary for VOICE-030C acoustic features before any runtime voice-setting work.
- Action taken: added a failing VOICE-030D validator first, implemented `scripts/run_voice_030d_private_feature_review.py`, added a private review case, created private JSON/Markdown output paths, and documented the command workflow.
- Data used: synthetic private validation feature fixtures only during validation. The runner is ready for Tarik's real private feature set, but real private review output should stay under `data/private/`.
- Output created: `docs/product/VOICE_030D_PRIVATE_FEATURE_REVIEW.md`, `research/experiments/cases/voice-030d-private-feature-review.json`, `scripts/run_voice_030d_private_feature_review.py`, and `scripts/validate_voice_030d_private_feature_review.py`.
- What was learned: feature review should summarize runtime candidates separately from diagnostic evidence. Pause-ratio and pause-duration metrics are useful context for understanding owner recordings, but should not become agent pacing targets.
- Why it matters for the thesis: this checkpoint shows the privacy-preserving bridge from raw owner speech, to acoustic features, to human-reviewed candidate signals without automatically tuning the deployed voice.
- Open questions: whether speech-burst count, energy variation, and mean speech RMS are sufficient for useful runtime tuning, and how to combine them with future local ASR transcript-pattern summaries.

### 2026-05-05 - VOICE-030C private learning queue

- Objective: make Tarik speech-sample learning more automatic while preserving the local-only private boundary and preventing unreviewed runtime personalization.
- Action taken: added a failing VOICE-030C validator first, implemented `scripts/private_speech_learning_queue.py`, wired `scripts/run_voice_030b_local_speech_capture.py` to call the queue after each saved recording/import, and documented the checkpoint.
- Data used: synthetic validation WAV and synthetic fake WebM fixture only. No real private Tarik recording was opened, no customer audio was used, and no provider key, ASR provider, TTS provider, LLM provider, transcript generation, voice cloning, or runtime personalization was used.
- Output created: `docs/product/VOICE_030C_PRIVATE_LEARNING_QUEUE.md`, `research/experiments/cases/voice-030c-private-learning-queue.json`, `scripts/private_speech_learning_queue.py`, and `scripts/validate_voice_030c_private_learning_queue.py`.
- What was learned: capture-time automation is useful only if it produces reviewable private queue states. WAV samples can be analyzed immediately; non-WAV samples should be queued for local conversion instead of silently failing or being sent to a provider.
- Speaker-context boundary: Tarik is a native Turkish speaker with high English proficiency. His speech can influence timing, filler placement, repair style, thinking pauses, sentence rhythm, and clear English delivery patterns, while the system should avoid cloning or overfitting the product voice to one speaker identity.
- Learning-signal correction: long owner pauses can reflect formulation time during complex instruction-giving, not desirable agent behavior. VOICE-030C now keeps `pause_ratio`, `average_pause_ms`, `longest_pause_ms`, and `silence_seconds` as diagnostic-only features and excludes them from runtime-learning candidates.
- Why it matters for the thesis: this creates an auditable transition from raw private owner speech samples to abstract delivery features while preserving human review before runtime use.
- Open questions: how many owner samples are enough to produce stable timing/rhythm guidance, how to combine VOICE-030C acoustic features with future local ASR transcript features, and how strongly owner-style signals should influence campaign-specific voice profiles.

### 2026-05-05 - VOICE-030B local speech capture/import

- Objective: create an intentional local storage path for Tarik speech recordings after metadata-only search did not find reusable Codex/ChatGPT microphone recordings on disk.
- Action taken: added a failing validator first, implemented `scripts/run_voice_030b_local_speech_capture.py`, added a localhost browser recorder, added existing-file import, wrote a private JSONL manifest, and documented the command workflow.
- Data used: synthetic validation WAV only. No real private Tarik recording, customer audio, provider key, ASR provider, TTS provider, LLM provider, transcript generation, or voice cloning was used.
- Output created: `docs/product/VOICE_030B_LOCAL_SPEECH_CAPTURE.md`, `research/experiments/cases/voice-030b-local-speech-capture.json`, `scripts/run_voice_030b_local_speech_capture.py`, and `scripts/validate_voice_030b_local_speech_capture.py`.
- What was learned: relying on desktop-app voice-input caches is not dependable; a product-grade personal speech-learning path needs explicit local capture/import with a private manifest and no public artifact.
- Why it matters for the thesis: this preserves an auditable privacy boundary between raw owner speech samples, later local feature extraction/transcription, and eventual reviewed runtime personalization.
- Open questions: whether browser WebM samples should be locally converted to WAV before VOICE-030A analysis, which local ASR option should be used next, and how reviewed owner-style patterns should be weighted against professional sales-agent delivery.
- Follow-up correction: after inspecting the recorder, browser capture was changed from WebM/Opus `MediaRecorder` output to local browser-side WAV encoding through Web Audio before upload. New HTTP recorder samples should now be directly usable by VOICE-030A, while already captured WebM files remain private historical inputs for later conversion if needed.

### 2026-05-05 - VOICE-030A raw audio local reader

- Objective: implement the first raw-audio learning step for Tarik speech samples while keeping transcription, provider calls, voice cloning, and runtime personalization out of scope.
- Action taken: added a failing VOICE-030A validator and synthetic WAV case first, implemented `scripts/raw_audio_speech_features.py`, added `scripts/run_voice_030_raw_audio_reader.py`, generated synthetic WAV fixtures under `.tmp`, extracted pause/rhythm/energy features, and documented the private-audio boundary.
- Data used: synthetic WAV fixtures only. No private recordings, provider keys, customer audio upload, ASR, TTS, LLM provider, transcript generation, or voice cloning were used.
- Output created: `docs/product/VOICE_030A_RAW_AUDIO_LOCAL_READER.md`, `research/experiments/cases/voice-030-raw-audio-local-reader.json`, `research/experiments/generated/VOICE-030A-raw-audio-local-reader/results.json`, `research/experiments/generated/VOICE-030A-raw-audio-local-reader/report.md`, `scripts/raw_audio_speech_features.py`, `scripts/run_voice_030_raw_audio_reader.py`, and `scripts/validate_voice_030_raw_audio_reader.py`.
- What was learned: raw audio can already provide useful delivery signals such as pause ratio, pause count, speech bursts, and energy variation without transcription. VOICE-030A should stay WAV-only until a local decoder/conversion path is reviewed.
- Error or correction preserved: the first parallel validation/generation run collided on a shared `.tmp` synthetic audio folder on Windows and produced a file-lock error. The runner now uses process-scoped synthetic audio folders to avoid cross-process deletion conflicts.
- Why it matters for the thesis: this separates acoustic delivery-pattern learning from transcript/semantic learning and provides a privacy-preserving bridge from raw audio to abstract speech features.
- Open questions: whether Tarik's captured recordings are WAV or need local conversion; which local ASR tool should follow `VOICE-030B`; and how audio features should be combined with VOICE-029 transcript-pattern features after human review.

### 2026-05-05 - VOICE-029 local speech profile learning scaffold

- Objective: start the local-only path for learning abstract delivery patterns from Tarik's speech style without reading raw audio, exporting private transcripts, cloning a voice, or calling providers.
- Action taken: added a failing validator and synthetic case first, implemented `scripts/personal_speech_profile.py`, added `scripts/run_voice_029_local_speech_profile.py`, added a private workspace initializer, generated a synthetic aggregate profile/report, and documented the privacy boundary.
- Data used: synthetic English/German speech-style fixture text only. No private recordings, provider keys, customer audio, raw transcript export, ASR provider, TTS provider, LLM provider, or voice cloning were used.
- Output created: `docs/product/VOICE_029_LOCAL_SPEECH_PROFILE_LEARNING.md`, `research/experiments/cases/voice-029-local-speech-profile-learning.json`, `research/experiments/generated/VOICE-029-local-speech-profile-learning/results.json`, `research/experiments/generated/VOICE-029-local-speech-profile-learning/report.md`, `scripts/personal_speech_profile.py`, `scripts/run_voice_029_local_speech_profile.py`, `scripts/validate_voice_029_local_speech_profile.py`, and `scripts/init_personal_speech_learning_workspace.py`.
- What was learned: personal speech learning should begin as aggregate pattern extraction, not raw audio training. The profile can count filler markers, repair markers, contractions, pause markers, and sentence rhythm without copying private wording.
- Why it matters for the thesis: this creates a privacy-preserving methodological boundary between raw speech data, redacted local transcripts, abstract profile features, and later reviewed runtime configuration.
- Open questions: how to transcribe Tarik's actual recordings locally, how much of the resulting profile should influence runtime voice delivery, and whether owner-style learning improves naturalness without making the agent sound less professional.

### 2026-05-05 - VOICE-028 controlled delivery imperfections

- Objective: implement a bounded English/German layer for professional delivery imperfections so the voice agent does not sound perfectly machine-rendered.
- Action taken: added a failing VOICE-028 validator and bilingual case set first, implemented `scripts/speech_imperfections.py`, added the offline runner/report, wired the layer into `RESP-002` after interaction prosody and before provider-neutral prosody, and updated setup/drift guards.
- Data used: synthetic English/German freeform and protected-text cases, prior human listening feedback about robotic perfection, existing protected-segment rules, and existing unsafe-claim/stop-intent suppression logic. No provider key, private call-center audio, Tarik speech sample, customer audio upload, or voice cloning was used.
- Output created: `docs/product/VOICE_028_CONTROLLED_IMPERFECTIONS.md`, `research/experiments/cases/voice-028-controlled-imperfections.json`, `research/experiments/generated/VOICE-028-controlled-imperfections/results.json`, `research/experiments/generated/VOICE-028-controlled-imperfections/report.md`, `scripts/speech_imperfections.py`, `scripts/run_voice_028_controlled_imperfections.py`, and `scripts/validate_voice_028_controlled_imperfections.py`.
- What was learned: speech imperfections need to be opt-in, sparse, language-aware, and placed at thought boundaries. They should not appear in protected campaign questions, disclosures, unsafe claim handling, stop-intent responses, anger, or handoff contexts.
- Why it matters for the thesis: this turns subjective listening feedback about AI-perfect delivery into a reproducible bilingual runtime layer with explicit safety constraints and measurable offline validation.
- Open questions: whether live audio rendering makes these imperfections feel natural or whether the provider exaggerates them; whether future personal speech-pattern learning can improve placement without copying private speech or creating a voice clone.

### 2026-05-05 - VOICE-027 interaction-prosody live A/B harness

- Objective: create a live-capable listening harness that isolates whether `VOICE-026` interaction prosody improves perceived English/German sales-agent voice quality over the current `VOICE-025` boundary-aware baseline.
- Action taken: added a failing validator and bilingual case set first, implemented `scripts/run_voice_027_interaction_prosody_live_ab.py`, reused the VOICE-024 provider safety pattern, added dry-run and forced-missing-key validation, and documented the checkpoint.
- Data used: synthetic English/German sales scripts, existing improved local ElevenLabs voice candidates from ignored config when available, public provider interface behavior already captured in project docs, and existing protected-segment rules. No private call-center audio, customer identifiers, provider keys, or voice cloning were used.
- Output created: `docs/product/VOICE_027_INTERACTION_PROSODY_LIVE_AB.md`, `research/experiments/cases/voice-027-interaction-prosody-live-ab.json`, `scripts/run_voice_027_interaction_prosody_live_ab.py`, and `scripts/validate_voice_027_interaction_prosody_live_ab.py`.
- What was learned: the live-comparison shell can isolate a single speech-behavior layer while preserving strict provider boundaries. The dry-run packet verifies that `with_voice_026` adds interaction markers and the baseline does not, without making provider calls. Tarik then listened to limited live English/German outputs and reported that the result sounds much better than earlier voice checkpoints, with pacing now the main remaining issue.
- Why it matters for the thesis: this prepares a controlled listening experiment for the speech-realism chapter: same voice, same provider, same script, same speech-realism baseline, one isolated interaction-prosody variable.
- Output created after listening: `research/experiments/generated/VOICE-027-interaction-prosody-live-ab/human-listening-review.md`.
- Open questions: how much faster the sales-call pace should become before clarity, trust, or German pronunciation begins to degrade.

### 2026-05-04 - VOICE-026 interaction prosody implementation

- Objective: implement the next speech-realism checkpoint by separating listener backchannels, lookup acknowledgements, and bounded sales-pace cues from speaker fillers.
- Action taken: added a failing VOICE-026 validator and bilingual case set first, implemented `scripts/speech_interaction.py`, added the offline runner/report, wired the layer into `RESP-002` after speech realism and before provider-neutral prosody, and updated setup/drift guards.
- Data used: public speech-realism references captured in `SPEECH_REALISM_REFERENCES.md`, synthetic English/German sales cases, and existing protected-segment rules. No private call-center audio, customer identifiers, provider keys, or live TTS calls were used.
- Output created: `research/experiments/generated/VOICE-026-interaction-prosody/results.json`, `research/experiments/generated/VOICE-026-interaction-prosody/report.md`, `docs/product/VOICE_026_INTERACTION_PROSODY.md`, `scripts/speech_interaction.py`, `scripts/run_voice_026_interaction_prosody.py`, and `scripts/validate_voice_026_interaction_prosody.py`.
- What was learned: natural speech behavior needs typed interaction cues rather than more random fillers. Lookup acknowledgements, neutral backchannels, and pace variation can improve perceived responsiveness, but protected campaign text and unsafe-claim contexts must block agreement-style markers.
- Error or correction preserved: `RESP-003` validation originally checked spoken English contractions case-sensitively; after VOICE-025 inserted `Well,` before `You're`, the provider-facing text correctly became `you're`. The validator was updated to check contraction presence case-insensitively while keeping forbidden full forms blocked.
- Why it matters for the thesis: this creates a testable bridge from literature review and listening feedback into the runtime architecture, with bilingual rules and a listening rubric covering naturalness, trust, confidence, warmth, pace, interruption safety, sales usefulness, and protected-text safety.
- Open questions: the next live ElevenLabs comparison should test whether these cues improve perceived human-likeness without making the agent sound over-emotional or falsely agreeable.

### 2026-05-04 - SPEECH-STYLE-003 final broad speech-realism literature sweep

- Objective: perform one last broader speech-science search before implementing `VOICE-026`, so the next voice checkpoint is informed by speech behavior beyond fillers and German/English discourse markers.
- Action taken: reviewed additional sources on general prosody, acoustic emotion, vocal first impressions, turn-taking distributions, conversational-system timing, entrainment/accommodation, spoken corpora, connected-speech reductions, text normalization, German spontaneous-speech reductions, acoustic charisma, and speech-synthesis evaluation.
- Data used: public scholarly/provider/corpus sources only; no private call-center audio, customer identifiers, provider keys, or restricted corpus examples.
- Output created: expanded `docs/thesis/SPEECH_REALISM_REFERENCES.md` and `docs/thesis/THESIS_REFERENCE_REGISTRY.md`.
- What was learned: the planned `VOICE-026` direction still holds, but it should evaluate more than "does it sound natural?" It should separate naturalness, trust, confidence, warmth, pace, interruption safety, sales usefulness, and protected-text safety.
- Why it matters for the thesis: this broadens the voice work from a filler-word experiment into a speech-behavior design layer grounded in prosody, turn-taking, entrainment, connected speech, and TTS evaluation literature.
- Open questions: whether adaptive entrainment to customer pace/energy should become a later `VOICE-03x` checkpoint after latency, interruption, and protected-text behavior are stable.

### 2026-05-04 - SPEECH-STYLE-002 deep English/German speech-pattern review

- Objective: run a broader web/literature checkpoint before the next voice implementation so the product does not keep fixing robotic speech one symptom at a time.
- Action taken: searched and triaged sources on English disfluencies, English discourse markers, German fillers/discourse markers, German backchannels, turn-taking latency, speech-synthesis filled-pause placement, provider prosody controls, breath/smiled speech, and sales/call-center vocal cues.
- Data used: public scholarly/provider sources only; no private call-center audio, raw customer data, provider keys, or restricted transcripts.
- Output created: expanded `docs/thesis/SPEECH_REALISM_REFERENCES.md`, updated `docs/thesis/THESIS_REFERENCE_REGISTRY.md`, and added a deep-dive follow-up section to `docs/product/VOICE_025_FILLER_PLACEMENT.md`.
- What was learned: the remaining realism gap is not just filler placement. Speaker fillers, discourse markers, listener backchannels, turn-taking latency, speech rate, pitch/intonation, and provider prosody controls must be modeled as separate but coordinated layers.
- Why it matters for the thesis: this creates a stronger literature-backed transition from listening feedback to a planned `VOICE-026` interaction-prosody/backchannel checkpoint, while preserving the non-stereotype bilingual design principle.
- Open questions: whether `VOICE-026` should first be offline-only or immediately include a live ElevenLabs comparison after the new interaction markers and pace/prosody controls pass validation.

### 2026-05-04 - VOICE-025 boundary-aware filler placement implementation

- Objective: fix unnatural English/German filler placement while preserving the shared vertical-agnostic sales-agent runtime and protected campaign text boundaries.
- Action taken: added a failing VOICE-025 validator first, changed `scripts/speech_realism.py` from mid-clause insertion to boundary-aware insertion, added German-specific `also`, `ähm`, `äh`, and `hm` placement rules, added a VOICE-025 runner/case set/report, updated setup checks, and regenerated the VOICE-023/VOICE-025 offline reports in organized generated folders.
- Data used: VOICE-024 listening feedback, VOICE-025 filler-placement research, German filler-particle and German turn-beginning sources, and synthetic English/German sales-response cases.
- Output created: `research/experiments/generated/VOICE-025-filler-placement/results.json`, `research/experiments/generated/VOICE-025-filler-placement/report.md`, `docs/product/VOICE_025_FILLER_PLACEMENT.md`, `scripts/run_voice_025_filler_placement.py`, and `scripts/validate_voice_025_filler_placement.py`.
- What was learned: the old rule could split fluent clause frames such as `the important thing is that` and `Wichtig ist, dass`; the new rule moves fillers before the planning sentence or to a sentence boundary. German needed its own profile rather than translated English markers, especially for `also`, `äh`, and `ähm`.
- Why it matters for the thesis: this is a clear example of using human listening feedback plus linguistic literature to refine an AI voice behavior layer under guardrails.
- Open questions: the next live audio test should compare whether German `äh`/`ähm` are rendered naturally by ElevenLabs or whether some German campaigns should prefer `also`/pause-only cues.

### 2026-05-04 - VOICE-025 filler-placement research

- Objective: ground the next speech-realism refinement in evidence about where fillers belong in spoken interaction, rather than adding filler words randomly.
- Action taken: reviewed the current `speech_realism.py` insertion logic, checked the VOICE-024 case that produced unnatural English placement, inspected the Obscura safe-browser wrapper constraints, and searched scholarly/provider sources on filled pauses, discourse boundaries, turn beginnings, confidence perception, German filler particles, and ElevenLabs pacing controls.
- Data used: VOICE-024 human listening feedback, `scripts/speech_realism.py`, `voice-024-speech-realism-live-ab.json`, Obscura safe-wrapper docs, and public web sources captured in `SPEECH_REALISM_REFERENCES.md`.
- Output created: updated `docs/thesis/SPEECH_REALISM_REFERENCES.md` and `docs/thesis/THESIS_REFERENCE_REGISTRY.md` with filler-placement, confidence-perception, German turn-beginning, and provider-control references.
- What was learned: the current pattern-based insertion can create unnatural mid-clause examples such as placing `um` after "The important thing is" before `that`; the next design should prefer pre-answer, sentence-boundary, discourse-transition, repair/reformulation, or pause-only cues. Obscura remains a development-only research tool and the approved wrapper could not run a live fetch in this session because the verified Docker image was unavailable.
- Why it matters for the thesis: this creates a literature-backed bridge from subjective listening feedback to a testable VOICE-025 rule change, while preserving the bilingual, non-stereotype framing.
- Open questions: whether VOICE-025 should implement all placement modes at once or first compare a small A/B/C set: current VOICE-023, boundary-aware fillers, and pause-only thinking cues.

### 2026-05-04 - VOICE-024 speech-realism live A/B harness

- Objective: isolate whether VOICE-023 speech realism improves perceived English/German sales-agent audio when the voice, provider, script, and timeout stay constant.
- Action taken: added a VOICE-024 case set, dry-run/live-capable ElevenLabs A/B runner, validator, product documentation, setup/drift guard entries, organized run-folder defaults, and generated JSON/report artifacts.
- Data used: synthetic English/German sales responses, improved ElevenLabs local voice IDs from ignored config, VOICE-022 spoken text normalization, VOICE-023 speech realism, and VOICE-015/016 prosody/provider rendering.
- Output created: `research/experiments/generated/VOICE-024-speech-realism-live-ab/results.json`, `research/experiments/generated/VOICE-024-speech-realism-live-ab/report.md`, and ignored MP3 files under `research/experiments/generated/VOICE-024-speech-realism-live-ab/audio/`.
- What was learned: this Codex terminal did not have `ELEVENLABS_API_KEY`, so live MP3 generation happened in Tarik's key-bearing terminal; the resulting live packet and 8 MP3 files were organized under the VOICE-024 run folder.
- Human listening feedback: German `with_voice_023` outputs sounded clearly better to Tarik, with the caveat that his German fluency may affect confidence. English outputs are close to the intended direction and the concept feels strong, but filler words sometimes appear in the wrong place.
- Error or correction preserved: the first raw voice-ID artifact scanner was too broad and incorrectly flagged metadata such as language labels; it was tightened to scan only actual voice-ID fields.
- Error or correction preserved: validator runs now use isolated `.tmp` output paths so they do not overwrite live listening reports or remove previously generated MP3 files.
- Why it matters for the thesis: VOICE-024 gives the thesis an ablation-style listening experiment, separating provider/custom-voice quality from the local speech-realism layer.
- Open questions: whether `VOICE-025` should refine filler placement by moving English fillers to pre-answer or sentence-boundary positions, reducing mid-clause fillers, and comparing filler placement against pause-only thinking cues.

### 2026-05-04 - VOICE-023 speech realism layer

- Objective: make eligible English/German freeform TTS text sound less robotic by adding bounded thinking-filler bundles without changing protected campaign or compliance text.
- Action taken: added `speech_realism.py`, a VOICE-023 runner, case set, validator, generated report, and RESP-002 runtime integration after spoken-text normalization and before prosody/provider rendering.
- Data used: synthetic English/German voice cases, current RESP-002/RESP-003 runtime packets, existing speech-realism references, and protected segment rules from earlier voice checkpoints.
- Output created: `VOICE-023-speech-realism.json`, `VOICE-023-speech-realism-report.md`, and runtime `speech_realism` packets inside voice delivery.
- What was learned: German language validation cannot treat `um` as an English filler because `um` is also a normal German preposition. The guard now avoids that false positive and currently limits German provider-facing fillers to `hm` and `also` until live provider listening tests confirm better forms.
- Why it matters for the thesis: this checkpoint turns subjective listening feedback about robotic pacing into a testable, bilingual, guardrailed speech-realism layer.
- Open questions: whether live ElevenLabs output should prefer visible fillers, provider pauses, voice-setting emotion controls, or a smaller combination of all three.

### 2026-05-04 - TRACE-001 pre-push thesis traceability gates

- Objective: make thesis documentation updates and source reference capture harder to forget before GitHub checkpoints.
- Action taken: added local guard scripts for thesis reference coverage and thesis-update coverage, plus validators and command-map documentation.
- Data used: existing project docs, research cases, provider/source URLs, current Git status, and thesis tracking files.
- Output created: `check_thesis_reference_registry.py`, `check_thesis_update_gate.py`, corresponding validators, command-map entries, and source-registry additions for missed provider links.
- What was learned: a useful guard must distinguish real source URLs from generated artifacts, local demo URLs, and provider API endpoints; otherwise it creates noisy failures that people will learn to ignore.
- Why it matters for the thesis: the writing phase should not depend on chat memory. Sources, decisions, and errors/fixes need to remain visible in project files as the implementation changes.
- Open questions: whether to later add an optional local pre-push hook after the visible command-based gate has proven useful.

### 2026-05-04 - VOICE-021 live custom voice listening review

Context:

- Tarik ran the full `VOICE-021` live comparison for English and German original-vs-improved ElevenLabs custom voices.
- All 8 audio files were created successfully.
- The improved English and German voices were clearly preferred over the first versions.

Human listening feedback:

- Improved versions for both German and English are definitely much better.
- Pace seems acceptable.
- Pitch variation seems acceptable, but still not fully natural.
- Emotional responsiveness may be slightly too high, but still usable.
- No muffling was noticed.
- Pronunciation seems good.
- The remaining realism gap is thinking behavior: humans often fill pauses with short hesitation sounds or filler words instead of leaving a clean break.
- Current thinking time is not long enough.
- Pitch variance is improving, but still does not yet feel fully natural.

Interpretation:

- The next improvement should not simply increase emotion.
- The next useful checkpoint should add controlled cognitive hesitation: short thinking fillers inside pauses, longer bounded thinking breaks, and less theatrical pitch movement.
- This should remain blocked for protected campaign questions, disclosures, compliance, handoff, hangup, and exact company-script segments.

Next checkpoint implication:

- Design `VOICE-023` as a thinking-filler and natural hesitation layer for eligible freeform speech, with English and German support.

### 2026-05-04 - VOICE-021 ElevenLabs custom voice comparison setup

Context:

- Tarik created first-version and improved-version ElevenLabs voices for English and German.
- The improved versions came from the naturalness/remixing prompt work around `VOICE-020`.
- We needed a safe way to compare all four voices without putting raw voice IDs into tracked files.

Action:

- Stored the four raw voice IDs in ignored `config/local/voice_ids.json`.
- Extended the local voice config helper to resolve named voice candidates.
- Added `research/experiments/cases/voice-021-elevenlabs-custom-voice-comparison.json`.
- Added `scripts/run_voice_021_custom_voice_comparison.py`.
- Added `scripts/validate_voice_021_custom_voice_comparison.py`.
- Generated the dry-run packet and report for the four-way comparison.
- Added documentation in `docs/product/VOICE_021_ELEVENLABS_CUSTOM_VOICE_COMPARISON.md`.

Result:

- Dry-run comparison contains 4 candidates, 4 scripts, and 8 planned audio outputs.
- No provider calls were made.
- No audio was created yet.
- Generated artifacts do not include raw voice IDs.
- Customer audio upload and voice cloning remain false.

Interpretation:

- `VOICE-021` creates the decision point for choosing the default English and German voices.
- The live step still needs `ELEVENLABS_API_KEY` and human listening ratings before making quality claims.
- This keeps voice selection separate from response quality, spoken-text normalization, and provider prosody rendering.

### 2026-05-04 - VOICE-022 bilingual spoken-text normalization

Context:

- Listening feedback showed that even improved provider voices could sound robotic when they read written phrasing too literally.
- A concrete example was English `I will`, which a human sales agent would often say as `I'll`.
- The same issue needed German handling, but German spoken normalization had to stay conservative and professional.

Action:

- Added `scripts/spoken_text_normalization.py`.
- Added `scripts/run_voice_022_spoken_text_normalization.py`.
- Added `scripts/validate_voice_022_spoken_text_normalization.py`.
- Added `research/experiments/cases/voice-022-spoken-text-normalization.json`.
- Generated `research/experiments/generated/VOICE-022-spoken-text-normalization.json`.
- Generated `research/experiments/generated/VOICE-022-spoken-text-normalization-report.md`.
- Documented the layer in `docs/product/VOICE_022_SPOKEN_TEXT_NORMALIZATION.md`.
- Wired VOICE-022 into `RESP-002` before prosody and provider rendering.
- Extended `RESP-003` validation so optional live TTS uses spoken-normalized/provider-rendered text only for eligible freeform segments.

Result:

- VOICE-022 covers 8 cases: 4 English and 4 German.
- The layer produced 11 normalizations across eligible freeform segments.
- Protected segment changes stayed at 0.
- RESP-002 and RESP-003 validators pass with both English and German spoken-normalized candidate responses.
- The guarded `final_response` remains unchanged.

Interpretation:

- This is a text-preparation layer, not a provider-specific voice-design replacement.
- It complements ElevenLabs voice design/remixing by making the provider input less written and less robotic.
- It preserves the vertical-agnostic architecture because the behavior is controlled through campaign/runtime segment metadata rather than hard-coded product assumptions.

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

### 2026-05-03 - CTX-001 automatic relevant-reader policy

- Objective: make the project-local relevant reader the default first step for large documentation reads, so future work can find the right context without reading entire long files by habit
- Action taken:
  - added a context-reading policy document
  - added a project validator that confirms the policy, command map, reader, and project instructions stay wired together
  - updated `AGENTS.md` so future project sessions see the rule directly
  - added the validator to setup checks and product review gates
- Data used:
  - current `scripts/read_relevant.py` behavior
  - `docs/product/COMMANDS.md` relevant-file-reading command examples
  - project need for self-contained, context-efficient documentation workflows
- Output created:
  - `docs/product/CONTEXT_READING_POLICY.md`
  - `scripts/validate_context_reading_policy.py`
- What was learned:
  - the relevant reader already existed and passed validation
  - setup validation already tracked the reader files, but the project did not yet have an explicit automatic-use rule
  - the durable place for this rule is project-local `AGENTS.md`, backed by a validator
- Error or risk recorded:
  - this is not a background watcher and cannot force every future model call to use the reader
  - the rule should stay flexible for code files, schemas, validators, and cases where whole-file consistency matters
- Why it matters for the thesis:
  - it documents a practical context-management improvement during iterative system development
  - it helps preserve reliable thesis/product documentation work as the repo grows
  - it supports reproducible project-local workflows rather than depending on external workspace memory tools
- Open questions:
  - whether a future CI check should enforce the policy validator
  - whether the reader should later produce compact summaries for repeated thesis-writing sessions

### 2026-05-03 - VOICE-018 professional-sales voice tuning

- Objective: respond to listening feedback that the live bilingual TTS was clear but too slow, flat, and still obviously AI-generated for real sales leads
- Action taken:
  - added an offline sales voice tuning layer on top of VOICE-016 provider previews
  - increased eligible freeform speech speed with bounded professional-sales ratios
  - compressed existing break tags to reduce robotic slowness
  - added emotion and pitch intent metadata for later provider tests
  - kept protected campaign, disclosure, do-not-call, hang-up, and sensitive text exact
  - added a validator and generated JSON/Markdown evidence
- Data used:
  - `research/experiments/generated/VOICE-016-provider-prosody-rendering.json`
  - first VOICE-017 and RESP-003 listening feedback
  - existing protected-segment taxonomy from VOICE-012 through VOICE-016
- Output created:
  - `scripts/sales_voice_tuning.py`
  - `scripts/run_voice_018_sales_voice_tuning.py`
  - `scripts/validate_voice_018_sales_voice_tuning.py`
  - `research/experiments/cases/voice-018-sales-voice-tuning.json`
  - `research/experiments/generated/VOICE-018-sales-voice-tuning.json`
  - `research/experiments/generated/VOICE-018-sales-voice-tuning-report.md`
  - `docs/product/VOICE_018_SALES_VOICE_TUNING.md`
- Technical result:
  - cases: 8
  - German cases: 4
  - English cases: 4
  - sales-tuned variants: 16
  - tuned segments: 12
  - protected segments: 14
  - pause compressions: 10
  - average eligible speed ratio: 1.11
  - max speed ratio: 1.142
  - protected text changes: 0
  - provider calls made: false
  - customer audio uploaded: false
  - voice cloning used: false
- What was learned:
  - speed and emotion can be tuned as structured delivery metadata before live provider calls
  - protected scripted/compliance text can remain exact while eligible freeform speech receives sales-call pacing
  - the current artifact is a provider-input improvement, not an audio quality claim
- Error or risk recorded:
  - request-level provider speed, especially for ElevenLabs, may affect all text in a single provider call unless the runtime later splits segments
  - pitch and emotion intent remain metadata until provider-specific live tests prove a safe mapping
  - human listening review is still required before claiming the tuned voice is better
- Why it matters for the thesis:
  - it turns qualitative listening feedback into a measurable, reproducible engineering iteration
  - it preserves the thesis distinction between text safety, delivery planning, provider rendering, live synthesis, and human listening evaluation
  - it documents a realistic product limitation: live voice naturalness requires iterative tuning beyond correct response content
- Open questions:
  - whether VOICE-018 sounds better in live ElevenLabs and/or Cartesia audio
  - whether per-segment TTS calls are needed so protected text can keep neutral pace while freeform speech is faster
  - whether the listening rubric should explicitly score sales pace, pitch contour, and AI-obviousness

### 2026-05-03 - VOICE-019 sales-tuned live A/B harness

- Objective: prepare a safe live listening test comparing VOICE-017-style prosody-shaped input against VOICE-018 professional-sales tuned input
- Action taken:
  - added a VOICE-019 case config selecting the same four bilingual source cases used by VOICE-017
  - added a live-capable runner that creates prosody and sales-tuned variants for ElevenLabs and Cartesia
  - reused the VOICE-017 provider-call helpers and safety boundaries
  - kept dry-run as the default behavior
  - added forced-missing-key fallback validation for both providers
  - added Git ignore rules for future VOICE-019 MP3/WAV live audio artifacts
- Data used:
  - `research/experiments/generated/VOICE-018-sales-voice-tuning.json`
  - `research/experiments/cases/voice-017-live-ab-audio.json`
- Output created:
  - `scripts/run_voice_019_sales_tuned_live_ab_audio.py`
  - `scripts/validate_voice_019_sales_tuned_live_ab_audio.py`
  - `research/experiments/cases/voice-019-sales-tuned-live-ab-audio.json`
  - `research/experiments/generated/VOICE-019-sales-tuned-live-ab-audio.json`
  - `research/experiments/generated/VOICE-019-sales-tuned-live-ab-audio-report.md`
  - `docs/product/VOICE_019_SALES_TUNED_LIVE_AB_AUDIO.md`
  - `research/experiments/VOICE-019-sales-tuned-live-ab-audio.md`
- Dry-run result:
  - cases: 4
  - German cases: 2
  - English cases: 2
  - providers: ElevenLabs and Cartesia
  - A/B variants: 16
  - prosody variants: 8
  - sales-tuned variants: 8
  - API calls made: 0
  - audio files created: 0
  - fallback count: 16
  - customer audio uploaded: false
  - voice cloning used: false
  - quality claim allowed: false
- What was learned:
  - the project can compare the previous prosody-shaped input against the new sales-tuned input without changing provider-key safety rules
  - the dry-run packet is ready for a controlled live run once provider keys and voice IDs are set in the same terminal
  - quality claims still need human listening review after audio exists
- Error or risk recorded:
  - live provider calls can create up to 8 calls per provider for the default four-case set, so the recommended first run uses `--limit 2`
  - ElevenLabs request-level speed may still affect full utterances unless future runtime splitting is added
  - dry-run validation proves structure and safety, not sound quality
- Why it matters for the thesis:
  - this creates a concrete experiment path from qualitative listening feedback to a controlled A/B audio evaluation
  - it preserves privacy and provider-safety gates while allowing repeatable human listening comparison
  - it supports honest reporting by separating dry-run readiness from live audio preference evidence
- Open questions:
  - whether sales-tuned audio is preferred over current prosody audio by the project owner
  - whether Cartesia's richer speed/volume tags or ElevenLabs' voice settings produce better sales-call pacing
  - whether a second listener should review the same A/B outputs before the thesis treats the result as stronger evidence

### 2026-05-03 - Roadmap checkpoint discipline and deferred-idea queue

- Objective: make the roadmap function as an operational checkpoint board rather than only a narrative planning document
- Action taken:
  - added roadmap operating rules for current phase tracking, checkpoint completion, and direction changes
  - added a checkbox-based checkpoint board with current, next, and recently completed checkpoints
  - added a deferred implementation queue for good ideas that are intentionally too early to build
  - defined unlock conditions so deferred ideas can be resurfaced when their phase becomes active
- Data used:
  - project owner's request that future-too-early implementation ideas should be preserved and resurfaced later
  - current voice/runtime, product-learning, and thesis-evidence roadmap state
- Output created:
  - updated `docs/thesis/ROADMAP.md`
- What was learned:
  - the project needs a lightweight planning memory because product discovery changes the order of work over time
  - a fixed long-term plan would be too rigid, but an explicit checkpoint board can keep momentum without pretending the future is fully known
  - deferred ideas are most useful when each one has an unlock condition, not just a vague "later" label
- Why it matters for the thesis:
  - it preserves the research and engineering decision trail more clearly
  - it makes it easier to reconstruct why certain features were delayed, implemented, or reprioritized
  - it supports honest methodology writing by showing that iteration was planned, tracked, and reviewed
- Open questions:
  - how often the roadmap should be committed during rapid experimentation
  - whether later thesis writing should include the checkpoint board directly or summarize it as project-management methodology

### 2026-05-04 - VOICE-019 first live ElevenLabs listening review

- Objective: evaluate whether `VOICE-018` sales-tuned provider input improves live ElevenLabs audio over the previous `VOICE-017`-style prosody input
- Action taken:
  - ran `VOICE-019` live for ElevenLabs with `--limit 2`
  - generated English and German A/B audio files for prosody versus sales-tuned variants
  - collected project-owner listening feedback for both languages
  - updated the roadmap so `VOICE-020` targets emotional delivery and controlled human speech variation
- Data used:
  - `research/experiments/generated/VOICE-019-sales-tuned-live-ab-audio.json`
  - `research/experiments/generated/VOICE-019-sales-tuned-live-ab-audio-report.md`
  - generated local MP3 files ignored by Git
  - project-owner listening judgment
- Output created:
  - updated `research/experiments/VOICE-019-sales-tuned-live-ab-audio.md`
  - updated `docs/thesis/ROADMAP.md`
- Live run result:
  - cases: 2
  - languages: English and German
  - provider: ElevenLabs
  - API calls made: 4
  - audio files created: 4
  - fallbacks: 0
  - customer audio uploaded: false
  - voice cloning used: false
  - max time to first audio: 1875.891 ms
  - max total provider latency: 2058.027 ms
- Human listening result:
  - English preferred variant: sales-tuned
  - German preferred variant: sales-tuned
  - sales-tuned was judged much better than the previous prosody variant in both languages
  - the beginning still sounded rigid enough to trigger a "this is a robot" reaction
  - the audio improved after the phrase "the important thing is"
  - remaining issues include insufficient emotional expressiveness, too much prepared-script feeling, insufficient controlled randomness in spacing and voicing, and not enough campaign-safe conversational texture such as contractions, light fillers, and natural pauses
- What was learned:
  - the project should continue from the sales-tuned direction rather than reverting to the older prosody-only direction
  - the next voice-quality problem is not only speed; it is emotional delivery and human-like variation
  - opening phrases are especially important because they shape the listener's immediate robot-detection reaction
- Why it matters for the thesis:
  - this records human evaluation evidence after a live provider run while keeping the claim narrow and honest
  - it shows an iterative path from dry-run safety to live audio generation to qualitative listening feedback
  - it identifies concrete next variables for voice naturalness experiments: emotion, openings, spacing randomness, contractions, fillers, and protected-text boundaries
- Open questions:
  - whether ElevenLabs provider settings can express emotion strongly enough without changing the generated text
  - whether some emotional naturalness must be handled by text/segment generation before TTS
  - how to preserve compliance-safe exact wording while adding human-like speech texture around non-protected segments

### 2026-05-04 - VOICE-020 expressive gesture design constraint

- Objective: refine the next voice-naturalness checkpoint before implementation
- Action taken:
  - recorded that `VOICE-020` should not apply voice effects as isolated one-at-a-time toggles
  - updated the roadmap current checkpoint to include bundled expressive gestures
- Data used:
  - project-owner feedback that realistic speech often combines effects, such as a filler word with a slight upward pitch, rather than applying pause, filler, and pitch as separate mechanical steps
- Output created:
  - updated `docs/thesis/ROADMAP.md`
- What was learned:
  - human-like voice tuning should operate on grouped expressive gestures, not only independent scalar controls
  - realistic delivery may require coordinated bundles such as filler plus pitch lift, short pause plus softened restart, emphasis plus faster follow-through, or uncertainty marker plus lower confidence tone
  - the gesture layer must still avoid protected campaign questions, compliance statements, appointment confirmations, and hang-up lines unless the campaign explicitly allows variation
- Why it matters for the thesis:
  - it makes the voice-naturalness method more defensible by treating speech delivery as coordinated behavior rather than disconnected effects
  - it gives `VOICE-020` a clearer design target: emotional and conversational realism with guardrails
- Open questions:
  - which gesture bundles improve human-likeness without reducing trust
  - whether each campaign should choose an allowed gesture palette
  - how to evaluate bundled gestures separately from provider voice quality

### 2026-05-04 - Sales knowledge RAG before private-data fine-tuning

- Objective: decide how the agent should learn sales process knowledge before any private call-center data is available
- Action taken:
  - recorded `RAG-001` as a future source-tracked sales knowledge base and retrieval layer
  - deferred private call-center pattern mining and fine-tuning until data governance and baseline gates are ready
  - kept the product architecture as one reusable sales-agent core plus campaign profiles, guarded responses, voice delivery, and a future sales knowledge layer
- Data used:
  - project-owner direction that real sales agents are trained, so the AI agent should also learn from sales training material and later actual call-center calls
  - project-owner preference to postpone fine-tuning until private call-center sales data is available
  - GDPR/privacy constraint that private call data may include personal data, voice data, sensitive inferences, and legally restricted processing purposes
- Output created:
  - updated `docs/thesis/ROADMAP.md`
- What was learned:
  - RAG is the right first learning layer because it can use source-tracked sales knowledge without permanently changing model behavior
  - fine-tuning should come later, after the project has lawful access to private call-center data and a clear purpose for the trained behavior
  - private call-center data should first be used for analysis: repeated actions, repeated speech, objection patterns, successful transitions, escalation points, and winning/losing conversation structures
  - fine-tuning should not be raw data ingestion; it should use curated, minimized, permissioned examples derived from analysis
- Why it matters for the thesis:
  - it creates a defensible learning progression: public/source-tracked sales knowledge, then retrieval evaluation, then restricted private-data analysis, then possible fine-tuning
  - it separates knowledge access from model-weight adaptation, which makes evaluation and privacy boundaries clearer
  - it supports an honest thesis discussion of why private data improves product realism but requires stronger governance than public datasets
- Open questions:
  - which public or owned sales training materials can be used with clear rights
  - what legal basis, consent, processor/controller role, retention policy, and data-processing agreement would apply to private call-center data
  - whether call audio should ever be used directly, or whether transcripts with minimization and pseudonymization are sufficient
  - how to evaluate RAG-assisted responses against fine-tuned responses without leaking private data into reports or Git

### 2026-05-04 - Private call-center audio local storage boundary

- Objective: make the raw private call-center audio boundary explicit before any real private audio enters the project
- Action taken:
  - designated `data/private/` as the only local storage folder for raw private call-center audio and raw private call assets
  - added a project-local ignore rule so private files under `data/private/` do not go to GitHub
  - added a private call-center data policy document
  - updated setup checks so the local private-data folder and ignore rule are part of project health
  - updated the drift guard to skip scanning `data/private/` contents, preventing accidental inspection or reporting of private files
- Data used:
  - project-owner requirement that call-center audio files should live inside `D:\Codex\active\emotion-aware-ai-sales-agent\data\private`
  - project-owner requirement that those files never leave local folders or go to the repository
- Output created:
  - `data/private/.gitignore`
  - `docs/data/PRIVATE_CALL_CENTER_DATA_POLICY.md`
  - updates to `.gitignore`, `README.md`, `AGENTS.md`, `docs/data/DATA_USAGE_POLICY.md`, `docs/thesis/ROADMAP.md`, `scripts/check_setup.py`, `scripts/validate_check_setup.py`, and `scripts/check_project_drift.py`
- What was learned:
  - private call-center audio needs a named local path, not only a general "restricted data" concept
  - the project should allow safe local private-data work while keeping raw private audio out of Git, generated artifacts, provider calls, and thesis deliverables
  - local setup checks should protect the folder boundary before real data arrives
- Why it matters for the thesis:
  - it preserves a defensible separation between reproducible public evidence and restricted private data
  - it supports later private-data pattern mining and fine-tuning without weakening privacy boundaries
  - it creates an auditable methodology trail for why private audio was stored locally and excluded from the repository
- Open questions:
  - whether future private transcripts should also remain under `data/private/` by default
  - whether a separate local manifest format is needed before the first real call-center audio import

### 2026-05-04 - Private identifiers are not training signal

- Objective: prevent private personal details inside call recordings from becoming model/RAG/fine-tuning material
- Action taken:
  - added an explicit rule that private identifiers are not training signal
  - added an export review gate for anything derived from private call-center audio before it can leave `data/private/`
  - added a validator that checks the private-data policy, ignore rules, and drift-guard skip rule without scanning private file contents
- Data used:
  - project-owner concern that real call recordings may contain names, addresses, phone numbers, and other private details that are not useful sales-learning signal
  - GDPR-oriented data-minimization principle that personal data should be limited to what is necessary for the processing purpose
- Output created:
  - `scripts/validate_private_data_boundary.py`
  - updates to `docs/data/PRIVATE_CALL_CENTER_DATA_POLICY.md`
  - updates to `docs/data/DATA_USAGE_POLICY.md`
  - updates to `docs/product/COMMANDS.md`
  - setup and drift-guard validation updates
- What was learned:
  - private call-center learning should extract patterns, not identities
  - the useful signal is objection type, emotion state, sales strategy, response pattern, turn structure, and outcome
  - identifiers, exact private facts, and sensitive details should stay in `data/private/` and be removed before any artifact is used for RAG, fine-tuning, reports, or Git
- Why it matters for the thesis:
  - it keeps later private-data experiments methodologically defensible
  - it separates sales-behavior learning from personal-data retention
  - it supports a clear public/private evidence boundary in the final write-up
- Open questions:
  - whether the first export review should be manual-only or assisted by a local redaction script
  - which fields belong in a future minimized private-call pattern schema

### 2026-05-04 - VOICE-020 ElevenLabs voice design packet

- Objective: turn `VOICE-019` listening feedback into a provider-aware ElevenLabs voice design checkpoint before creating or selecting new voices
- Action taken:
  - added an offline `VOICE-020` case/config file with English and German sales-agent voice prompts
  - added settings candidates for realtime-balanced, emotional-opening, clarity-safe, and expressive-quality tests
  - added bundled emotional delivery gestures instead of one-effect-at-a-time voice tweaks
  - added protected-text locks for campaign questions, disclosures, claim/legal/medical boundaries, appointment confirmations, handoff, and hang-up lines
  - added a runner and validator that create a deterministic design packet without API keys, provider calls, generated audio, private audio upload, or voice cloning
  - documented official ElevenLabs sources as provider documentation inspiration, not copied code
- Data used:
  - `VOICE-018` sales-tuned delivery metadata
  - `VOICE-019` live listening feedback
  - official ElevenLabs voice, Voice Design, TTS best-practice, settings, privacy, and commercial-use docs
  - project-owner clarification that private call-center audio may only inform local abstract tuning notes for future voice adjustment
- Output created:
  - `research/experiments/cases/voice-020-elevenlabs-voice-design.json`
  - `research/experiments/generated/VOICE-020-elevenlabs-voice-design.json`
  - `research/experiments/generated/VOICE-020-elevenlabs-voice-design-report.md`
  - `docs/product/VOICE_020_ELEVENLABS_VOICE_DESIGN.md`
  - `research/experiments/VOICE-020-elevenlabs-voice-design.md`
  - `scripts/run_voice_020_elevenlabs_voice_design.py`
  - `scripts/validate_voice_020_elevenlabs_voice_design.py`
- Dry-run result:
  - voice design profiles: 2
  - languages: English and German
  - settings candidates: 4
  - emotional delivery bundles: 5
  - provider calls made: false
  - API key required: false
  - private audio uploaded: false
  - voice cloning used: false
  - generated audio created: false
- What was learned:
  - the next useful voice work is a deliberate ElevenLabs voice-candidate test, not random provider experimentation
  - voice quality needs both provider voice selection and runtime delivery rules
  - private call-center audio can be useful later as local pattern evidence, but not as provider training/upload material
- Why it matters for the thesis:
  - it records how qualitative listening feedback becomes a reproducible experimental design
  - it separates product speech content, protected campaign text, provider voice design, and privacy boundaries
  - it gives future thesis writing a clean example of iterative engineering after an audio-quality failure mode
- Open questions:
  - whether ElevenLabs Voice Design or Voice Library voices produce better German and English sales-agent quality
  - whether the `emotional-opening` settings candidate reduces the immediate robot-detection reaction without sounding theatrical
  - whether provider settings alone are enough, or whether response segmentation must control protected and freeform text separately

### 2026-05-04 - VOICE-020 Voice Design UI and local voice-ID refinement

- Objective: adapt `VOICE-020` to the actual ElevenLabs Voice Design page and reduce repeated manual voice-ID setup
- Action taken:
  - added Voice Design UI candidates for `loudness` and `guidance_scale`
  - updated English and German prompts to explicitly request clean full-band quality and avoid telephone-filtered, muffled, distant, compressed, or low-bandwidth sound
  - increased the runtime speed candidates because current Voice Design previews sounded too slow for sales usefulness
  - added longer synthetic preview text inspired by the ElevenLabs generated example, while keeping it product-owned and campaign-safe
  - added ignored local config support at `config/local/voice_ids.json`
  - wired local voice-ID lookup into ElevenLabs live paths used by `VOICE-013`, `VOICE-017`/`VOICE-019`, and `RESP-003`
  - kept environment variables as the override path and kept API keys environment-only
- Data used:
  - project-owner screenshot of ElevenLabs Voice Design showing `loudness`, `guidance_scale`, and generated preview text behavior
  - project-owner feedback that generated Voice Design voices sounded robotic, phone-like/muffled, and too slow
- Output created:
  - `config/local/.gitignore`
  - `config/local/voice_ids.example.json`
  - `scripts/local_voice_config.py`
  - `scripts/validate_local_voice_config.py`
  - updates to `VOICE-020` config, docs, generated report, setup checks, and command map
- What was learned:
  - ElevenLabs Voice Design quality must be guided at voice-creation time, not only at runtime TTS time
  - the project needs separate controls for voice-generation UI settings and runtime TTS settings
  - voice IDs are lower sensitivity than API keys, but still belong in local ignored config because client/provider choices may change
- Why it matters for the thesis:
  - it documents a practical provider-interface adaptation after observing real tool behavior
  - it records another voice-quality failure mode: telephone-like/muffled generation and overly slow speech
  - it preserves reproducibility without committing account-specific voice IDs
- Open questions:
  - which guidance-scale range produces the least robotic result without drifting away from the sales-agent persona
  - whether full-band prompt wording is enough to remove the phone-like effect
  - whether ElevenLabs Voice Library voices outperform Voice Design voices for German sales delivery

### 2026-05-04 - VOICE-020 Voice Remixing prompts

- Objective: use ElevenLabs Voice Remixing as a provider-side naturalization step before building more local pacing logic
- Action taken:
  - added official ElevenLabs Voice Remixing as a `VOICE-020` source
  - added extensive English and German remix prompts for created/owned sales voices
  - targeted pacing, emotion, pitch, audio quality, timbre, and bundled conversational microtexture
  - included custom remix scripts for English and German opening/objection-handling samples
  - documented prompt strength guidance: start with `Medium`, then try `High` if changes are too subtle
- Data used:
  - project-owner discovery that ElevenLabs Voice Remixing can transform existing voices with prompt categories such as pacing, emotion, pitch, and audio quality
  - official ElevenLabs Voice Remixing docs
  - previous owner feedback about roboticness, stale pacing, insufficient fillers, insufficient contractions/connectors, and unbundled voice effects
- Output created:
  - updated `research/experiments/cases/voice-020-elevenlabs-voice-design.json`
  - updated `research/experiments/generated/VOICE-020-elevenlabs-voice-design.json`
  - updated `research/experiments/generated/VOICE-020-elevenlabs-voice-design-report.md`
  - updated `docs/product/VOICE_020_ELEVENLABS_VOICE_DESIGN.md`
- What was learned:
  - Remixing can reduce local workload by improving the base voice before runtime synthesis
  - Remixing does not replace runtime delivery control because protected text, campaign-specific pacing, and turn-by-turn variation still need product-side rules
  - bundled speech effects should be requested at the provider level as natural voice behavior, not as isolated pause/filler/pitch toggles
- Why it matters for the thesis:
  - it shows the prototype adapting to provider capabilities instead of overbuilding local logic too early
  - it creates a cleaner separation between base voice quality and runtime sales-agent behavior
  - it records a practical method for iterating voice naturalness with human listening feedback
- Open questions:
  - whether Medium or High remix strength best balances voice identity and naturalness
  - whether German remixing improves native rhythm enough for the first real-client context
  - which naturalness issues remain after remixing and therefore must be handled in runtime delivery

### 2026-05-04 - PRIVATE-CALL-LEARNING-001 local-only private call learning scaffold

- Objective: prepare for future private call-center audio without letting raw recordings, raw transcripts, customer identifiers, or sensitive details drift into Git, providers, RAG, generated reports, or fine-tuning datasets
- Action taken:
  - added a machine-readable private-call learning pipeline case
  - added a checker and validator that verify the scaffold without reading private file contents
  - added an initializer for ignored local `data/private/` subfolders
  - documented pattern-mining-first learning, redaction, human review, safe export, and retention/deletion boundaries
  - updated setup, drift, command, roadmap, and data policy references so future sessions treat this as an active project boundary
- Data used:
  - no private recordings
  - no private transcripts
  - project-owner requirements that future call-center audio stays local, raw audio is not uploaded, identifiers are ignored as learning signal, and both successful and unsuccessful sales calls can teach useful patterns
- Output created:
  - `research/experiments/cases/private-call-learning-001.json`
  - `research/experiments/generated/PRIVATE-CALL-LEARNING-001.json`
  - `research/experiments/generated/PRIVATE-CALL-LEARNING-001-report.md`
  - `docs/data/PRIVATE_CALL_LEARNING_PIPELINE.md`
  - `research/experiments/PRIVATE-CALL-LEARNING-001.md`
  - `scripts/check_private_call_learning_pipeline.py`
  - `scripts/init_private_call_learning_workspace.py`
  - `scripts/validate_private_call_learning_pipeline.py`
- Dry-run result:
  - network calls made: false
  - raw private content read: false
  - secret values logged: false
  - raw audio provider upload allowed: false
  - raw audio Git tracking allowed: false
  - customer identifier learning allowed: false
  - fine-tuning enabled by default: false
- What was learned:
  - private call-center data should first become human-reviewed sales-pattern notes, not immediate fine-tuning material
  - successful calls can teach target behavior, while failed calls should become avoid-patterns and guardrails
  - raw transcripts inherit the same privacy risk as raw audio and must not become normal generated artifacts
- Why it matters for the thesis:
  - it creates a defensible private-data methodology before data arrives
  - it separates reproducible public experiments from restricted local product-learning evidence
  - it records the privacy and retention constraints that will shape later RAG or fine-tuning claims
- Open questions:
  - which local ASR and speaker-segmentation approach is accurate enough for German call-center audio
  - what redaction quality threshold is required before pattern notes can leave `data/private/`
  - whether sales-expert review should label success/failure patterns before RAG is built

### 2026-05-04 - SPEECH-STYLE-001 English/German speech realism references

- Objective: preserve internet-researched speech-pattern references for thesis writing and future `VOICE-023` design
- Action taken:
  - created a thesis reference note for spontaneous speech, disfluency, filler particles, pauses, breath behavior, and audible warmth
  - updated the thesis outline and writing guide so the reference note is discoverable during thesis drafting
  - updated dataset readiness notes to treat Spoken BNC2014 and DGD/FOLK as candidate speech-realism references, not immediate phase-1 datasets
  - updated the roadmap so `VOICE-023` uses language-aware speech-realism references while keeping protected text exact
- Sources recorded:
  - Clark and Fox Tree (2002) on English `uh` and `um` as speech-planning delay signals
  - Spoken BNC2014 for contemporary spoken English conversation reference
  - DGD/FOLK for spontaneous German interaction reference
  - Muhlack, Trouvain, and Jessen (2023) on German filler particles
  - Belz (2023) on filler-particle terminology and phonetic classification
  - GAT 2 as a German conversation-analysis transcription reference for pauses, breath, lengthening, and laughter notation
  - Trouvain, Werner, and Moebius (2020) plus Werner, Trouvain, and Moebius (2022) on breath and pause variability
  - Barthel and Quene (2015) on acoustic cues of smiled speech
- What was learned:
  - fillers should be modeled as timing and planning signals, not as random noise
  - English and German need different filler inventories and discourse-marker tendencies
  - breathing and pause variability are part of perceived naturalness
  - audible warmth can be modeled cautiously, but it must not become theatrical or manipulative
  - language mechanics must remain separate from cultural stereotypes and campaign persona
- Why it matters for the thesis:
  - it gives the voice-naturalness design a research trail instead of relying only on subjective listening impressions
  - it supports a future methodology section explaining why fillers, pauses, and prosody are controlled rather than random
  - it creates sources for a related-work discussion on spontaneous speech and speech realism
- Open questions:
  - whether to validate the English profile against Spoken BNC2014 before implementation or after the first `VOICE-023` prototype
  - whether DGD/FOLK access terms allow enough inspection for German profile refinement
  - how to evaluate smile/warmth cues without making the sales agent sound overexcited

### 2026-05-04 - REF-001 thesis reference registry and expanded writing map

- Objective: preserve the broader source trail from earlier project work and make the thesis outline/writing guide reflect the actual project scope
- Action taken:
  - added `THESIS_REFERENCE_REGISTRY.md` as a central source map
  - expanded `THESIS_OUTLINE.md` from a short skeleton into a chapter-by-chapter evidence map
  - expanded `THESIS_WRITING_GUIDE.md` with writing workflow, source rules, evidence rules, and limitations to preserve
  - moved `VOICE-023` engineering implications out of the speech-reference file into `docs/product/VOICE_023_SPEECH_REALISM_LAYER.md`
  - added source candidates for IEMOCAP, MELD, and Persuasion for Good to the dataset manifest
  - recovered sales-objection source URLs for Apollo, Salesgenie, Proposify, and B2B Vic
- Sources organized:
  - public datasets: IEMOCAP, MELD, Persuasion for Good
  - speech realism: English/German disfluency, pause, breath, and smiled-speech references
  - privacy/data governance: European Commission and EDPB GDPR references
  - voice providers: Cartesia, ElevenLabs, OpenAI, Azure, Google Cloud, AWS Polly, Deepgram, and Piper
  - sales-objection product sources: Apollo, Salesgenie, Proposify, B2B Vic
  - open-source/process inspirations: project-attributed GitHub repositories already tracked in `third-party-inspirations.md`
- What was learned:
  - the thesis needs a source registry separate from individual product docs
  - not every source has the same academic weight
  - provider docs should support engineering choices, not quality claims
  - sales-practice articles can ground product categories, but should not be treated as peer-reviewed evidence
- Why it matters for the thesis:
  - it prevents citations and source provenance from being lost in chat history
  - it makes the final writing process easier by mapping each chapter to evidence files
  - it keeps product inspiration, academic evidence, provider documentation, and private-data rules separate
- Open questions:
  - final citation style required by the university
  - exact local archive provenance and license terms for downloaded datasets
  - final legal sources for German outbound calling, insurance sales, and call recording
