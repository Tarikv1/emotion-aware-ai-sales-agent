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

### 2026-05-15 - PROD-053E English runtime wording patch

- Objective: promote Tarik-approved English single-turn wording into the deterministic realtime runtime without bundling unresolved behavior decisions.
- Action taken: added a failing `PROD-053E` validator first, promoted accepted and safe English wording in `runtime/core/realtime_turns.py`, added a checkpoint runner, product doc, generated promoted/skipped evidence files, and updated the command/checkpoint navigation.
- Data used: `research/experiments/generated/PROD-053D-english-review-import/accepted_as_written_items.json` and `runtime_patch_candidates.json`. No provider calls, LLM judging, private data reads, retrieval, voice playback, German phrase promotion, or German naturalness claims were used.
- Output created: `scripts/prod_053e_english_runtime_wording_patch.py`, `scripts/run_prod_053e_english_runtime_wording_patch.py`, `scripts/validate_prod_053e_english_runtime_wording_patch.py`, `docs/product/PROD_053E_ENGLISH_RUNTIME_WORDING_PATCH.md`, and generated artifacts under `research/experiments/generated/PROD-053E-english-runtime-wording-patch/`.
- What was learned: `26` English responses are safe to promote now: `15` accepted as-written, `10` wording-only rework candidates, and `1` approved-with-edit-note item. Voicemail action-only behavior, coverage knowledge-policy behavior, and context-sensitive autonomy wording remain separate runtime/design questions.
- Why it matters for the thesis: this converts human review evidence into a bounded runtime change while preserving the distinction between phrase-level quality improvements and behavioral policy changes.
- Open questions: whether the promoted single-turn wording stays natural after the customer answers, which is the purpose of the next `PROD-054` stress review.

### 2026-05-15 - PROD-053D English review import

- Objective: import Tarik's PROD-053C English review export and distinguish exact approvals from rework notes before changing runtime text.
- Action taken: added a failing PROD-053D validator first, then added an importer, runner, product doc, imported review summary, accepted-as-written list, approved-with-edit-note list, needs-rework list, owner feedback themes, runtime patch candidates, report, and result artifact.
- Data used: `research/experiments/imports/PROD-053C-english-spoken-response-expansion-review/prod_053c_review_export.json.json` and `research/experiments/generated/PROD-053C-english-spoken-response-expansion-review/english_spoken_response_review_items.json`. No provider calls, LLM judging, private data reads, retrieval, voice playback, runtime behavior changes, response text changes, or German phrase promotion were used.
- Output created: `scripts/prod_053d_english_review_import.py`, `scripts/run_prod_053d_english_review_import.py`, `scripts/validate_prod_053d_english_review_import.py`, `docs/product/PROD_053D_ENGLISH_REVIEW_IMPORT.md`, and generated artifacts under `research/experiments/generated/PROD-053D-english-review-import/`.
- What was learned: the review contains `16` approved statuses and `13` needs-rework statuses, but only `15` items are approved as-written because `prod-053c-existing-provider-gap` has a material edit note. The owner feedback themes are contractions over formal expansions, less formal acknowledgements, voicemail action-only behavior, short transfer responses, modal precision, coverage knowledge vs advice, callback brevity, and useful small mirroring.
- Why it matters for the thesis: this preserves human review as structured evidence instead of manually interpreting it from memory, and it prevents unreviewed runtime changes from being hidden inside a review import.
- Open questions: which runtime patch candidates should be applied first, and whether voicemail, coverage, and context-sensitive autonomy should be separate checkpoints rather than part of a wording-only patch.

### 2026-05-15 - PROD-053C English spoken-response expansion review

- Objective: create a broader English exact phrase review packet without making Tarik re-review responses already carried forward by PROD-053B.
- Action taken: added a failing PROD-053C validator first, then added a generator, runner, product doc, scope-decision artifact, policy-application audit, review item JSON, report, and local HTML review page with `localStorage`, `Export JSON`, and `Import JSON` controls.
- Data used: `research/experiments/generated/PROD-053B-compact-english-psychology-layer-review/result.json`, `research/experiments/generated/PROD-053B-compact-english-psychology-layer-review/compact_english_policy_rules.json`, `research/experiments/generated/PROD-053B-compact-english-psychology-layer-review/current_english_case_policy_audit.json`, and deterministic probes against `runtime/core/realtime_turns.py`. No provider calls, LLM judging, private data reads, retrieval, voice playback, runtime behavior changes, response text changes, or German phrase promotion were used.
- Output created: `scripts/prod_053c_english_spoken_response_expansion_review.py`, `scripts/run_prod_053c_english_spoken_response_expansion_review.py`, `scripts/validate_prod_053c_english_spoken_response_expansion_review.py`, `docs/product/PROD_053C_ENGLISH_SPOKEN_RESPONSE_EXPANSION_REVIEW.md`, and generated artifacts under `research/experiments/generated/PROD-053C-english-spoken-response-expansion-review/`.
- What was learned: the reachable English deterministic runtime surface is larger than the previous review lane: PROD-053C produced `29` review items, made of `2` PROD-053B-flagged rewrites and `27` previously unreviewed reachable English response types. It excluded `2` already-approved carry-forward cases and deferred `provider-comparison` because the current classifier has no distinct reachable English branch for it.
- Why it matters for the thesis: this turns the compact psychology rules into a concrete human-review surface without treating deterministic checks as proof of naturalness or importing unreviewed phrases into runtime.
- Open questions: which proposed English responses Tarik accepts, which need wording changes, and whether accepted single-turn wording should be applied in a narrow runtime update before `PROD-054` multi-turn naturalness stress testing.

### 2026-05-15 - PROD-053B compact English psychology layer review

- Objective: compress the PROD-053A English sales psychology research into a reviewed, deterministic, English-only rule layer before expanding the English spoken-response surface.
- Action taken: added a failing PROD-053B validator first, then added a generator, runner, product doc, compact policy rules, candidate-rule review, current English case audit, rejected/deferred tactic review, report, and local HTML review page.
- Data used: `research/experiments/generated/PROD-053A-english-sales-psychology-deep-dive/compact_candidate_rules.json`, `research/experiments/generated/PROD-053A-english-sales-psychology-deep-dive/rejected_or_deferred_tactics.json`, and `research/experiments/generated/PROD-052-language-lane-review-separation/english_spoken_review_items.json`. No provider calls, LLM judging, private data reads, retrieval, voice playback, or German phrase promotion were used.
- Output created: `scripts/prod_053b_compact_english_psychology_layer_review.py`, `scripts/run_prod_053b_compact_english_psychology_layer_review.py`, `scripts/validate_prod_053b_compact_english_psychology_layer_review.py`, `docs/product/PROD_053B_COMPACT_ENGLISH_PSYCHOLOGY_LAYER_REVIEW.md`, and generated artifacts under `research/experiments/generated/PROD-053B-compact-english-psychology-layer-review/`.
- What was learned: the `8` candidate rules are useful enough to carry into PROD-053C, but `3` need constraints so mirroring does not become parroting, friction diagnosis does not become broad interrogation, and autonomy language does not become accidental terminal wording. The current stakeholder and partner English responses should be reopened in PROD-053C because they echo the customer category and should include clearer no-commitment relief.
- Why it matters for the thesis: this shows the research-to-runtime discipline: deeper sales psychology is not copied into a large planner, but compressed into deterministic, reviewable rules before any runtime response text changes.
- Open questions: which broader English response types should enter PROD-053C, and whether the rewrite packet should include only flagged already-reviewed cases plus previously unreviewed English surface area.

### 2026-05-15 - Thesis path reference audit after runtime move

- Objective: make sure thesis documents point to current project paths after runtime-affecting files moved under `runtime/`.
- Action taken: scanned `14` thesis Markdown files for path-like references, patched stale moved paths in `METHODOLOGY_LOG.md`, updated command guidance for ignored local voice config, and confirmed intentionally ignored `runtime/config/local/voice_ids.json` is covered by `runtime/config/local/.gitignore`.
- Data used: local thesis Markdown files, `runtime/` folder inventory, and `git check-ignore -v runtime/config/local/voice_ids.json`. No provider calls, LLM judging, private data reads, retrieval, or runtime behavior changes were used.
- Output created: updated thesis references for `runtime/persistence/sqlite_schema.sql`, `runtime/persistence/SQLITE_PROTOTYPE.md`, `runtime/prompts/product-qualification-agent.txt`, `runtime/providers/VOICE_PROVIDER_RUN_BOUNDARY.md`, `runtime/providers/VOICE_GENERATED_AUDIO_ASSET_LOG.md`, `runtime/config/local/.gitignore`, and `runtime/config/local/voice_ids.example.json`.
- What was learned: tracked thesis path references were mostly current; the remaining absent references were intentionally ignored local config files rather than moved tracked files.
- Why it matters for the thesis: thesis writing can now point to the current runtime folder structure instead of stale pre-move locations.
- Open questions: whether a permanent thesis path-reference validator is worth adding later, or whether the existing reference/update gates plus targeted path audits are enough.

### 2026-05-15 - Runtime folder boundary map

- Objective: reduce project-folder confusion before adding more English runtime behavior rules.
- Action taken: added a top-level `runtime/` folder, moved runtime-affecting source modules, runtime assets, and canonical runtime-facing Markdown into it, kept thin `scripts/*` compatibility wrappers plus short product-doc stubs for historical paths, and tightened the manifest validator so runtime sources/docs must physically live under `runtime/`.
- Data used: local project file inventory, command-map references, existing project navigation guidance, and static impact scan output. No provider calls, LLM judging, private data reads, or runtime execution were used.
- Output created: `runtime/README.md`, `runtime/runtime_manifest.json`, runtime subfolders for architecture, core behavior, entrypoints, contracts, policy, retrieval, speech, voice, providers, campaigns, prompts, config, and persistence; canonical runtime Markdown under `runtime/architecture/`, `runtime/entrypoints/`, `runtime/policy/`, `runtime/providers/`, and `runtime/persistence/`; `scripts/validate_runtime_manifest.py`; compatibility wrappers under `scripts/`; and navigation/setup updates in `README.md`, `docs/PROJECT_NAVIGATION.md`, `scripts/README.md`, `docs/product/COMMANDS.md`, `scripts/check_setup.py`, and `scripts/check_project_drift.py`.
- What was learned: the current runtime surface is real and can be separated without changing response text when legacy command compatibility is preserved. The manifest now tracks `45` runtime entries and `9` non-runtime defaults. Generated artifacts, checkpoint runners, validators, `.tmp`, and private data should remain outside the runtime boundary unless a future checkpoint promotes a specific file. Windows denied direct move/unlink operations, so the safe migration path was copy-to-runtime, hash verification, wrapper/stub replacement, and validated cleanup of old runtime asset copies.
- Why it matters for the thesis: the project now distinguishes runtime-affecting implementation from research evidence and generated review artifacts, which reduces the chance of accidentally cleaning up or editing the wrong files.
- Open questions: which legacy wrappers can eventually be removed after command docs, validators, and historical review workflows no longer depend on exact `scripts/*` paths.

### 2026-05-15 - PROD-053A English sales psychology deep dive

- Objective: research the useful sales psychology and adjacent human psychology needed for a compact English live-call psychology layer.
- Action taken: added a PROD-053A generator, runner, validator, product doc, source register, topic findings, compact candidate rules, rejected/deferred tactic list, result summary, and report.
- Data used: public source-backed research plus existing project direction from RAG-020/RAG-021. The packet uses paraphrased project-owned findings only and stores no source excerpts, copied scripts, private customer data, provider outputs, or LLM judgments.
- Output created: `scripts/prod_053a_english_sales_psychology_deep_dive.py`, `scripts/run_prod_053a_english_sales_psychology_deep_dive.py`, `scripts/validate_prod_053a_english_sales_psychology_deep_dive.py`, `docs/product/PROD_053A_ENGLISH_SALES_PSYCHOLOGY_DEEP_DIVE.md`, and generated artifacts under `research/experiments/generated/PROD-053A-english-sales-psychology-deep-dive/`.
- What was learned: the useful layer should emphasize adaptive selling, listening, buyer confidence, autonomy, friction diagnosis, trust repair, conversation repair, spoken brevity, and ethical insight. It should reject false scarcity, hidden emotion diagnosis, commitment traps, excessive customer-category echoing, and large live psychology planners.
- Why it matters for the thesis: this records a disciplined research-to-compression step, showing how deeper psychology research can be transformed into a small reviewed runtime rule layer without adding live latency or manipulative behavior.
- Open questions: which compact candidate rules should be accepted into PROD-053B, and which already-reviewed English phrases should be reopened by the new rules.

### 2026-05-15 - English call-control phrase shortening

- Objective: incorporate owner feedback that the English send-info, manager-review, and spouse-review responses should sound shorter and more natural for a live call.
- Action taken: updated the English `written-info-request`, `stakeholder-review`, and `partner-review` low-pressure responses; updated the frozen PROD-050 proposal text; adjusted deterministic naturalness markers so shorter owner-approved low-pressure wording is accepted without requiring the old `If useful...` sentence shape; regenerated affected PROD-050 through PROD-052 artifacts.
- Data used: Tarik's English wording feedback and existing PROD-050/051/052 generated evidence. No German wording acceptance, provider call, LLM judging, private data read, retrieval enablement, voice playback, public demo polish, payment collection, contract signing, or production runtime promotion was used.
- Output created: revised generated artifacts under `research/experiments/generated/PROD-050-safe-call-control-softening-regression/`, `research/experiments/generated/PROD-051-safe-call-control-runtime-update/`, and `research/experiments/generated/PROD-052-language-lane-review-separation/`.
- What was learned: deterministic naturalness checks need to validate the conversational function of a phrase, not force one old sentence pattern. The send-info phrase still needs to name the item being sent, so the accepted shape became `tailor the summary... then send it over`.
- Why it matters for the thesis: this is a concrete human-in-the-loop correction where project-owner language intuition improves the spoken-call surface after automated checks passed.
- Open questions: how many additional English response types should enter the broader PROD-053 review packet before multi-turn testing.

### 2026-05-15 - PROD-052 language-lane review separation

- Objective: separate exact spoken-response acceptance by language so English can be reviewed now while German wording remains pending native/source-backed evidence.
- Action taken: added a PROD-052 generator, runner, validator, product doc, separated English review items, German pending-review items, reusable multilingual policy rules, legacy mixed review-surface inventory, review HTML, report, and result summary.
- Data used: PROD-051 runtime and naturalness artifacts only. No provider call, LLM judging, private data read, retrieval enablement, voice playback, public demo polish, payment collection, contract signing, or production runtime promotion was used.
- Output created: `scripts/prod_052_language_lane_review_separation.py`, `scripts/run_prod_052_language_lane_review_separation.py`, `scripts/validate_prod_052_language_lane_review_separation.py`, `docs/product/PROD_052_LANGUAGE_LANE_REVIEW_SEPARATION.md`, and generated artifacts under `research/experiments/generated/PROD-052-language-lane-review-separation/`.
- What was learned: deterministic naturalness gates are useful for multilingual policy constraints, but exact phrase naturalness needs language-specific human or source-backed review. English can move faster because Tarik can judge it directly; German should stay separated and unaccepted until a stronger review source exists.
- Why it matters for the thesis: this records a concrete limitation in AI-assisted language evaluation instead of overclaiming bilingual naturalness from automated checks.
- Open questions: which older mixed review surfaces should be reopened as separated English/German packets, and whether the next immediate product step should stress-test only English multi-turn naturalness.

### 2026-05-14 - PROD-051 safe call-control runtime update with naturalness audit

- Objective: apply the selected call-control softening to the live deterministic runtime only if the response text also becomes natural enough for a spoken sales call.
- Action taken: added a PROD-051 generator, runner, validator, product doc, runtime update evidence, naturalness audit, before/after naturalness comparison, protected-boundary probes, review HTML, report, and result summary. The live runtime now uses `answer-and-continue` for selected non-refusal cases and maps that to `bridge-then-continue`.
- Data used: frozen PROD-050 cases and baseline/proposed evidence, existing PROD-049 through PROD-045 result packets, and deterministic live runtime probes. No raw transcript text, provider call, LLM call, private data read, retrieval enablement, voice playback, public demo polish, payment collection, contract signing, or production runtime promotion was used.
- Output created: `scripts/prod_051_safe_call_control_runtime_update.py`, `scripts/run_prod_051_safe_call_control_runtime_update.py`, `scripts/validate_prod_051_safe_call_control_runtime_update.py`, `docs/product/PROD_051_SAFE_CALL_CONTROL_RUNTIME_UPDATE.md`, and generated artifacts under `research/experiments/generated/PROD-051-safe-call-control-runtime-update/`.
- What was learned: the selected `22` non-refusal cases can be softened in live runtime only when call-control and response text move together. A deterministic naturalness rubric caught the earlier shallow flag-only implementation risk by requiring direct answer, optional continuation, no terminal close, no internal jargon, spoken sentence shape, customer-fit, language-fit, and no pressure/payment/contract/unsupported claim.
- Why it matters for the thesis: the project now has a repeatable offline method for validating conversation naturalness beyond reviewing its own generated artifacts or relying on green regression counts.
- Open questions: whether the answer-and-continue path remains natural in the second turn after the customer accepts, ignores, challenges, or refuses the optional continuation.

### 2026-05-14 - PROD-050 safe call-control softening regression

- Objective: prove the selected safe end-call softening candidates before editing the live deterministic runtime.
- Action taken: added a PROD-050 proposed-softening generator, runner, validator, product doc, regression cases, regression results, protected-boundary probes, proposed runtime change summary, review HTML, report, and result summary. Runtime behavior and call-control behavior were not changed.
- Data used: PROD-049 candidate matrix, PROD-045 English regression cases, PROD-046D German source-informed results, and passing PROD-049/048C/047/046/045 result packets. No raw transcript text, provider call, LLM call, private data read, retrieval enablement, voice playback, public demo polish, payment collection, contract signing, or production runtime promotion was used.
- Output created: `scripts/prod_050_safe_call_control_softening_regression.py`, `scripts/run_prod_050_safe_call_control_softening_regression.py`, `scripts/validate_prod_050_safe_call_control_softening_regression.py`, `docs/product/PROD_050_SAFE_CALL_CONTROL_SOFTENING_REGRESSION.md`, and generated artifacts under `research/experiments/generated/PROD-050-safe-call-control-softening-regression/`.
- What was learned: all `22` selected non-refusal cases can be proposed as `bridge-then-continue` only when the proposal also replaces terminal safe-close wording with low-pressure optional continuation text while preserving approved answer content. The tightened evidence records no pressure, unsupported-claim, payment-collection, or contract-signing violations. Protected boundaries stayed unchanged across `9` probes.
- Why it matters for the thesis: the project now has an auditable method for improving conversational continuity without conflating proposed call-control quality evidence with live runtime promotion.
- Open questions: whether `PROD-051` should apply both the call-control mapping and the response-text softening to the live deterministic runtime, update the bridge-then-continue definition for non-lookup answer-then-continue cases, and migrate affected historical expectations while keeping the older German review chain clear about what changed later.

### 2026-05-14 - PROD-049 safe end-call bridge-continue review

- Objective: move forward while the native German follow-up review is blocked, using existing call-control evidence to decide where safe end-call behavior should be tested as bridge-then-continue.
- Action taken: added a PROD-049 review generator, runner, validator, product doc, candidate matrix, protected-boundary probes, review packet, review HTML, report, and result summary. Runtime behavior and call-control behavior were not changed.
- Data used: existing PROD-046 call-control findings plus passing PROD-048C, PROD-047, PROD-046, and PROD-045 result packets. No raw transcript text, provider call, LLM call, private data read, retrieval enablement, voice playback, public demo polish, payment collection, contract signing, or production runtime promotion was used.
- Output created: `scripts/prod_049_safe_end_call_bridge_continue_review.py`, `scripts/run_prod_049_safe_end_call_bridge_continue_review.py`, `scripts/validate_prod_049_safe_end_call_bridge_continue_review.py`, `docs/product/PROD_049_SAFE_END_CALL_BRIDGE_CONTINUE_REVIEW.md`, and generated artifacts under `research/experiments/generated/PROD-049-safe-end-call-bridge-continue-review/`.
- What was learned: not all abrupt safe end-calls should be softened. `price-first-direct`, `written-info-request`, `stakeholder-review`, and `partner-review` are suitable future bridge-then-continue candidates, while email-only, payment/scam safety, sale-ready, callback, support, cancellation, do-not-call, and human-request boundaries should remain terminal or escalated.
- Why it matters for the thesis: this separates safe regression success from spoken-call quality and creates an auditable path for improving conversational continuity without weakening consent, safety, or escalation boundaries.
- Open questions: whether `PROD-050` can safely apply bridge-then-continue to the selected candidate groups without introducing pressure, looping questions, unsupported claims, or premature voice/demo promotion.

### 2026-05-12 - PROD-048C German wording feedback patch

- Objective: apply only the reviewed price-first German wording correction from PROD-048B and prepare a corrected grouped follow-up review packet.
- Action taken: changed the German plain price-first runtime wording to remove the payment/contract sentence, added a PROD-048C generator, runner, validator, product doc, before/after evidence, safety-boundary preservation evidence, corrected German follow-up HTML, follow-up packet JSON, export schema, CSV, and German README. Customer-move classification, runtime policy, and call-control behavior were not changed.
- Data used: PROD-048B imported reviewer feedback from Diro, the PROD-048A grouped packet, and deterministic runtime probes for price, payment safety, scam safety, and sale-ready contexts. No raw transcript text, German sales-call scripts, provider call, LLM call, private data read, retrieval enablement, voice playback, public demo polish, payment collection, contract signing, or production runtime promotion was used.
- Output created: `scripts/prod_048c_german_wording_feedback_patch.py`, `scripts/run_prod_048c_german_wording_feedback_patch.py`, `scripts/validate_prod_048c_german_wording_feedback_patch.py`, `docs/product/PROD_048C_GERMAN_WORDING_FEEDBACK_PATCH.md`, and generated artifacts under `research/experiments/generated/PROD-048C-german-wording-feedback-patch/`.
- What was learned: a native reviewer can accept the price answer as phone-acceptable while still flagging a subtle sales-pressure effect, so the import-to-patch workflow must separate acceptance, small-change requests, and safety/impact flags.
- Why it matters for the thesis: German wording quality is now improved through a traceable human-feedback loop without overclaiming full native approval or legal compliance.
- Open questions: whether the reviewer accepts the shortened price-first answer and whether the remaining unreviewed grouped answers need additional wording patches.

### 2026-05-12 - PROD-048B native German review import

- Objective: import returned native German reviewer feedback as partial evidence without treating blank rows as rejection or approval.
- Action taken: added a deterministic reviewer JSON importer, runner, validator, product doc, generated summary, reviewed/unreviewed item splits, revision candidates, follow-up review plan, and import HTML. Runtime policy and call-control behavior were not changed.
- Data used: reviewer-exported JSON from `research/experiments/imports/PROD-048B-native-german-review-import/deutsche-telefonantworten-bewertung-1.json`, the grouped PROD-048A packet, and the earlier individual-row PROD-048A packet for traceability. No raw transcript text, German sales-call scripts, provider call, LLM call, private data read, retrieval enablement, voice playback, public demo polish, payment collection, contract signing, or production runtime promotion was used.
- Output created: `scripts/prod_048b_native_german_review_import.py`, `scripts/run_prod_048b_native_german_review_import.py`, `scripts/validate_prod_048b_native_german_review_import.py`, `docs/product/PROD_048B_NATIVE_GERMAN_REVIEW_IMPORT.md`, and generated artifacts under `research/experiments/generated/PROD-048B-native-german-review-import/`.
- What was learned: the returned export had a broken checked-count summary and used `99` individual rows, so importer logic must recompute reviewed rows from filled fields and preserve the import-shape concern.
- Why it matters for the thesis: native-language feedback is now evidence-imported as partial, auditable review data instead of being overclaimed as full German approval.
- Open questions: whether the price-first wording revision should be applied in a targeted patch checkpoint, and whether the reviewer can continue with the grouped HTML for the remaining unreviewed answer groups.

### 2026-05-12 - PROD-048A German review HTML and brevity packet

- Objective: respond to native-reviewer feedback that the previous German review packet was too repetitive and that many answers sounded too long, forced, complete, or AI-like.
- Action taken: added a grouped German review packet generator, runner, validator, product doc, grouped German-only HTML, German README, export schema, review table, brevity before/after evidence, and duplicate-answer group evidence. Runtime policy and call-control behavior were not changed.
- Data used: existing PROD-046 German response-quality findings, PROD-046D German source-informed results, PROD-046 call-control findings, and the valid German PROD-047 campaign profile. No raw transcript text, German sales-call scripts, provider call, LLM call, private data read, retrieval enablement, voice playback, public demo polish, payment collection, contract signing, or production runtime promotion was used.
- Output created: `scripts/prod_048a_german_review_html_and_brevity_packet.py`, `scripts/run_prod_048a_german_review_html_and_brevity_packet.py`, `scripts/validate_prod_048a_german_review_html_and_brevity_packet.py`, `docs/product/PROD_048A_GERMAN_REVIEW_HTML_AND_BREVITY_PACKET.md`, and generated artifacts under `research/experiments/generated/PROD-048A-german-review-html-and-brevity-packet/`.
- What was learned: the review surface should not ask a human reviewer to rate the same answer repeatedly; grouping repeated German answers keeps traceability while reducing review fatigue.
- Why it matters for the thesis: the German review method now separates case-level traceability from human-review usability, and records brevity changes without claiming native German approval.
- Open questions: whether the native reviewer accepts the shorter grouped answers, requests small wording edits, or finds that some grouped customer utterances need distinct responses.

### 2026-05-12 - PROD-048A native German review HTML packet

- Objective: prepare a German-only, non-technical, browser-openable review packet so a native German reviewer can judge wording quality without knowing the technical project.
- Action taken: added a PROD-048A generator, runner, validator, product doc, German reviewer README, self-contained HTML review interface, packet JSON, export schema, and review table. Runtime behavior was not changed.
- Data used: existing PROD-046 German response-quality findings, PROD-046D German source-informed results for customer utterances, PROD-046 call-control findings, and the valid German PROD-047 campaign-profile fixture. No raw transcript text, German sales-call scripts, provider call, LLM call, private data read, retrieval enablement, voice playback, public demo polish, payment collection, contract signing, or production runtime promotion was used.
- Output created: `scripts/prod_048a_native_german_review_html_packet.py`, `scripts/run_prod_048a_native_german_review_html_packet.py`, `scripts/validate_prod_048a_native_german_review_html_packet.py`, `docs/product/PROD_048A_NATIVE_GERMAN_REVIEW_HTML_PACKET.md`, and generated artifacts under `research/experiments/generated/PROD-048A-native-german-review-html-packet/`.
- What was learned: native German review can now be collected as structured JSON/CSV evidence without server infrastructure and without claiming approval before reviewer feedback exists.
- Why it matters for the thesis: PROD-048A separates source-informed machine validation from actual human language review, making the German wording-quality gate auditable.
- Open questions: whether the returned native German review accepts the current wording, requests small wording edits, or reveals broader call-control/end-call issues.

### 2026-05-12 - PROD-047 campaign-profile contract validator

- Objective: create a reusable deterministic campaign-profile contract so future campaign fields cannot enter guarded runtime policies without explicit language, field shape, source boundary, review status, and hard safety defaults.
- Action taken: added `campaign_profile_contract.py`, PROD-047 runner/validator scripts, product documentation, example valid and invalid campaign profiles, generated schema, guard matrix, validation cases/results, report, and review HTML. Runtime behavior was not changed.
- Data used: existing PROD-046 review findings plus synthetic project-owned campaign-profile fixtures only. No raw transcript text, German sales scripts, provider call, LLM call, private data read, retrieval enablement, voice playback, public demo polish, payment collection, contract signing, or production runtime promotion was used.
- Output created: `scripts/campaign_profile_contract.py`, `scripts/run_prod_047_campaign_profile_contract_validator.py`, `scripts/validate_prod_047_campaign_profile_contract_validator.py`, `docs/product/PROD_047_CAMPAIGN_PROFILE_CONTRACT_VALIDATOR.md`, example campaigns under `runtime/campaigns/examples/`, and generated artifacts under `research/experiments/generated/PROD-047-campaign-profile-contract-validator/`.
- What was learned: campaign/profile quality is now enforceable as a deterministic contract instead of a runtime-template assumption. Valid English and German profiles can pass for offline/internal review while still being blocked from voice/demo/customer use.
- Why it matters for the thesis: PROD-047 turns the campaign-field bottleneck found by PROD-046 into an auditable guardrail layer, separating campaign configuration readiness from runtime-policy behavior.
- Open questions: whether the next native German wording review should annotate these campaign profiles directly, and whether later customer/demo promotion needs a stricter legal-review status contract.

### 2026-05-12 - PROD-046 core sales-policy human/product review

- Objective: review the English and German deterministic runtime-policy surface from PROD-045 through PROD-046D before broader promotion.
- Action taken: added a review-only PROD-046 runner, validator, product doc, human review packet, English/German response-quality findings, call-control findings, campaign-field findings, recommended next actions, review HTML, and report. No runtime behavior was changed.
- Data used: existing generated PROD-045, PROD-046A, PROD-046B, PROD-046C, and PROD-046D evidence only. No raw transcript text, external scripts, provider call, LLM call, private data read, retrieval enablement, voice playback, public demo polish, payment collection, contract signing, or production runtime promotion was used.
- Output created: `scripts/prod_046_core_sales_policy_human_review.py`, runner/validator scripts, `docs/product/PROD_046_CORE_SALES_POLICY_HUMAN_REVIEW.md`, and generated artifacts under `research/experiments/generated/PROD-046-core-sales-policy-human-review/`.
- What was learned: the current policy surface is strong enough for offline regression evidence and internal product review, but not for voice/demo/customer use. German still needs native-speaker review, some safe end-call decisions may feel abrupt, and campaign-field contracts are the strongest next deterministic product-quality gate.
- Why it matters for the thesis: PROD-046 separates deterministic regression success from product-readiness claims, showing that multilingual policy safety, wording quality, campaign profile shape, and customer-facing promotion are distinct validation layers.
- Open questions: whether the campaign-profile validator should precede native German review for all future campaigns, and which call-control paths should receive bridge-quality tests later.

### 2026-05-12 - PROD-046D German source-informed wording-quality guard

- Objective: reduce remaining internal-sounding German customer-facing runtime wording after PROD-046C using GER-001 source-informed guidance.
- Action taken: added a PROD-046D runner, validator, product doc, source traceability map, before/after wording evidence, review HTML, generated report, and targeted German response/campaign-field wording updates. The changes removed overused customer-facing `freigegeben`, `Vertriebsteil`, log-centric callback wording, and bureaucratic security phrasing while preserving routing and call-control behavior.
- Data used: existing PROD-045/PROD-046A/PROD-046B/PROD-046C generated evidence, synthetic project-owned German regression cases, and accepted GER-001 source URLs from regulator, consumer-protection, public-service, and plain-language sources. The sources were used as wording guidance only, not legal-compliance evidence. No raw transcript text, German sales scripts, provider call, LLM call, private data read, retrieval enablement, voice playback, public demo polish, payment collection, contract signing, or production runtime promotion was used.
- Source-selection rationale: German runtime wording should be informed by consumer-protection and plain-language sources because the active German B2C path involves phone-call trust, written-info, refusal, scam/payment, support/cancellation, and regulated-advice boundaries. Sales scripts, sales guru blogs, aggressive close scripts, affiliate SEO pages, and copied competitor wording were rejected because they optimize persuasion rather than safe customer-facing clarity.
- Output created: `scripts/prod_046d_german_source_informed_wording_quality_guard.py`, runner/validator scripts, `docs/product/PROD_046D_GERMAN_SOURCE_INFORMED_WORDING_QUALITY_GUARD.md`, generated artifacts under `research/experiments/generated/PROD-046D-german-source-informed-wording-quality-guard/`, thesis reference updates, and narrow German wording edits in `scripts/run_realtime_turn_simulation.py` and `scripts/prod_046a_german_naturalized_policy_regression.py`.
- What was learned: deterministic multilingual safety can still sound too internal even after grammar/interpolation fixes. German campaign fields need customer-facing sentence/object shapes, and source-informed wording gates should check for internal metadata terms before human review.
- Why it matters for the thesis: PROD-046D adds a traceable methodology step between deterministic regression and human review: source-informed wording QA can improve customer-facing language without relying on LLM rewriting, sales scripts, provider calls, or legal-compliance claims.
- Open questions: whether a German-speaking human/product reviewer accepts the source-informed wording before voice playback, demo use, retrieval changes, or runtime promotion.

### 2026-05-12 - PROD-046C German campaign-field interpolation guard

- Objective: fix the malformed German campaign-field interpolation left after PROD-046B, especially `bei beim` in price-first responses and `um ein kurzer Abgleich` in identity repair.
- Action taken: added a PROD-046C runner, validator, product doc, generated interpolation guard cases/results, before/after evidence, review HTML, and report. Updated only the German localized response assembly and German campaign fixture fields needed to avoid fragment-sensitive interpolation errors.
- Data used: existing PROD-045/PROD-046A/PROD-046B generated regression evidence and synthetic project-owned German regression cases only. No raw transcript text, provider call, LLM call, private data read, retrieval enablement, voice playback, public demo polish, payment collection, contract signing, or production runtime promotion was used.
- Output created: `scripts/prod_046c_german_campaign_field_interpolation_guard.py`, runner/validator scripts, `docs/product/PROD_046C_GERMAN_CAMPAIGN_FIELD_INTERPOLATION_GUARD.md`, generated artifacts under `research/experiments/generated/PROD-046C-german-campaign-field-interpolation-guard/`, and narrow German interpolation fixes in `scripts/run_realtime_turn_simulation.py` and `scripts/prod_046a_german_naturalized_policy_regression.py`.
- What was learned: removing banned internal terms is not enough; campaign fields need grammar-compatible shapes or full customer-facing sentence fields in German.
- Why it matters for the thesis: PROD-046C records a concrete multilingual guardrail lesson for deterministic sales-agent policy: safety and routing can pass while localized string assembly still fails.
- Open questions: whether the now-guarded German wording is acceptable to a German-speaking human/product reviewer before voice playback, demo use, or runtime promotion.

### 2026-05-11 - PROD-046B German response wording-quality pass

- Objective: improve German customer-facing runtime response wording after PROD-046A proved German routing but still exposed internal-policy-sounding terms.
- Action taken: added a PROD-046B runner, validator, product doc, generated before/after wording evidence, findings, regression rerun results, review HTML, and report. Rewrote only German localized responses and German campaign fixture wording needed to remove internal route/policy terms while preserving call-control and routing behavior.
- Data used: existing PROD-046A/PROD-045 generated regression evidence and synthetic project-owned German cases only. No raw transcript text, external German sales scripts, provider call, LLM call, private data read, retrieval enablement, voice playback, public demo polish, payment collection, contract signing, or production runtime promotion was used.
- Output created: `scripts/prod_046b_german_response_wording_quality_pass.py`, runner/validator scripts, `docs/product/PROD_046B_GERMAN_RESPONSE_WORDING_QUALITY_PASS.md`, generated artifacts under `research/experiments/generated/PROD-046B-german-response-wording-quality-pass/`, and narrow German response wording edits in `scripts/run_realtime_turn_simulation.py`.
- What was learned: deterministic routing can pass while response wording still sounds like internal implementation language; the German path needs a wording-quality gate before human/product review.
- Why it matters for the thesis: PROD-046B records a practical limitation of rule-based multilingual policy work: safety semantics and natural customer-facing language must be validated separately.
- Open questions: whether German-speaking human review accepts the improved wording before any broader demo, voice playback, or runtime-promotion claim.

### 2026-05-11 - PROD-046A German naturalized policy regression

- Objective: prove the PROD-045 runtime-policy surface on natural German de-DE customer utterances, not literal English translations.
- Action taken: added a PROD-046A runner, validator, product doc, generated German regression cases/results, false-positive cases/results, review data, review HTML, and report. Added narrow German phrase triggers and improved German localized responses in the realtime turn classifier.
- Data used: synthetic project-owned German de-DE regression utterances only, plus existing PROD-045 generated evidence. No raw transcript text, external German sales scripts, provider call, LLM call, private data read, retrieval enablement, voice playback, public demo polish, payment collection, contract signing, or production runtime promotion was used.
- Output created: `scripts/prod_046a_german_naturalized_policy_regression.py`, runner/validator scripts, `docs/product/PROD_046A_GERMAN_NATURALIZED_POLICY_REGRESSION.md`, generated artifacts under `research/experiments/generated/PROD-046A-german-naturalized-policy-regression/`, and narrow German runtime policy edits in `scripts/run_realtime_turn_simulation.py`.
- What was learned: the English PROD-045 surface was not enough evidence for German; without German-specific phrase triggers, most natural German customer moves fell into the generic clarification path.
- Why it matters for the thesis: PROD-046A separates multilingual intent-equivalence testing from translation and keeps policy safety measurable across language paths.
- Open questions: whether PROD-046 human review accepts the German and English runtime-policy evidence before any broader demo or voice unlock.

### 2026-05-11 - PROD-045 core sales-policy regression rerun

- Objective: harden the deterministic evaluator exposed by PROD-044, then apply only the justified core sales-policy updates behind regression gates.
- Action taken: added PROD-045 runner, validator, product doc, generated regression cases/results, evaluator hardening results, runtime policy change summary, review data, review HTML, and report. Updated the realtime turn classifier with narrow campaign-guarded policies for price-first, written-info/email-only, identity repair, payment/scam safety, support/cancellation, specialist handoff, existing-provider gap isolation, decision-maker review, and sale-ready guarded next steps.
- Data used: PROD-043/PROD-044 generated evidence plus synthetic generic regression cases only. No raw transcript text, provider call, LLM call, private data read, dataset download, retrieval enablement, voice playback, public demo polish, payment collection, contract signing, or production runtime promotion was used.
- Output created: `scripts/prod_045_core_sales_policy_regression_rerun.py`, runner/validator scripts, `docs/product/PROD_045_CORE_SALES_POLICY_REGRESSION_RERUN.md`, generated artifacts under `research/experiments/generated/PROD-045-core-sales-policy-regression-rerun/`, and narrow runtime policy edits in `scripts/run_realtime_turn_simulation.py`.
- What was learned: generic clarification must be treated as a negative control for required-boundary moves; a response is not safe enough just because it avoids an obvious failure flag.
- Why it matters for the thesis: PROD-045 closes the gap between offline playbook evidence and guarded runtime behavior while preserving reusable SalesCampaign fact boundaries.
- Open questions: whether PROD-046 human review should accept these targeted runtime-policy changes before any broader runtime promotion, demo claim, voice playback unlock, or retrieval default change.

### 2026-05-11 - PROD-044 core sales-policy update review packet

- Objective: review PROD-043 evidence and identify exactly which core sales-policy changes are justified before modifying runtime behavior.
- Action taken: added an offline PROD-044 runner, validator, product doc, generated review packet, review data, review HTML, and report. The runner reads PROD-043 evidence, probes the current deterministic realtime turn entrypoint with PROD-043 synthetic generic cases, groups justified candidate policy updates, lists blocked updates, and records required campaign-fact guards.
- Data used: existing PROD-043 artifacts and synthetic generic single-turn probes only. No raw transcript text, provider call, LLM call, private data read, dataset download, retrieval enablement, runtime behavior change, voice playback, public demo polish, or production runtime promotion was used.
- Output created: `scripts/prod_044_core_sales_policy_update.py`, runner/validator scripts, `docs/product/PROD_044_CORE_SALES_POLICY_UPDATE.md`, and generated artifacts under `research/experiments/generated/PROD-044-core-sales-policy-update/`.
- What was learned: PROD-043 evidence justifies targeted runtime-policy candidates, but the reusable core must receive campaign-approved facts for pricing, identity, written summaries, support/cancellation routes, specialist handoff, and claim boundaries before any runtime edit is applied.
- Why it matters for the thesis: PROD-044 separates evidence-backed policy design from runtime modification, preserving the project boundary between offline sales-intelligence evaluation and production behavior change.
- Open questions: whether the next checkpoint should apply all eight candidate policy groups at once or stage them by highest-risk customer moves such as price-first, email-only, support/cancellation, and payment fear.

### 2026-05-11 - PROD-043 sales playbook runtime adapter

- Objective: create an offline adapter/evaluator that uses PROD-042 turn-level playbook artifacts to classify customer moves, retrieve playbook/evaluation rules, and score single-turn agent responses.
- Action taken: added deterministic customer-move classification cases, playbook retrieval cases, generic good/bad agent-response evaluation cases, evaluation outputs, a static review surface, product documentation, and validator gates for accuracy, retrieval coverage, expected-result matching, and boundary preservation.
- Data used: existing PROD-042 artifacts only plus synthetic generic test cases. No CallCenterEN transcript text, source transcript sequence, provider call, LLM call, private data read, dataset download, runtime behavior change, retrieval enablement, or runtime-agent modification was used.
- Output created: `scripts/prod_043_sales_playbook_runtime_adapter.py`, runner/validator scripts, `docs/product/PROD_043_SALES_PLAYBOOK_RUNTIME_ADAPTER.md`, and generated artifacts under `research/experiments/generated/PROD-043-sales-playbook-runtime-adapter/`.
- What was learned: the PROD-042 playbook can be consumed as an offline rule layer for move classification, playbook lookup, and deterministic single-turn response evaluation without creating another simulator or touching runtime behavior.
- Why it matters for the thesis: PROD-043 bridges extracted sales intelligence toward future agent-policy work while preserving the no-runtime-promotion and no-transcript-copying boundaries.
- Open questions: whether PROD-044 should update core sales policy based on the offline adapter results, and which failure cases should be prioritized first.

### 2026-05-10 - PROD-042 narrow quality fix pass

- Objective: correct output-quality defects in PROD-042 without redesigning the checkpoint or changing runtime behavior.
- Action taken: repaired invalid recovery tactic IDs, made playbook rules move-specific, added move-specific deterministic evaluation checks, enforced safe next-best-action behavior after rejection/boundary reactions, added explicit unsupported-target tactic flags/metrics, and added support-count method/limitations metadata across artifacts and review HTML.
- Data used: existing parsed raw CallCenterEN aggregate outputs and abstract checkpoint cross-check artifacts only. No provider call, LLM call, private data read, dataset download, transcript copying, retrieval enablement, or runtime-agent modification.
- Output created: regenerated PROD-042 artifacts in `research/experiments/generated/PROD-042-callcenteren-turn-pattern-playbook/` and updated PROD-042 generator/validator scripts plus product doc note.
- What was learned: narrow validator gates are needed to prevent structurally valid but tactically weak playbook recommendations, especially around rejection/boundary handling and recovery integrity.
- Why it matters for the thesis: this keeps the turn-level playbook commercially safer and more actionable for a future offline adapter while preserving strict no-runtime-promotion boundaries.
- Open questions: whether low-support target tactics should stay in taxonomy for planning only, or be hidden by default in future review surfaces.

### 2026-05-10 - PROD-042 turn-level sales pattern playbook extraction

- Objective: create a new checkpoint that extracts reusable turn-level sales intelligence from CallCenterEN raw zip aggregates instead of generating more synthetic scenario conversations.
- Action taken: added deterministic raw zip parsing, aggregate turn-signal extraction, source-index cross-checking against PROD-013/PROD-014, pattern artifact generation (moves/tactics/quality/reaction/state/next-action/failure/recovery/playbook/evaluation), static HTML review surface, and validator gates for leakage/commercial-safety/no-scenario-generation boundaries.
- Data used: primary raw source `data/external/callcenteren/raw` plus existing abstract checkpoints `PROD-013` and `PROD-014` for cross-check/fallback enrichment only. No provider call, LLM call, private data read, dataset download, transcript copying, source-sequence copying, runtime behavior change, retrieval enablement, or runtime-agent modification was used.
- Output created: `docs/product/PROD_042_CALLCENTEREN_TURN_PATTERN_PLAYBOOK.md`, `scripts/prod_042_callcenteren_turn_pattern_playbook.py`, `scripts/run_prod_042_callcenteren_turn_pattern_playbook.py`, `scripts/validate_prod_042_callcenteren_turn_pattern_playbook.py`, and generated artifacts under `research/experiments/generated/PROD-042-callcenteren-turn-pattern-playbook/`.
- What was learned: turn-level pattern extraction is a stronger foundation for next-step offline runtime adapters than producing additional synthetic dialogue scripts; coverage gaps can be reported explicitly without hallucinating unsupported categories.
- Why it matters for the thesis: this preserves commercial-safety boundaries while still producing actionable customer-move/tactic/reaction intelligence for deterministic evaluation and future adapter work.
- Open questions: whether PROD-043 should first consume playbook rules as an offline evaluator overlay, a bounded offline response-shaping adapter, or both in sequence.

### 2026-05-10 - PROD-041A agent reactivity validation repair

- Objective: fix the PROD-041A failure where customer responses changed but agent answers could repeat or ignore the latest customer turn.
- Action taken: added deterministic customer intent classification, per-turn agent reactivity fields, repeated-answer and looping-question detection, state penalties for repeated/ignored agent behavior, false-safe-close guards, review-surface reactivity fields, and validator gates requiring agent responses to address the immediately previous customer intent.
- Data used: existing offline PROD-041A recipes, scenario profiles, and deterministic generated artifacts only. No provider call, LLM call, private data read, dataset download, transcript copying, runtime behavior change, or production promotion was used.
- Output created: regenerated `interaction_traces.json`, `scenario_diversity_traces.json`, `scenario_diversity_review.html`, `scenario_diversity_review_data.json`, `result.json`, and `report.md` under `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/`.
- What was learned: the current local sales-agent harness is callable but not sufficient as final contextual trace text because it is single-turn/stage-classified. PROD-041A now records that truthfully and validates the deterministic reactivity adapter against zero repeated agent answers, zero ignored customer inputs, zero looping questions, and zero false safe closes.
- Why it matters for the thesis: it separates customer reactivity from agent reactivity and prevents long offline traces from looking interactive when the agent is actually looping.

### 2026-05-10 - PROD-041A interactive conditional customer simulation rewrite

- Objective: replace PROD-041A fixed scripted dialogue with interactive conditional customer simulation.
- Action taken: added `customer_reaction_policy_bank.json`, `interactive_scenario_profiles.json`, canonical `interaction_traces.json`, and a validator that checks seeded variation, variable exchange counts, `agent_action_tags`, selected `reaction_rule_ids`, customer state before/after records, no static scripts, and no runtime promotion.
- Data used: existing PROD-013/PROD-014 abstract pattern IDs and the local deterministic sales-agent turn harness only. No provider call, LLM call, private data read, dataset download, transcript text copying, source sequence copying, or runtime behavior change was used.
- Output created: regenerated `scenario_recipes.json`, `customer_reaction_policy_bank.json`, `concrete_scenario_frames.json`, `interactive_scenario_profiles.json`, `interaction_traces.json`, `scenario_diversity_traces.json`, `scenario_diversity_review.html`, `scenario_diversity_review_data.json`, `result.json`, and `report.md` under `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/`.
- What was learned: a useful offline sales simulator needs customer state and reaction policies, not prewritten calls. The repaired checkpoint now produces `120` traces from `40` profiles x `3` seeds, with variable lengths and customer turns reacting to the immediately previous agent tags.
- Why it matters for the thesis: it tests dynamic interaction quality and safe recovery behavior while keeping CallCenterEN use leakage-safe and abstract.
- Open questions: whether PROD-041 human review should accept the local deterministic agent harness behavior or require a later runtime-agent upgrade before voice/demo use.

### 2026-05-10 - PROD-041A leakage-safe scenario recipe layer

- Objective: repair PROD-041A grounding so concrete frames and dialogue are produced from abstract reusable scenario recipes, not direct scenario labels or any individual CallCenterEN-like source situation.
- Action taken: added `scenario_recipes.json`, wired frames and traces to reference `recipe_id`, removed provider-brand names from visible openings, added `spoken_trace_authoring` so frames are semantic inputs rather than speech strings, and strengthened the validator to require abstract pattern IDs, fictional context flags, no source sequence copying, no dataset-specific phrasing, no frame-field restatement, and no source wording in spoken dialogue.
- Data used: existing PROD-014/PROD-013 abstract pattern artifacts only. No provider call, LLM call, private data read, dataset download, transcript copying, source-sequence copying, or runtime behavior change was used.
- Output created: regenerated `scenario_recipes.json`, `concrete_scenario_frames.json`, `scenario_diversity_traces.json`, `scenario_diversity_review.html`, `scenario_diversity_review_data.json`, `result.json`, and `report.md` under `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/`.
- What was learned: PROD-041A can keep the same `40` labels and metrics while making the source boundary explicit: abstract recipe -> original fictional frame -> authored spoken trace. Direct frame-field interpolation produced metadata-like dialogue; authored scripts are now the only visible speech source.
- Why it matters for the thesis: it preserves commercial-safety evidence by preventing close paraphrases, transcript text, names, provider names, unique source event sequences, or source dialogue from entering review-ready artifacts.
- Open questions: whether the next human review should accept the recipe-grounded traces for offline evidence or request targeted rewrites before voice/demo use.

### 2026-05-10 - PROD-041A spoken-reason and review-surface repair

- Objective: fix the two PROD-041A review findings without expanding or redesigning the checkpoint.
- Action taken: added per-frame `spoken_reason` text for spoken relevance lines, stopped using internal `realistic_agent_goal` text in agent speech, restored per-call terminal scoring and failure-taxonomy rendering in the review HTML, and strengthened validator coverage for both issues.
- Data used: existing offline PROD-041A concrete frames and generated traces only. No provider call, LLM call, private data read, dataset download, or runtime behavior change was used.
- Why it matters for the thesis: the checkpoint now better separates internal evaluation goals from spoken dialogue while preserving review evidence for terminal outcomes, safe-close accounting, and failure taxonomy.

### 2026-05-10 - PROD-041A concrete scenario frame mining and dialogue naturalness repair

- Objective: repair PROD-041A dialogue realism without adding scenarios by introducing a concrete frame-mining layer between abstract pattern sources and generated traces.
- Action taken: rewrote PROD-041A generation so spoken dialogue is produced from `concrete_scenario_frames.json` instead of direct scenario-label concern text; updated runner outputs, validator gates, review surface fields, and naturalness checks.
- Data used: abstract-only sources from `PROD-014` scenario-bank IDs and `PROD-013` pattern IDs. No provider call, LLM call, private data read, dataset download, transcript copying, or runtime behavior change was used.
- Output created: updated `scripts/prod_041a_conditional_scenario_diversity_expansion.py`, `scripts/run_prod_041a_conditional_scenario_diversity_expansion.py`, `scripts/validate_prod_041a_conditional_scenario_diversity_expansion.py`, and regenerated `result.json`, `report.md`, `concrete_scenario_frames.json`, `scenario_diversity_traces.json`, `scenario_diversity_review.html`, `scenario_diversity_review_data.json` under `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/`.
- What was learned: frame-grounded generation removes most evaluator-style phrasing while keeping deterministic coverage. Each trace now references one unique frame, dialogue realism scores use a `7`-component naturalness model, and frame-quality/bridge-repeat/short-reply/challenge metrics can be validated directly.
- Why it matters for the thesis: this isolates realism repair from scenario-count expansion and keeps the evidence chain clean: abstract mined patterns -> concrete safe frames -> deterministic review-ready traces.
- Open questions: whether PROD-041 human review accepts the repaired dialogue as sufficiently natural, or requests targeted trace rewrites before any voice/demo use.

### 2026-05-10 - PROD-041 conditional simulation review

- Objective: complete the human review checkpoint for the locked PROD-041A expanded traces without expanding the scenario set again.
- Action taken: added the PROD-041 review module, runner, validator, product doc, generated result/report/review-packet artifacts, command-map coverage, setup coverage, drift-guard coverage, and thesis documentation.
- Data used: the generated `PROD-041A-conditional-scenario-diversity-expansion` result and trace artifacts only. No provider call, LLM call, private data read, dataset download, PROD-041A modification, runtime behavior change, retrieval default change, composer-hook default change, customer data, server start, or payment handling was used.
- Output created: `docs/product/PROD_041_CONDITIONAL_SIMULATION_REVIEW.md`, `scripts/prod_041_conditional_simulation_review.py`, `scripts/run_prod_041_conditional_simulation_review.py`, `scripts/validate_prod_041_conditional_simulation_review.py`, `research/experiments/generated/PROD-041-conditional-simulation-review/result.json`, `research/experiments/generated/PROD-041-conditional-simulation-review/report.md`, and `research/experiments/generated/PROD-041-conditional-simulation-review/conditional_simulation_review_packet.json`.
- What was learned: PROD-041A is structurally complete and should stay locked. The remaining deterministic phrasing is acceptable for offline review only, but customer language still has template-like moments and some safe-close outcomes are only partially earned. Targeted customer-turn rewrites are required before voice playback or public demo use.
- Why it matters for the thesis: the checkpoint separates broad deterministic scenario coverage from human realism judgment, preventing the project from hiding demo-readiness concerns behind more generated scenarios.
- Open questions: which selected customer turns should be rewritten first if voice playback or public demo polish is reopened.

### 2026-05-10 - PROD-041A conditional scenario diversity expansion

- Objective: expand the conditional simulator before the PROD-041 human review so the review is based on a broader, mixed B2B/B2C scenario set instead of the original eight calls.
- Action taken: added the PROD-041A scenario diversity module, runner, validator, product doc, static HTML inspection surface, generated trace/data/report/result artifacts, command-map coverage, setup coverage, drift-guard coverage, and thesis documentation.
- Data used: the PROD-014 leakage-checked scenario bank and the PROD-013 abstract CallCenterEN pattern bank for abstract pattern IDs only. No provider call, LLM call, private data read, dataset download, raw transcript storage, copied transcript text, transcript-derived runtime prompt, runtime behavior change, retrieval default change, composer-hook default change, customer data, server start, or payment handling was used.
- Output created: `docs/product/PROD_041A_CONDITIONAL_SCENARIO_DIVERSITY_EXPANSION.md`, `scripts/prod_041a_conditional_scenario_diversity_expansion.py`, `scripts/run_prod_041a_conditional_scenario_diversity_expansion.py`, `scripts/validate_prod_041a_conditional_scenario_diversity_expansion.py`, `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/result.json`, `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/report.md`, `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/scenario_diversity_traces.json`, `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/scenario_diversity_review.html`, and `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/scenario_diversity_review_data.json`.
- What was learned: the review packet can now test breadth as well as conditional turn quality. PROD-041A creates `40` calls with `24` B2B and `16` B2C scenarios, one curated scenario label per call, all `7` opening styles, deterministic strategy detection, deterministic emotion handling, richer terminal outcomes, scenario-level scores, and failure taxonomy counts while keeping hard failures, payment collection, unsupported claims, and leakage at `0`.
- Review correction: initial human inspection found that the first generated PROD-041A traces leaked checkpoint/scenario metadata into spoken answers, used raw scenario labels such as `price_sensitive` as customer-facing language, and failed to answer the price objection directly. The generator and validator were revised so visible review text cannot contain checkpoint IDs, blocked raw scenario labels, evaluator-style phrases such as direct-answer instructions, or a price-sensitive first answer without the explicit synthetic price range.
- Dialogue realism correction: later human inspection found that structurally valid traces still sounded too templated, especially repeated customer phrases such as "That boundary makes sense", "My remaining concern is", and "What would the next step be without pushing me". The generator now adds deterministic non-smooth customer behavior, including interruptions, skeptical pushback, one-word refusals, confused follow-ups, early price asks, identity checks, email-only requests, and refusal-before-finish cases. The validator now requires per-trace dialogue realism scores, bans the repeated template phrases, checks duplicated opening words such as `where where`, requires at least `20%` non-smooth traces, and keeps hard failures, payment collection, unsupported claims, and leakage at `0`.
- Final realism hardening: a final pass banned additional semi-template customer phrasing such as "Because you kept it brief on", "If we continue, I want the step to stay limited to", and "I am not ready to agree on". Customer turns now include more short imperfect replies such as "Fine, send it", "Email only", "No, not today", "Who exactly are you?", "I need to ask my manager", "That still sounds vague", and "What are you actually selling?". Dialogue realism scoring is stricter, with an average score of `4.45` and `18` perfect traces instead of all calls receiving `5/5`, while safety counters remain at `0`.
- Why it matters for the thesis: the simulator review can now assess whether emotion-aware sales behavior remains safe and strategy-aligned across diverse objections, markets, domains, and terminal outcomes before any voice or public demo expansion.
- Open questions: whether human review accepts the broader scenario traces as realistic enough to unblock voice playback, scenario branching, more call seeds, or public demo polish.

### 2026-05-10 - PROD-040 CallCenterEN conditional customer simulation

- Objective: make simulated customer replies vary turn by turn according to the agent's preceding answer, using CallCenterEN-derived interaction patterns without copying transcript text.
- Action taken: added the PROD-040 conditional simulator module, runner, validator, product doc, static HTML inspection surface, generated trace/data/report/result artifacts, command-map coverage, setup coverage, drift-guard coverage, and thesis documentation.
- Data used: PROD-039 hardened traces, the PROD-014 leakage-checked scenario bank, and the PROD-013 abstract CallCenterEN pattern bank. No provider call, LLM call, private data read, dataset download, raw transcript storage, copied transcript text, transcript-derived runtime prompt, runtime behavior change, retrieval default change, composer-hook default change, customer data, server start, or payment handling was used.
- Output created: `docs/product/PROD_040_CALLCENTEREN_CONDITIONAL_CUSTOMER_SIMULATION.md`, `scripts/prod_040_callcenteren_conditional_customer_simulation.py`, `scripts/run_prod_040_callcenteren_conditional_customer_simulation.py`, `scripts/validate_prod_040_callcenteren_conditional_customer_simulation.py`, `research/experiments/generated/PROD-040-callcenteren-conditional-customer-simulation/result.json`, `research/experiments/generated/PROD-040-callcenteren-conditional-customer-simulation/report.md`, `research/experiments/generated/PROD-040-callcenteren-conditional-customer-simulation/conditional_customer_traces.json`, `research/experiments/generated/PROD-040-callcenteren-conditional-customer-simulation/conditional_customer_trace_demo.html`, and `research/experiments/generated/PROD-040-callcenteren-conditional-customer-simulation/conditional_customer_trace_demo_data.json`.
- What was learned: conditional customer simulation is a better inspection target than a same-case text rerun. PROD-040 creates `8` calls and `24` customer turns with conditional customer turn count `24`, agent-conditioned customer reply count `24`, unique customer response count `24`, repeated customer response count `0`, unique agent answer count `24`, repeated agent answer count `0`, profile customized agent answer count `24`, B2B call count `6`, B2C call count `2`, internal reason answer count `6`, internal reason price-first violation count `0`, agent opening line visible count `8`, conversation sequence starts with agent count `8`, CallCenterEN pattern source count `59`, scenario bank source count `8`, accepted deals `6`, rejected deals `2`, hard failures `0`, payment collection count `0`, and leakage findings `0`.
- Why it matters for the thesis: the simulator now tests dynamic interaction quality, not just single-turn response quality, while preserving source-safety and no-runtime-promotion boundaries.
- Open questions: whether the conditional conversations feel realistic enough under human review to unblock voice playback, scenario branching, more seeds, or public demo polish.

### 2026-05-10 - PROD-039 customer realism simulator hardening

- Objective: improve the realism of simulated customer responses on the same fixed calls without changing agent behavior or safety outcomes.
- Action taken: added the PROD-039 hardening module, runner, validator, product doc, generated result/report/hardened-trace/comparison artifacts, command-map coverage, setup coverage, drift-guard coverage, and thesis documentation.
- Data used: the generated PROD-037 surface data and PROD-038 review packet only. No provider call, LLM call, private data read, dataset download, runtime behavior change, retrieval default change, composer-hook default change, customer data, server start, or payment handling was used.
- Output created: `docs/product/PROD_039_CUSTOMER_REALISM_SIMULATOR_HARDENING.md`, `scripts/prod_039_customer_realism_simulator_hardening.py`, `scripts/run_prod_039_customer_realism_simulator_hardening.py`, `scripts/validate_prod_039_customer_realism_simulator_hardening.py`, `research/experiments/generated/PROD-039-customer-realism-simulator-hardening/result.json`, `research/experiments/generated/PROD-039-customer-realism-simulator-hardening/report.md`, `research/experiments/generated/PROD-039-customer-realism-simulator-hardening/customer_realism_hardened_traces.json`, `research/experiments/generated/PROD-039-customer-realism-simulator-hardening/customer_realism_comparison_packet.json`, and `research/experiments/generated/PROD-039-customer-realism-simulator-hardening/customer_realism_comparison.html`.
- What was learned: customer realism can be improved as a separate simulator layer. PROD-039 changes `14` customer responses and `8` customer openings while keeping agent answer changed count `0`, decision snapshot changed count `0`, terminal outcome changed count `0`, and safety flag changed count `0`. Baseline unrealistic phrase hits drop from `11` to `0`, with `29` naturalness features recorded.
- Why it matters for the thesis: the project now separates conversation realism from runtime policy behavior and can compare old versus hardened customer speech on fixed cases before expanding the demo.
- Open questions: whether the hardened traces feel better in the actual replay UI and whether more realistic customer speech exposes new route or policy issues.

### 2026-05-10 - PROD-038 local demo surface review

- Objective: record the human review outcome for the local trace demo surface before adding voice playback or public demo polish.
- Action taken: added the PROD-038 review module, runner, validator, product doc, generated result/report/review-packet artifacts, command-map coverage, setup coverage, drift-guard coverage, and thesis documentation.
- Data used: the generated PROD-037 surface data and Tarik's review that the customer responses are weak and unrealistic. No provider call, LLM call, private data read, dataset download, runtime behavior change, retrieval default change, composer-hook default change, customer data, server start, or payment handling was used.
- Output created: `docs/product/PROD_038_LOCAL_DEMO_SURFACE_REVIEW.md`, `scripts/prod_038_local_demo_surface_review.py`, `scripts/run_prod_038_local_demo_surface_review.py`, `scripts/validate_prod_038_local_demo_surface_review.py`, `research/experiments/generated/PROD-038-local-demo-surface-review/result.json`, `research/experiments/generated/PROD-038-local-demo-surface-review/report.md`, and `research/experiments/generated/PROD-038-local-demo-surface-review/local_demo_surface_review_packet.json`.
- What was learned: the demo surface works as an inspection tool, but the conversation content is not ready. PROD-038 accepts demo surface UI `true`, rejects customer response realism `false`, sets conversation quality gate passed `false`, records `5` customer-response issue categories, and blocks voice playback, scenario branching, more seeds, and public demo polish.
- Why it matters for the thesis: it prevents the project from mistaking interface readiness for conversational realism. The next evidence needs to prove better customer simulation on the same cases before expanding the demo.
- Open questions: which customer-realism constraints improve naturalness without hiding rejection, compliance, or safe-close boundaries.

### 2026-05-10 - PROD-037 local interactive trace demo surface

- Objective: turn the accepted PROD-036 readiness packet into a local browser-openable trace replay surface for inspection.
- Action taken: added the PROD-037 surface module, runner, validator, product doc, generated result/report/surface-data/static-HTML artifacts, command-map coverage, setup coverage, drift-guard coverage, and thesis documentation.
- Data used: the generated PROD-036 readiness packet only. No provider call, LLM call, private data read, dataset download, runtime behavior change, retrieval default change, composer-hook default change, customer data, server start, or payment handling was used.
- Output created: `docs/product/PROD_037_LOCAL_INTERACTIVE_TRACE_DEMO_SURFACE.md`, `scripts/prod_037_local_interactive_trace_demo_surface.py`, `scripts/run_prod_037_local_interactive_trace_demo_surface.py`, `scripts/validate_prod_037_local_interactive_trace_demo_surface.py`, `research/experiments/generated/PROD-037-local-interactive-trace-demo-surface/result.json`, `research/experiments/generated/PROD-037-local-interactive-trace-demo-surface/report.md`, `research/experiments/generated/PROD-037-local-interactive-trace-demo-surface/local_interactive_trace_demo_surface.html`, and `research/experiments/generated/PROD-037-local-interactive-trace-demo-surface/local_interactive_trace_demo_surface_data.json`.
- What was learned: the first practical demo artifact can stay simple and evidence-driven. PROD-037 reports surface ready `true`, visible calls `8`, visible turns `14`, selectable calls `8`, selectable turns `14`, static HTML ready `true`, keyboard accessible controls `true`, exact customer text visible `true`, exact agent answer visible `true`, decision process visible `true`, state transition visible `true`, terminal outcome visible `true`, safety flags visible `true`, cold opening visible `true`, and local synthetic trace replay `true`.
- Why it matters for the thesis: the project now has an auditable bridge from metrics to inspectable conversation behavior, so claims about answer quality and decision logic can be reviewed turn by turn.
- Open questions: whether the surface is ergonomic enough before adding voice playback, scenario branching, or more seeds.

### 2026-05-10 - PROD-036 interactive demo readiness review

- Objective: decide whether the aligned PROD-035 traces are ready to become a local interactive trace demo surface.
- Action taken: added the PROD-036 readiness module, runner, validator, product doc, generated result/report/readiness-packet/static-preview artifacts, command-map coverage, setup coverage, drift-guard coverage, and thesis documentation.
- Data used: the generated PROD-035 result and aligned interactive trace artifacts only. No provider call, LLM call, private data read, dataset download, runtime behavior change, retrieval default change, composer-hook default change, customer data, server start, or payment handling was used.
- Output created: `docs/product/PROD_036_INTERACTIVE_DEMO_READINESS_REVIEW.md`, `scripts/prod_036_interactive_demo_readiness_review.py`, `scripts/run_prod_036_interactive_demo_readiness_review.py`, `scripts/validate_prod_036_interactive_demo_readiness_review.py`, `research/experiments/generated/PROD-036-interactive-demo-readiness-review/result.json`, `research/experiments/generated/PROD-036-interactive-demo-readiness-review/report.md`, `research/experiments/generated/PROD-036-interactive-demo-readiness-review/interactive_demo_readiness_packet.json`, and `research/experiments/generated/PROD-036-interactive-demo-readiness-review/interactive_demo_readiness_preview.html`.
- What was learned: the aligned traces are sufficient for the first local demo surface. PROD-036 reports local interactive demo ready `true`, demo-ready calls `8`, demo blocker count `0`, exact customer text visible `true`, exact agent answer visible `true`, decision process visible `true`, state transition visible `true`, terminal outcome visible `true`, safety flags visible `true`, cold opening visible `true`, decision snapshot mismatches `0`, and unknown-objection decisions `0`.
- Why it matters for the thesis: the project now has a reviewable bridge from evaluation artifacts to demo artifacts without confusing synthetic local trace replay with live deployment.
- Open questions: how interactive the PROD-037 demo surface should be before voice or provider integration becomes useful.

### 2026-05-10 - PROD-035 runtime decision-trace alignment

- Objective: align the visible runtime decision process with the actual spoken answer behavior in the clean PROD-033 interactive traces.
- Action taken: added an opt-in `align_decision_trace` path to the guarded response generator, plus the PROD-035 module, runner, validator, product doc, generated aligned trace/report artifacts, command-map coverage, setup coverage, drift-guard coverage, and thesis documentation.
- Data used: the generated PROD-034 result and PROD-033 interactive trace artifacts only. No provider call, LLM call, private data read, dataset download, retrieval default change, composer-hook default change, customer data, server start, or payment handling was used.
- Output created: `docs/product/PROD_035_RUNTIME_DECISION_TRACE_ALIGNMENT.md`, `scripts/prod_035_runtime_decision_trace_alignment.py`, `scripts/run_prod_035_runtime_decision_trace_alignment.py`, `scripts/validate_prod_035_runtime_decision_trace_alignment.py`, `research/experiments/generated/PROD-035-runtime-decision-trace-alignment/result.json`, `research/experiments/generated/PROD-035-runtime-decision-trace-alignment/report.md`, `research/experiments/generated/PROD-035-runtime-decision-trace-alignment/aligned_interactive_call_traces.json`, and `research/experiments/generated/PROD-035-runtime-decision-trace-alignment/aligned_interactive_call_trace.html`.
- What was learned: decision visibility can be improved independently from spoken answer text. PROD-035 preserved spoken answers with changed count `0`, customer response changed count `0`, and terminal outcome changed count `0`, while reducing decision snapshot mismatches from `13` to `0` and unknown-objection decisions from `6` to `0`.
- Why it matters for the thesis: evaluation needs an honest trace of what the agent decided. Otherwise a good spoken answer can still be hard to audit, reproduce, or explain.
- Open questions: whether the aligned trace is now strong enough for a local interactive demo readiness review, and whether the opt-in alignment should later become the default runtime trace behavior after broader regression checks.

### 2026-05-10 - PROD-034 interactive post-fix review

- Objective: review the completed PROD-033 cold-opening and outcome-driven traces before deciding between runtime decision-trace alignment and local demo review.
- Action taken: added the PROD-034 review module, runner, validator, product doc, generated result/report/review-packet/static-HTML artifacts, command-map coverage, setup coverage, drift-guard coverage, and thesis documentation.
- Data used: the generated PROD-033 result and interactive trace artifacts only. No provider call, LLM call, private data read, dataset download, runtime behavior change, retrieval default change, composer-hook default change, customer data, server start, or payment handling was used.
- Output created: `docs/product/PROD_034_INTERACTIVE_POST_FIX_REVIEW.md`, `scripts/prod_034_interactive_post_fix_review.py`, `scripts/run_prod_034_interactive_post_fix_review.py`, `scripts/validate_prod_034_interactive_post_fix_review.py`, `research/experiments/generated/PROD-034-interactive-post-fix-review/result.json`, `research/experiments/generated/PROD-034-interactive-post-fix-review/report.md`, `research/experiments/generated/PROD-034-interactive-post-fix-review/interactive_post_fix_review_packet.json`, and `research/experiments/generated/PROD-034-interactive-post-fix-review/interactive_post_fix_review_trace.html`.
- What was learned: the simulator mechanics are now clean enough to stop fixing the simulator itself. PROD-034 kept cold opening fix passed `true`, outcome-driven termination passed `true`, fixed turn limit used `false`, loop guard triggered `false`, max-turn terminal count `0`, callback converted to sale-ready `0`, repeated agent answers `0`, repeated customer messages `0`, hard failures `0`, payment collection count `0`, unsupported claim count `0`, and leakage findings `0`. The remaining issue is decision visibility: decision snapshot mismatches were `13`, and unknown-objection decisions were `6`.
- Why it matters for the thesis: the thesis can separate answer quality from explainability/debuggability. A sales agent can speak acceptably while its logged decision process is still too generic for rigorous evaluation.
- Open questions: how to align the decision trace without making the actual answer more robotic, more question-heavy, or less direct.

### 2026-05-10 - PROD-033 interactive simulator termination fix

- Objective: fix the interactive simulator so calls start from cold-call entrances and end by customer acceptance or rejection instead of repeated fixed-length turns.
- Action taken: added the PROD-033 simulator, runner, validator, product doc, generated trace/report artifacts, command-map coverage, setup coverage, drift-guard coverage, and thesis documentation.
- Data used: the RouteSignal CRM synthetic campaign and deterministic cold-call seeds. No provider call, LLM call, private data read, dataset download, runtime behavior change, retrieval default change, composer-hook default change, customer data, server start, or payment handling was used.
- Output created: `docs/product/PROD_033_INTERACTIVE_SIMULATOR_TERMINATION_FIX.md`, `scripts/prod_033_interactive_simulator_termination_fix.py`, `scripts/run_prod_033_interactive_simulator_termination_fix.py`, `scripts/validate_prod_033_interactive_simulator_termination_fix.py`, `research/experiments/generated/PROD-033-interactive-simulator-termination-fix/result.json`, `research/experiments/generated/PROD-033-interactive-simulator-termination-fix/report.md`, `research/experiments/generated/PROD-033-interactive-simulator-termination-fix/interactive_call_traces.json`, and `research/experiments/generated/PROD-033-interactive-simulator-termination-fix/interactive_call_trace.html`.
- What was learned: cold-call openings and outcome-driven termination remove the most obvious simulator artifacts. PROD-033 produced `8` cold-call openings, all calls started with an agent opening, all calls ended by customer decision, fixed turn limit used was `false`, loop guard triggered was `false`, max-turn terminal count was `0`, accepted deals were `4`, rejected deals were `4`, callback converted to sale-ready was `0`, repeated agent answers were `0`, and repeated customer messages were `0`.
- Why it matters for the thesis: simulator realism now includes the first-contact sales opening and a terminal customer decision, so later policy reviews are less likely to optimize for artificial benchmark structure.
- Open questions: whether the post-fix traces still expose runtime decision-snapshot mismatches, and whether the next fix should target decision trace alignment or full demo review.

### 2026-05-09 - PROD-032 interactive simulation review

- Objective: inspect the PROD-031 reactive state traces and decide which issues are simulator-design limits, runtime-policy issues, product-grounding issues, or still-relevant static route gaps.
- Action taken: added the PROD-032 review module, runner, validator, product doc, command-map coverage, setup coverage, drift-guard coverage, generated result/report/review-packet/static-HTML artifacts, and thesis documentation.
- Data used: the generated PROD-031 result and interactive trace artifacts only. No provider call, LLM call, private data read, dataset download, runtime behavior change, retrieval default change, composer-hook default change, customer data, server start, or payment handling was used.
- Output created: `docs/product/PROD_032_INTERACTIVE_SIMULATION_REVIEW.md`, `scripts/prod_032_interactive_simulation_review.py`, `scripts/run_prod_032_interactive_simulation_review.py`, `scripts/validate_prod_032_interactive_simulation_review.py`, `research/experiments/generated/PROD-032-interactive-simulation-review/result.json`, `research/experiments/generated/PROD-032-interactive-simulation-review/report.md`, `research/experiments/generated/PROD-032-interactive-simulation-review/interactive_simulation_review_packet.json`, and `research/experiments/generated/PROD-032-interactive-simulation-review/interactive_simulation_review_trace.html`.
- What was learned: headline metrics can look clean while trace-level review still finds important limitations. PROD-032 found `54` raw findings across `7` affected calls: callback converted to sale-ready `5` times, repeated agent answers `12`, repeated customer messages `4`, decision snapshot mismatches `19`, unknown-objection decisions `6`, and premature close markers `3`. Product grounding issues remained `0`, with hard failures `0`, payment collection count `0`, unsupported claim count `0`, and leakage findings `0`.
- Why it matters for the thesis: the evaluation now separates safe answer content, visible decision-process correctness, simulator realism, and route-gap relevance instead of collapsing them into one success metric.
- Open questions: whether PROD-033 can remove artificial callback/repetition loops without hiding genuine runtime policy gaps, and which runtime decision trace mismatch should be fixed first after terminal control is clean.

### 2026-05-09 - PROD-031 interactive grounded call simulation

- Objective: replace weak static customer-turn replay with deterministic reactive customer simulation.
- Action taken: added the PROD-031 simulator, runner, validator, product doc, generated trace/report artifacts, command-map coverage, setup coverage, drift-guard coverage, and thesis documentation.
- Data used: the project-owned RouteSignal CRM synthetic campaign and deterministic customer seeds. No provider call, LLM call, private data read, dataset download, runtime change, retrieval default change, composer-hook default change, customer data, server start, or payment handling was used.
- Output created: `docs/product/PROD_031_INTERACTIVE_GROUNDED_CALL_SIMULATION.md`, `scripts/prod_031_interactive_grounded_call_simulation.py`, `scripts/run_prod_031_interactive_grounded_call_simulation.py`, `scripts/validate_prod_031_interactive_grounded_call_simulation.py`, `research/experiments/generated/PROD-031-interactive-grounded-call-simulation/result.json`, `research/experiments/generated/PROD-031-interactive-grounded-call-simulation/report.md`, `research/experiments/generated/PROD-031-interactive-grounded-call-simulation/interactive_call_traces.json`, and `research/experiments/generated/PROD-031-interactive-grounded-call-simulation/interactive_call_trace.html`.
- What was learned: reactive state traces are stronger evidence than static scenario replay because they show whether an agent answer changes customer trust, interest, clarity, friction, objections, and commitment. PROD-031 ran `8` seeds, `26` turns, and `18` reactive customer turns with safe close rate `1.0`, non-sale correctness `1.0`, interactive realism score `1.0`, hard failures `0`, payment collection count `0`, unsupported claim count `0`, and leakage findings `0`.
- Why it matters for the thesis: the evaluation now measures conversational effect, not only correctness against prewritten turns.
- Open questions: which findings are simulator-design limits, which are runtime policy issues, and whether the old static route gaps still need direct fixes.

### 2026-05-09 - PROD-031 interactive simulation design pivot

- Objective: respond to Tarik's review that the current full scenarios are still weak because customer turns are scripted replay rather than reactive conversation.
- Action taken: wrote the `PROD-031-interactive-grounded-call-simulation` design spec and updated the roadmap/decision log to replace the planned static route-gap fix with a deterministic interactive customer simulator.
- Data used: the completed PROD-027 through PROD-030 evidence and Tarik's product review feedback. No provider call, LLM call, private data read, dataset download, runtime change, retrieval default change, composer-hook default change, server start, customer data, or payment handling was used.
- Output created: `docs/superpowers/specs/2026-05-09-interactive-grounded-call-simulation-design.md`.
- What was learned: static multi-turn replay is useful as regression evidence, but it is not strong enough to evaluate sales ability because customer trust, clarity, interest, friction, objections, and commitment do not react to the agent.
- Why it matters for the thesis: the next evaluation layer must measure stateful conversational effect, not only answer correctness on prewritten turns.
- Open questions: which simulator failure modes will represent real runtime defects versus simulator-design limits, and whether route-gap fixes still matter after reactive evaluation.

### 2026-05-09 - PROD-030 grounded demo review

- Objective: inspect the PROD-029 grounded full-scenario trace and decide which grounded answers are demo-ready, which route gaps need revision, and whether runtime campaign-profile promotion is still blocked.
- Action taken: added a PROD-030 grounded demo review module, runner, validator, product doc, command-map coverage, checkpoint index entry, setup coverage, drift-guard fixture coverage, thesis logs, and generated result/report/review-packet/static-HTML artifacts.
- Data used: the generated `PROD-029` grounded full-scenario result only. PROD-030 did not call providers, call an LLM, read private data, download a dataset, start a server, enable retrieval by default, enable composer hooks by default, collect payment, change runtime behavior, or promote the runtime campaign profile.
- Output created: `docs/product/PROD_030_GROUNDED_DEMO_REVIEW.md`, `scripts/prod_030_grounded_demo_review.py`, `scripts/run_prod_030_grounded_demo_review.py`, `scripts/validate_prod_030_grounded_demo_review.py`, `research/experiments/generated/PROD-030-grounded-demo-review/result.json`, `research/experiments/generated/PROD-030-grounded-demo-review/report.md`, `research/experiments/generated/PROD-030-grounded-demo-review/demo_review_packet.json`, and `research/experiments/generated/PROD-030-grounded-demo-review/demo_review_trace.html`.
- What was learned: the grounded answer layer is ready as a local demo wording candidate, with accepted grounded answers `120`, revised grounded answers `0`, rejected grounded answers `0`, hard failures `0`, payment collection count `0`, unsupported claim count `0`, and leakage findings `0`. Full-demo readiness is still blocked by `10` route-gap turns across `7` scenarios.
- Why it matters for the thesis: the checkpoint separates answer usefulness from route-policy correctness. Better product facts fix the over-questioning problem, but safe sales autonomy still depends on correct policy actions and call controls.
- Open questions: whether PROD-031 should fix the route gaps in the runtime router, the scenario-specific expectation mapping, or both; and whether a post-fix rerun can make the full grounded scenario set demo-ready.

### 2026-05-09 - PROD-029 grounded full-scenario rerun

- Objective: rerun the exact PROD-027 full-scenario evaluation with the accepted PROD-028 synthetic campaign facts so the project can compare the old question-heavy answers against fact-grounded campaign answers.
- Action taken: added a PROD-029 grounded full-scenario module, runner, validator, product doc, command-map coverage, checkpoint index entry, setup coverage, drift-guard fixture coverage, thesis logs, and generated result/report/scenario/static-HTML artifacts.
- Data used: the unchanged `PROD-027` full scenario set and the fictional `PROD-028` RouteSignal CRM campaign facts. PROD-029 did not copy source transcript text, call providers, call an LLM, read private data, download a dataset, start a server, enable retrieval by default, enable composer hooks by default, collect payment, or change runtime behavior.
- Output created: `docs/product/PROD_029_GROUNDED_FULL_SCENARIO_RERUN.md`, `scripts/prod_029_grounded_full_scenario_rerun.py`, `scripts/run_prod_029_grounded_full_scenario_rerun.py`, `scripts/validate_prod_029_grounded_full_scenario_rerun.py`, `research/experiments/generated/PROD-029-grounded-full-scenario-rerun/result.json`, `research/experiments/generated/PROD-029-grounded-full-scenario-rerun/report.md`, `research/experiments/generated/PROD-029-grounded-full-scenario-rerun/grounded_full_scenario_set.json`, and `research/experiments/generated/PROD-029-grounded-full-scenario-rerun/grounded_full_scenario_trace.html`.
- What was learned: grounding improves answer usefulness on the same scenario set without creating new safety findings. Direct answer rate is `1.0`, knowledge-applicable fact rate is `1.0`, grounded question overuse rate is `0.0`, PROD-027 question overuse rate is `0.7833`, grounded answer win rate is `0.6583`, hard failures are `0`, payment collection count is `0`, unsupported claim count is `0`, and leakage findings are `0`.
- Why it matters for the thesis: this separates the route-policy problem from the product-knowledge problem. Approved campaign facts can reduce over-questioning and improve buyer-facing usefulness, while the remaining route gaps still need their own review before runtime promotion.
- Open questions: which grounded answers should be accepted for demo review, whether the fact-grounded answer layer belongs in a runtime campaign profile, and which unchanged PROD-027 route gaps should become PROD-030 or later policy work.

### 2026-05-09 - PROD-028 synthetic campaign knowledge grounding

- Objective: add a realistic but fictional product brain before demo polishing so the agent can answer buyer questions with approved product facts instead of only asking more questions.
- Action taken: added a PROD-028 synthetic campaign module, runner, validator, product doc, command-map coverage, checkpoint index entry, setup coverage, drift-guard fixture coverage, thesis reference-registry coverage, and generated result/report/campaign/static-HTML artifacts.
- Data used: public CRM/SaaS pricing and product pages from HubSpot, Pipedrive, Salesforce, and Zendesk as inspiration only for packaging patterns. PROD-028 did not copy real company wording, use a real brand as the campaign, call providers, call an LLM, read private data, download a dataset, start a server, enable retrieval by default, enable composer hooks by default, collect payment, or change runtime behavior.
- Output created: `docs/product/PROD_028_SYNTHETIC_CAMPAIGN_KNOWLEDGE_GROUNDING.md`, `scripts/prod_028_synthetic_campaign_knowledge_grounding.py`, `scripts/run_prod_028_synthetic_campaign_knowledge_grounding.py`, `scripts/validate_prod_028_synthetic_campaign_knowledge_grounding.py`, `research/experiments/generated/PROD-028-synthetic-campaign-knowledge-grounding/result.json`, `research/experiments/generated/PROD-028-synthetic-campaign-knowledge-grounding/synthetic_campaign.json`, `research/experiments/generated/PROD-028-synthetic-campaign-knowledge-grounding/report.md`, and `research/experiments/generated/PROD-028-synthetic-campaign-knowledge-grounding/grounded_answer_trace.html`.
- What was learned: product facts materially reduce the question-only behavior. Across `12` same-question comparisons, the grounded candidate reached direct answer rate `1.0`, factual correctness rate `1.0`, price correctness rate `1.0`, question overuse rate `0.0`, safe unknown handling rate `1.0`, unsupported claim count `0`, and payment collection count `0`; the current baseline had baseline question overuse rate `1.0`.
- Why it matters for the thesis: this isolates an important product-learning variable: the agent was over-asking partly because it had no approved product facts. A campaign knowledge layer can improve answer usefulness without relying on live retrieval, provider calls, or unsafe claims.
- Open questions: whether the same grounded answer quality survives multi-turn full-scenario evaluation and whether the grounded answer layer should become a campaign-profile runtime component or remain a demo/evaluation candidate.

### 2026-05-09 - PROD-027 full scenario route evaluation

- Objective: replace one-line trace review with a stronger multi-turn route evaluation that shows whether the local guarded runtime stays on the right sales path across full scenarios.
- Action taken: added a PROD-027 full-scenario module, runner, validator, product doc, command-map coverage, checkpoint index entry, setup coverage, drift-guard fixture coverage, and generated result/report/scenario-set/static-HTML artifacts.
- Data used: the generated `PROD-014` CallCenterEN abstract scenario bank only. PROD-027 did not copy source transcript text, reconstruct source calls, call providers, call an LLM, read private data, download a dataset, start a server, enable retrieval by default, enable composer hooks by default, collect payment, or change runtime behavior.
- Output created: `docs/product/PROD_027_FULL_SCENARIO_ROUTE_EVALUATION.md`, `scripts/prod_027_full_scenario_route_evaluation.py`, `scripts/run_prod_027_full_scenario_route_evaluation.py`, `scripts/validate_prod_027_full_scenario_route_evaluation.py`, `research/experiments/generated/PROD-027-full-scenario-route-evaluation/result.json`, `research/experiments/generated/PROD-027-full-scenario-route-evaluation/report.md`, `research/experiments/generated/PROD-027-full-scenario-route-evaluation/full_scenario_set.json`, and `research/experiments/generated/PROD-027-full-scenario-route-evaluation/full_scenario_route_trace.html`.
- What was learned: the local runtime is safe on this stronger route set, with hard failures `0`, payment collection count `0`, leakage findings `0`, non-sale correctness `1.0`, and safe-close correctness `1.0`. It still has route gaps: route correctness `0.9167`, policy-action correctness `0.9167`, call-control correctness `0.975`, and `13/20` scenarios fully route-passed.
- Why it matters for the thesis: this gives stronger evidence than isolated answer checks because it evaluates multi-turn sales-route behavior, exposes exact decision traces, and preserves source-safety boundaries.
- Open questions: which route misses should become local policy fixes, which are acceptable classifier limits, and whether a polished demo should use this route set or a smaller reviewed subset.

### 2026-05-09 - PROD-026 local demo trace harness

- Objective: convert the accepted `PROD-025` bounded demo readiness packet into a local, inspectable demo trace surface without promoting runtime behavior or enabling live/provider/customer-data paths.
- Action taken: added a PROD-026 trace-harness module, runner, validator, product doc, command-map coverage, checkpoint index entry, setup coverage, drift-guard fixture coverage, and generated result/report/trace-packet/static-HTML artifacts.
- Data used: the generated `PROD-025` bounded demo readiness packet only. PROD-026 did not call providers, call an LLM, read private data, download a dataset, start a server, enable retrieval by default, enable composer hooks by default, collect payment, or change runtime behavior.
- Output created: `docs/product/PROD_026_LOCAL_DEMO_TRACE_HARNESS.md`, `scripts/prod_026_local_demo_trace_harness.py`, `scripts/run_prod_026_local_demo_trace_harness.py`, `scripts/validate_prod_026_local_demo_trace_harness.py`, `research/experiments/generated/PROD-026-local-demo-trace-harness/result.json`, `research/experiments/generated/PROD-026-local-demo-trace-harness/report.md`, `research/experiments/generated/PROD-026-local-demo-trace-harness/trace_packet.json`, and `research/experiments/generated/PROD-026-local-demo-trace-harness/trace_harness.html`.
- What was learned: the project can now show `3` exact synthetic questions and `3` exact agent answers together with policy action, call control, expected outcome, source checkpoint, and safety flags. The harness is ready for manual review while production runtime promotion and live provider demo remain blocked.
- Why it matters for the thesis: this creates a concrete bridge from evaluation evidence to a human-inspectable product demo while preserving the privacy, safety, and no-overclaim boundaries established by earlier checkpoints.
- Open questions: whether the selected three trace cards are the right first demo set and whether the next demo should stay as static trace review or add a separate offline scripted-call simulation.

### 2026-05-09 - PROD-025 bounded demo readiness packet

- Objective: convert the clean `PROD-024` post-fix evidence into a bounded local-demo scope without promoting the runtime or enabling live/provider/customer-data paths.
- Action taken: added a PROD-025 readiness-packet module, runner, validator, product doc, command-map coverage, checkpoint index entry, setup coverage, drift-guard fixture coverage, and generated result/report artifacts.
- Data used: the generated `PROD-024` post-fix result only. PROD-025 did not call providers, call an LLM, read private data, download a dataset, enable retrieval by default, enable composer hooks by default, or change runtime behavior.
- Output created: `docs/product/PROD_025_BOUNDED_DEMO_READINESS_PACKET.md`, `scripts/prod_025_bounded_demo_readiness_packet.py`, `scripts/run_prod_025_bounded_demo_readiness_packet.py`, `scripts/validate_prod_025_bounded_demo_readiness_packet.py`, `research/experiments/generated/PROD-025-bounded-demo-readiness-packet/result.json`, and `research/experiments/generated/PROD-025-bounded-demo-readiness-packet/report.md`.
- What was learned: the project is ready for a bounded local trace-only demo harness. The allowed modes are local trace replay, offline scripted-call simulation, and human review packet. Production runtime promotion, live provider demo, customer data, payment handling, retrieval defaults, and composer-hook defaults remain blocked.
- Why it matters for the thesis: the work now has a concrete product-demo boundary that can show exact question/answer behavior and decision traces without overstating readiness or weakening privacy/provider boundaries.
- Open questions: whether the local trace harness should be a CLI packet first, a small static HTML report, or both.

### 2026-05-09 - PROD-024 live-shaped post-fix rerun

- Objective: rerun the full live-shaped dialogue-policy path after `PROD-023` to verify the local runtime-policy and call-control fix across all turns, not only the exact gap packet.
- Action taken: added a PROD-024 post-fix rerun module, runner, validator, product doc, command-map coverage, checkpoint index entry, setup coverage, drift-guard fixture coverage, and generated result/report artifacts.
- Data used: the generated `PROD-023` result and the existing synthetic `PROD-021` live-shaped case file. PROD-024 did not call providers, call an LLM, read private data, download a dataset, enable retrieval by default, or enable composer hooks by default.
- Output created: `docs/product/PROD_024_LIVE_SHAPED_POST_FIX_RERUN.md`, `scripts/prod_024_live_shaped_post_fix_rerun.py`, `scripts/run_prod_024_live_shaped_post_fix_rerun.py`, `scripts/validate_prod_024_live_shaped_post_fix_rerun.py`, `research/experiments/generated/PROD-024-live-shaped-post-fix-rerun/result.json`, and `research/experiments/generated/PROD-024-live-shaped-post-fix-rerun/report.md`.
- What was learned: across `7` calls and `19` customer turns, policy action correctness, call-control correctness, protected context preservation, non-sale correctness, safe-close correctness, and state reference completeness are all `1.0`, with `0` hard failures, `0` payment collection findings, and `0` leakage findings. The post-fix gate passes while the legacy PROD-021 hook-gain gate stays false because it measured a different hypothesis.
- Why it matters for the thesis: the project now has full live-shaped evidence that the local runtime policy can handle the previously failed states without relying on composer-hook gain. This permits bounded demo-readiness planning, not production runtime promotion.
- Open questions: what the smallest bounded demo should include, which exact traces should be visible, and which provider/live steps remain blocked behind manual review.

### 2026-05-09 - PROD-023 runtime-policy and call-control fix

- Objective: close the exact `PROD-022` policy-action and call-control misses without changing retrieval defaults, composer-hook defaults, provider behavior, or dataset scope.
- Action taken: added a PROD-023 runtime-policy/call-control module, runner, validator, product doc, command-map coverage, checkpoint index entry, setup coverage, drift-guard fixture coverage, and generated result/report artifacts.
- Data used: the generated `PROD-022` gap packet and the existing synthetic `PROD-021` live-shaped case file. PROD-023 did not call providers, call an LLM, read private data, download a dataset, enable retrieval by default, or enable composer hooks by default.
- Output created: `docs/product/PROD_023_RUNTIME_POLICY_CALL_CONTROL_FIX.md`, `scripts/prod_023_runtime_policy_call_control_fix.py`, `scripts/run_prod_023_runtime_policy_call_control_fix.py`, `scripts/validate_prod_023_runtime_policy_call_control_fix.py`, `research/experiments/generated/PROD-023-runtime-policy-call-control-fix/result.json`, and `research/experiments/generated/PROD-023-runtime-policy-call-control-fix/report.md`.
- What was learned: the narrow local runtime-policy fix closes `10/10` policy-action misses and `3/3` call-control misses from PROD-022, with policy action correctness `1.0`, call-control correctness `1.0`, protected context preservation `1.0`, non-sale correctness `1.0`, safe-close correctness `1.0`, hard failures `0`, payment collection count `0`, and leakage findings `0`.
- Why it matters for the thesis: the project now separates policy/call-control correctness from hook wording quality. Composer hooks can stay opt-in, but the next claim must come from a full post-fix live-shaped rerun rather than from the narrow gap packet alone.
- Open questions: whether `PROD-024-live-shaped-post-fix-rerun` preserves the same clean metrics across the full evidence path and whether hooks should stay as-is, be revised, be discarded, or become demo-only opt-in.

### 2026-05-09 - PROD-022 PROD-021 review gap packet

- Objective: convert the failed `PROD-021` live-shaped gate into a compact product-review packet with exact gap turns and narrow implementation targets.
- Action taken: added a PROD-022 gap-packet module, runner, validator, product doc, command-map coverage, checkpoint index entry, setup coverage, drift-guard fixture coverage, and generated result/report artifacts.
- Data used: the generated `PROD-021` result artifact only. PROD-022 did not call providers, call an LLM, read private data, download a dataset, change runtime behavior, enable retrieval by default, or enable composer hooks by default.
- Output created: `docs/product/PROD_022_PROD_021_REVIEW_GAP_PACKET.md`, `scripts/prod_022_prod_021_review_gap_packet.py`, `scripts/run_prod_022_prod_021_review_gap_packet.py`, `scripts/validate_prod_022_prod_021_review_gap_packet.py`, `research/experiments/generated/PROD-022-prod-021-review-gap-packet/result.json`, and `research/experiments/generated/PROD-022-prod-021-review-gap-packet/report.md`.
- What was learned: PROD-022 found `10` gap turns in PROD-021: `10` policy action misses and `3` call-control misses, with `0` protected-context gaps, `0` hard failures, and `0` leakage findings. The fix targets are runtime policy router specialization, sale-ready call-control detection, procurement-review continuation guarding, and keeping composer hooks opt-in.
- Why it matters for the thesis: the project now has a precise bridge from evaluation failure to implementation scope. The evidence says hook wording improved some turns, but policy routing and call-control must be corrected before runtime promotion.
- Open questions: whether a narrow `PROD-023` runtime-policy/call-control patch can close the exact gaps without weakening protected contexts, non-sale correctness, safe-close correctness, or default-off retrieval boundaries.

### 2026-05-09 - PROD-021 live-shaped dialogue-policy simulation

- Objective: test whether the `PROD-020` opt-in runtime composer-hook gain survives live-shaped, multi-turn dialogue flow against the `PROD-011` hardened dialogue-policy expectations.
- Action taken: added a PROD-021 simulation module, runner, validator, product doc, command-map coverage, checkpoint index entry, setup coverage, fixed live-shaped case file, and generated result/report artifacts.
- Data used: synthetic live-shaped customer turns built from project-owned checkpoint abstractions, plus the generated `PROD-020` result and `PROD-011` policy case as prior evidence. PROD-021 did not read raw CallCenterEN files, download data, call providers, call an LLM, use embeddings, write vectors, read private data, store raw source text, enable retrieval by default, or enable composer hooks by default.
- Output created: `docs/product/PROD_021_LIVE_SHAPED_DIALOGUE_POLICY_SIMULATION.md`, `scripts/prod_021_live_shaped_dialogue_policy_simulation.py`, `scripts/run_prod_021_live_shaped_dialogue_policy_simulation.py`, `scripts/validate_prod_021_live_shaped_dialogue_policy_simulation.py`, `research/experiments/cases/prod-021-live-shaped-dialogue-policy-simulation.json`, `research/experiments/generated/PROD-021-live-shaped-dialogue-policy-simulation/result.json`, and `research/experiments/generated/PROD-021-live-shaped-dialogue-policy-simulation/report.md`.
- What was learned: across `7` calls and `19` customer turns, opt-in hooks improved `4` turns, opt-in total score was `112` versus retrieval-only score `98`, opt-in won `4` turns, retrieval-only won `0`, and `15` tied. Safety stayed clean: protected context preservation `1.0`, state reference completeness `1.0`, non-sale correctness `1.0`, safe-close correctness `1.0`, hard failure rate `0.0`, payment collection count `0`, and leakage finding count `0`. The gate did not pass because policy action correctness was `0.4737` and call-control correctness was `0.8421`.
- Why it matters for the thesis: PROD-021 separates hook-wording quality from stateful runtime-policy readiness. The hooks remain useful as an opt-in candidate, but the project cannot claim runtime promotion until policy-action and call-control gaps are closed in live-shaped multi-turn flow.
- Open questions: which narrow runtime-policy changes close the observed policy-action and call-control misses without weakening protected-context behavior, default-off retrieval, or no-provider/no-private-data boundaries.

### 2026-05-09 - PROD-020 naturalized customer-turn evaluation

- Objective: test whether the `PROD-019` opt-in runtime composer-hook gain survives when rubric-like generated customer turns are rewritten into natural customer wording.
- Action taken: added a PROD-020 naturalization module, runner, validator, product doc, command-map coverage, checkpoint index entry, setup coverage, and generated result/report artifacts over the fixed PROD-015 comparison output with the PROD-019 gate as prior evidence.
- Data used: the generated `PROD-015` result artifact and the generated `PROD-019` gate result only. PROD-020 did not read raw CallCenterEN files, download data, call providers, call an LLM, use embeddings, write vectors, read private data, store raw source text, enable retrieval by default, or enable composer hooks by default.
- Output created: `docs/product/PROD_020_NATURALIZED_CUSTOMER_TURN_EVALUATION.md`, `scripts/prod_020_naturalized_customer_turn_evaluation.py`, `scripts/run_prod_020_naturalized_customer_turn_evaluation.py`, `scripts/validate_prod_020_naturalized_customer_turn_evaluation.py`, `research/experiments/generated/PROD-020-naturalized-customer-turn-evaluation/result.json`, and `research/experiments/generated/PROD-020-naturalized-customer-turn-evaluation/report.md`.
- What was learned: across `180` fixed turns, `120` source turns were rubric-like and `123` questions were changed into natural wording. Runtime prompts had `0` rubric-token findings, source-pattern refs were preserved for `180/180` rows, and expected outcomes were preserved for `180/180` rows. With retrieval and composer hooks explicitly enabled, `107` answers received hooks without evaluation-label input. Hooked total score was `1065` versus baseline score `734`, with `107` hooked wins, `0` baseline wins, and `73` ties. Safety stayed clean: hard failures `0`, leakage findings `0`, payment collection findings `0`, expected outcome correctness `180/180`, non-sale correctness `1.0`, safe-close correctness `1.0`, and safety gate pass count `180/180`.
- Why it matters for the thesis: PROD-020 closes the main PROD-019 evidence weakness by showing that the hook gain was not only caused by obvious rubric tokens such as `too_expensive` or `timeline_question` in runtime prompts. It still remains opt-in candidate evidence, not default retrieval evidence.
- Open questions: whether the naturalized hook gain survives live-shaped multi-turn simulation against the PROD-011 hardened dialogue policy, where state continuity, call-control decisions, protected contexts, and turn order matter more than single-turn wording.

### 2026-05-09 - PROD-019 guarded runtime composer hooks

- Objective: move the `PROD-018` offline hook idea into the actual guarded response composer behind an explicit opt-in flag, while proving default behavior stays unchanged.
- Action taken: added a runtime composer-hook helper, wired `--composer-hooks-enabled` into `generate_guarded_response.py`, added a PROD-019 module, runner, validator, product doc, command-map coverage, checkpoint index entry, setup coverage, and generated result/report artifacts over the fixed PROD-015 comparison output.
- Data used: the generated `PROD-015` result artifact and the generated `PROD-018` gate result only. PROD-019 did not read raw CallCenterEN files, download data, call providers, call an LLM, use embeddings, write vectors, read private data, store source text, enable retrieval by default, or enable composer hooks by default.
- Output created: `docs/product/PROD_019_GUARDED_RUNTIME_COMPOSER_HOOKS.md`, `scripts/runtime_composer_hooks.py`, `scripts/prod_019_guarded_runtime_composer_hooks.py`, `scripts/run_prod_019_guarded_runtime_composer_hooks.py`, `scripts/validate_prod_019_guarded_runtime_composer_hooks.py`, `research/experiments/generated/PROD-019-guarded-runtime-composer-hooks/result.json`, and `research/experiments/generated/PROD-019-guarded-runtime-composer-hooks/report.md`.
- What was learned: on the same `180` fixed PROD-015 turns, default-off output drift was `0`, proving the new hook flag does not alter the existing guarded response path. With both retrieval and composer hooks explicitly enabled, `98` answers received runtime hooks without evaluation-label input. Hooked total score was `916` versus current retrieval score `663`, with `92` hooked wins, `0` current wins, and `88` ties. Safety stayed clean: hard failures `0`, leakage findings `0`, payment collection findings `0`, non-sale correctness `1.0`, safe-close correctness `1.0`, and safety gate pass count `180/180`.
- Why it matters for the thesis: PROD-019 turns the composer-improvement claim from an offline label-aware patch into real guarded-composer evidence while preserving the default-off runtime boundary. It still does not justify default retrieval because many evaluated turns use rubric-like generated wording that can expose easy textual signals.
- Open questions: whether the opt-in runtime hooks still improve answers when rubric-like customer prompts are rewritten into natural customer language and when live-shaped multi-turn dialogue policy is tested.

### 2026-05-09 - PROD-018 CallCenterEN composer-hook test

- Objective: test whether a narrow offline composer-hook layer can turn `PROD-015` retrieved-but-not-used hints into safer, more specific answers before changing runtime behavior.
- Action taken: added a PROD-018 product doc, offline composer-hook module, runner, validator, command-map coverage, checkpoint index entry, setup coverage, and generated result/report artifacts over the fixed PROD-015 comparison output.
- Data used: the generated `PROD-015` result artifact only. PROD-018 did not read raw CallCenterEN files, download data, call providers, call an LLM, use embeddings, write vectors, read private data, store source text, change runtime behavior, or enable retrieval by default.
- Output created: `docs/product/PROD_018_CALLCENTEREN_COMPOSER_HOOK_TEST.md`, `scripts/callcenteren_composer_hook_test.py`, `scripts/run_prod_018_callcenteren_composer_hook_test.py`, `scripts/validate_prod_018_callcenteren_composer_hook_test.py`, `research/experiments/generated/PROD-018-callcenteren-composer-hook-test/result.json`, and `research/experiments/generated/PROD-018-callcenteren-composer-hook-test/report.md`.
- What was learned: on the same `180` fixed PROD-015 turns, the offline hook layer applied to `174` retrieved-not-used answers and preserved the `3` existing influenced answers. Hooked total score was `1421` versus current retrieval score `663` and old runtime score `652`; hooked answers won `174` turns versus current retrieval and `177` turns versus old runtime, with old runtime winning `0`. Safety stayed clean: hard failures `0`, leakage findings `0`, payment collection findings `0`, non-sale correctness `1.0`, safe-close correctness `1.0`, and safety gate pass count `180/180`.
- Why it matters for the thesis: PROD-018 shows the no-gain problem was mainly composition, not matching. However, the evidence is still offline and label-aware, so it justifies a red-first guarded runtime-composer candidate test, not a default retrieval promotion or commercial runtime claim.
- Open questions: whether `PROD-019` can reproduce the PROD-018 gains through the actual guarded response composer without relying on evaluation labels, weakening generic fallback safety, or contaminating commercial runtime prompts with CallCenterEN-derived text.

### 2026-05-09 - PROD-017 CallCenterEN specificity scoring

- Objective: add an evaluation-only scorer that can distinguish safe-generic answers from safe-specific objection-fit answers on the unchanged `PROD-015` rows.
- Action taken: added a PROD-017 product doc, specificity-scoring module, runner, validator, command-map coverage, checkpoint index entry, setup coverage, and generated result/report artifacts over the fixed PROD-015 comparison output.
- Data used: the generated `PROD-015` result artifact only. PROD-017 did not read raw CallCenterEN files, download data, call providers, call an LLM, use embeddings, write vectors, read private data, store source text, or change runtime behavior.
- Output created: `docs/product/PROD_017_CALLCENTEREN_SPECIFICITY_SCORING.md`, `scripts/callcenteren_specificity_scoring.py`, `scripts/run_prod_017_callcenteren_specificity_scoring.py`, `scripts/validate_prod_017_callcenteren_specificity_scoring.py`, `research/experiments/generated/PROD-017-callcenteren-specificity-scoring/result.json`, and `research/experiments/generated/PROD-017-callcenteren-specificity-scoring/report.md`.
- What was learned: PROD-017 confirms the scoring blind spot. PROD-015 treated all `180` turns as ties, but specificity scoring gives retrieval `3` wins, old runtime `0` wins, and `177` ties, with old total score `652`, retrieval total score `663`, and score delta `11`. All `3` influenced retrieval answers win under the new scorer, but only `3` answers changed at all. Absolute quality gap count is `177`, generic old-answer rate is `1.0`, and generic retrieval-answer rate is `0.9833`.
- Why it matters for the thesis: the project now has a more sensitive fixed-case evaluator before editing the runtime composer. The result is not broad retrieval-improvement evidence; it is evidence that safe-specific answers can be measured and that composer changes must increase the number of non-generic answers before runtime claims are justified.
- Open questions: whether `PROD-018` should start with only authority/decision-maker hooks, or include a small set of price, callback, trust repair, support handoff, and cancellation-boundary hooks in one narrow fixed-case composer test.

### 2026-05-09 - PROD-016 CallCenterEN retrieval no-gain diagnosis

- Objective: explain why the `PROD-015` retrieval-enabled runtime tied the old retrieval-disabled runtime before making any runtime or retrieval-promotion change.
- Action taken: added a PROD-016 product doc, diagnosis module, runner, validator, command-map coverage, checkpoint index entry, setup coverage, and generated result/report artifacts over the fixed PROD-015 output.
- Data used: the generated `PROD-015` result artifact only. PROD-016 did not read raw CallCenterEN files, download data, call providers, call an LLM, use embeddings, write vectors, read private data, store source text, or change runtime behavior.
- Output created: `docs/product/PROD_016_CALLCENTEREN_RETRIEVAL_NO_GAIN_DIAGNOSIS.md`, `scripts/callcenteren_retrieval_no_gain_diagnosis.py`, `scripts/run_prod_016_callcenteren_retrieval_no_gain_diagnosis.py`, `scripts/validate_prod_016_callcenteren_retrieval_no_gain_diagnosis.py`, `research/experiments/generated/PROD-016-callcenteren-retrieval-no-gain-diagnosis/result.json`, and `research/experiments/generated/PROD-016-callcenteren-retrieval-no-gain-diagnosis/report.md`.
- What was learned: across `180` analyzed turns, retrieval matching was not the main bottleneck. Matching success was `1.0` and no-match rate was `0.0`, but `174` turns were retrieved-not-used, `177` answers were unchanged, only `3` answers changed, and all `3` changed answers still tied the old runtime. The diagnosis flags composer influence gap and scoring blind spot as high-severity, plus runtime classifier mismatch (`180/180` unknown-runtime-signal, `120` rubric-like prompts) and campaign domain mismatch (`8` domains through one B2B software campaign) as medium-severity.
- Why it matters for the thesis: this prevents the project from mistaking safe retrieval matching for a better sales agent. It also creates a defensible sequence: improve the evaluator's specificity/objective-fit scoring first, then test composer changes on fixed cases, and only then consider larger full-bank evidence.
- Open questions: whether `PROD-017` should only add evaluation scoring over the fixed PROD-015 rows, or also create a small natural-language scenario verbalization check as a separate later checkpoint.

### 2026-05-09 - PROD-015 CallCenterEN runtime comparison

- Objective: compare the old retrieval-disabled runtime and the opt-in retrieval-enabled runtime on the same `PROD-014` generated CallCenterEN scenario prompts.
- Action taken: added a PROD-015 product doc, runtime-comparison module, runner, validator, command-map coverage, checkpoint index entry, setup coverage, and generated result/report artifacts with exact customer questions, exact old-runtime answers, exact retrieval-runtime answers, and selected decision traces.
- Data used: the project-owned `PROD-014` scenario bank generated from abstract `PROD-013` CallCenterEN pattern IDs. The default run scanned `5,000` source sentences transiently from ignored local CallCenterEN ZIP files for leakage checks. No source sentence text, raw transcript body, company-specific wording, agent/customer names, private data, provider output, LLM output, embedding, vector database record, commercial runtime prompt text, or commercial model-training material was stored.
- Output created: `docs/product/PROD_015_CALLCENTEREN_RUNTIME_COMPARISON.md`, `scripts/callcenteren_runtime_comparison.py`, `scripts/run_prod_015_callcenteren_runtime_comparison.py`, `scripts/validate_prod_015_callcenteren_runtime_comparison.py`, `research/experiments/generated/PROD-015-callcenteren-runtime-comparison/result.json`, and `research/experiments/generated/PROD-015-callcenteren-runtime-comparison/report.md`.
- What was learned: on the default stratified slice of `60` scenarios and `180` turns, both runtimes scored `810`, retrieval won `0` turns, old runtime won `0` turns, and `180` turns tied. Retrieval influenced only `3` responses, was blocked `3` times, and was retrieved-but-not-used `174` times. Safety stayed clean: hard failures `0`, leakage findings `0`, non-sale correctness `120/120`, safe-close correctness `60/60`, discovery-before-close `180/180`, and emotional handling `180/180`.
- Why it matters for the thesis: the result prevents overclaiming from the smaller PROD-012 retrieval win. It shows that retrieval can remain safe on a larger generated bank, but current scoring and composition do not yet prove a quality gain over the old runtime.
- Open questions: whether to strengthen retrieval query/composition/scoring first, run the full `240`-scenario bank as a baseline, or move to live-shaped dialogue-policy simulation before trying another retrieval improvement.

### 2026-05-09 - PROD-014 CallCenterEN scenario bank

- Objective: turn the extracted `PROD-013` CallCenterEN pattern bank into a clean, leakage-tested scenario bank for old-runtime versus retrieval-runtime evaluation.
- Action taken: added a PROD-014 product doc, scenario-bank module, runner, validator, command-map coverage, checkpoint index entry, setup coverage, and generated scenario-bank/report artifacts.
- Data used: the abstract `PROD-013` pattern bank generated from approved local CallCenterEN files. The run also scanned `5,000` source sentences transiently from ignored local CallCenterEN ZIP files for leakage checks. No source sentence text, raw transcript body, company-specific wording, agent/customer names, private data, provider output, LLM output, embedding, vector database record, commercial runtime prompt text, or commercial model-training material was stored.
- Output created: `docs/product/PROD_014_CALLCENTEREN_SCENARIO_BANK.md`, `scripts/callcenteren_scenario_bank.py`, `scripts/run_prod_014_callcenteren_scenario_bank.py`, `scripts/validate_prod_014_callcenteren_scenario_bank.py`, `research/experiments/generated/PROD-014-callcenteren-scenario-bank/scenario-bank.json`, and `research/experiments/generated/PROD-014-callcenteren-scenario-bank/report.md`.
- What was learned: the generated bank contains `240` scenarios, `720` customer turns, `240` unique scenario recipes, `2,502` abstract source-pattern references, `10` source-pattern categories, and `0` leakage findings after a transient scan of `5,000` local source sentences. It covers `sale_eligible`, `price_objection`, `callback_request`, `cancellation_boundary`, `support_handoff`, and `trust_repair`, with scenario quality `1.0`, leakage failure rate `0.0`, safe-close coverage `0.3375`, non-sale boundary coverage `0.6625`, and emotion-label coverage `1.0`. The output is an expanded evaluation bank, not one scenario per source call.
- Why it matters for the thesis: PROD-014 moves the project from hand-written seed scenarios toward a larger, auditably pattern-derived test bank while preserving the non-commercial dataset boundary and making hard failure, non-sale correctness, leakage, safe close, and emotional handling measurable in the next runtime comparison.
- Open questions: whether `PROD-015` should compare old core versus opt-in retrieval on all `240` generated scenarios first, or start with a smaller stratified slice for faster iteration before expanding to the full bank.

### 2026-05-09 - PROD-013 CallCenterEN abstract pattern extraction

- Objective: replace hand-written CallCenterEN-style pattern assumptions with a local extractor that can build a clean pattern bank from approved local dataset files.
- Action taken: added a PROD-013 product doc, extraction module, runner, validator, setup coverage, command-map coverage, checkpoint index entry, source-boundary documentation, full-run bounded extraction support, and a local download manifest with source file hashes.
- Data used: after explicit approval, the public CallCenterEN ZIP files were downloaded to ignored local storage under `data/external/callcenteren/raw/`. The validation harness uses a temporary `.tmp` fixture only to prove the extractor shape. No provider call, private data read, customer audio, raw transcript body storage, commercial model training, or commercial runtime prompt contamination is used.
- Output created: `docs/product/PROD_013_CALLCENTEREN_PATTERN_EXTRACTION.md`, `scripts/callcenteren_pattern_extraction.py`, `scripts/run_prod_013_callcenteren_pattern_extraction.py`, `scripts/validate_prod_013_callcenteren_pattern_extraction.py`, `research/experiments/generated/PROD-013-callcenteren-pattern-extraction/pattern-bank.json`, `research/experiments/generated/PROD-013-callcenteren-pattern-extraction/report.md`, and `research/experiments/generated/PROD-013-callcenteren-pattern-extraction/download-manifest.json`.
- What was learned: the full bounded extraction scanned `95,946` source JSON payloads, parsed `95,934` conversations, and produced `4,313,595` pseudo-turns with `0` leakage findings. The real files often expose word-level timestamps without reliable speaker labels, so PROD-013 marks speaker roles as inferred for pattern mining only, not ground-truth diarization. The inference now uses role-specific language signals before file-direction fallback, distinguishing agent-like disclosures, permission checks, discovery, offer, repair, and handoff language from customer-like price questions, objections, busy/wrong-person boundaries, cancellation, support issues, and callback/info requests. The project now has a deterministic extraction contract for opening styles, customer intents, objections, emotion/tone transitions, persuasion tactics, discovery questions, conversation stages, close attempts, safety boundaries, timing/speech-naturalness signals, domain patterns, customer personas, scenario templates, and agent mistake labels without storing exact scripts.
- Why it matters for the thesis: PROD-013 makes the real-call-pattern grounding auditable and repeatable, while preserving the non-commercial dataset boundary and leakage discipline needed before broader scenario generation.
- Open questions: when PROD-012 should be switched from its hand-written seed patterns to the extracted PROD-013 bank, and whether a later diarization-quality review is needed before treating turn-role statistics as strong evidence.

### 2026-05-09 - PROD-012 CallCenterEN scenario evaluation

- Objective: strengthen the real-call-pattern evaluation lane by using CallCenterEN / AIxBlock as pattern grounding for fixed synthetic scenarios, then compare old core behavior against opt-in RAG-018 retrieval.
- Action taken: added a PROD-012 product doc, case file, scenario-evaluation module, runner, validator, generated result/report, setup coverage, command-map coverage, checkpoint index entry, and source-boundary documentation.
- Data used: six project-owned synthetic scenarios and twelve turns grounded in nine CallCenterEN-style source patterns. The source reference is the Hugging Face `AIxBlock/92k-real-world-call-center-scripts-english` dataset and arXiv paper, with no dataset download required by default. No provider call, private data read, customer audio, raw transcript body storage, vector database, embedding provider, LLM reranker, commercial model training, or commercial runtime prompt contamination was used.
- Output created: `docs/product/PROD_012_CALLCENTEREN_SCENARIO_EVALUATION.md`, `scripts/callcenteren_scenario_evaluation.py`, `scripts/run_prod_012_callcenteren_scenario_evaluation.py`, `scripts/validate_prod_012_callcenteren_scenario_evaluation.py`, `research/experiments/cases/prod-012-callcenteren-scenario-evaluation.json`, and `research/experiments/generated/PROD-012-callcenteren-scenario-evaluation/`.
- What was learned: on the fixed CallCenterEN-grounded synthetic scenarios, the retrieval version scored `14` versus old core score `5`, won `5` quality-scored turns, old core won `0`, protected turns were preserved `5/5`, hard failure rate stayed `0.0`, leakage failure rate stayed `0.0`, and non-sale correctness stayed `1.0`.
- Why it matters for the thesis: PROD-012 tests retrieval improvement against scenarios grounded in real-world call-center patterns while preserving leakage controls and non-commercial dataset boundaries.
- Open questions: whether the same improvement survives a larger locally downloaded CallCenterEN ZIP scan and later human review without making retrieval default.

### 2026-05-09 - PROD-011 dialogue-policy hardening

- Objective: turn PROD-010 long-call objection evidence into a compact policy-action layer before any live-runtime promotion.
- Action taken: added a PROD-011 product doc, dialogue-policy module, runner, validator, derived case file, generated report/result, command-map coverage, setup coverage, drift coverage, roadmap update, and decision-log entry.
- Data used: seven synthetic PROD-010 long-call scenarios and forty-nine turns across telecom, B2B software, insurance service, medical equipment, membership service, home service, and retail product scenarios. No provider call, private data read, customer audio, transcript body storage, dataset download, payment handling, checkout handling, vector database, embedding provider, commercial runtime prompt contamination, or runtime behavior change was used.
- Output created: `docs/brain/PROD_011_DIALOGUE_POLICY_HARDENING.md`, `scripts/dialogue_policy_hardening.py`, `scripts/run_prod_011_dialogue_policy_hardening.py`, `scripts/validate_prod_011_dialogue_policy_hardening.py`, `research/experiments/cases/prod-011-dialogue-policy-hardening.json`, and `research/experiments/generated/PROD-011-dialogue-policy-hardening/`.
- What was learned: the hardened policy layer preserved the targets: hard failure rate `0.0`, safe close rate `1.0`, non-sale correctness `1.0`, policy action correctness `1.0`, blocked action avoidance `1.0`, objection stack preservation `1.0`, state-reference completeness `1.0`, call-control correctness `1.0`, and max latency `16 ms`.
- Why it matters for the thesis: PROD-011 separates state-packet generation from policy-action selection, making the full-sale pivot easier to evaluate and audit before any live-shaped runtime test.
- Open questions: whether the same hardened policy remains stable when tested against fuller transcript simulations rather than compact turn metadata.

### 2026-05-09 - PROD-010 long-call universal objections

- Objective: stress the generated BRAIN-002 packet path on longer calls with repeated universal buyer objections before any dialogue-policy or runtime-promotion work.
- Action taken: added a PROD-010 product doc, long-call case file, runner, validator, generated report/result, command-map coverage, setup coverage, drift coverage, roadmap update, and decision-log entry. The generated packet module now carries turn position, total turn count, and the call-level objection stack through each BRAIN-002 packet.
- Data used: seven synthetic calls and forty-nine turns across telecom, B2B software, insurance service, medical equipment, membership service, home service, and retail product scenarios. The objection stack covers price, competitor comparison, timing, authority, procurement, privacy, claim boundary, technical risk, anger, cancellation, support, and trust. No provider call, private data read, customer audio, transcript body storage, dataset download, payment handling, checkout handling, vector database, embedding provider, commercial runtime prompt contamination, or runtime behavior change was used.
- Output created: `docs/product/PROD_010_LONG_CALL_UNIVERSAL_OBJECTIONS.md`, `scripts/run_prod_010_long_call_universal_objections.py`, `scripts/validate_prod_010_long_call_universal_objections.py`, `research/experiments/cases/prod-010-long-call-universal-objections.json`, and `research/experiments/generated/PROD-010-long-call-universal-objections/`.
- What was learned: the generated packet path preserved the long-call targets: safe close rate `1.0`, hard failure rate `0.0`, non-sale correctness `1.0`, state packet completeness `1.0`, objection boundary correctness `1.0`, long-call state continuity `1.0`, close-attempt quality `0.9214`, and call-control correctness `1.0`.
- Why it matters for the thesis: PROD-010 makes the full-sale pivot more credible by testing whether the agent can keep buyer-state and safety boundaries stable across longer multi-objection conversations, not only short fixed calls.
- Open questions: how to turn the fixture-proven objection-state behavior into a hardened dialogue policy without overfitting to synthetic turn labels.

### 2026-05-09 - PROD-009 cross-domain generated gauntlet

- Objective: expand the generated BRAIN-002 full-call packet path beyond the SD-card/storage slice while preserving safety, non-sale correctness, and packet completeness.
- Action taken: added a PROD-009 product doc, cross-domain case file, runner, validator, generated report/result, command-map coverage, setup coverage, drift coverage, roadmap update, and decision-log entry. The existing generated packet module now supports cross-domain final-turn signals while preserving PROD-008 behavior.
- Data used: ten synthetic calls and twenty-eight turns across retail product, telecom, B2B software, insurance service, medical equipment, home service, membership service, and automotive service. Each call uses at least three source-pattern IDs from the PROD-006 pattern bank. No provider call, private data read, customer audio, transcript body storage, dataset download, payment handling, checkout handling, vector database, embedding provider, commercial runtime prompt contamination, or runtime behavior change was used.
- Output created: `docs/product/PROD_009_CROSS_DOMAIN_GENERATED_GAUNTLET.md`, `scripts/run_prod_009_cross_domain_generated_gauntlet.py`, `scripts/validate_prod_009_cross_domain_generated_gauntlet.py`, `research/experiments/cases/prod-009-cross-domain-generated-gauntlet.json`, and `research/experiments/generated/PROD-009-cross-domain-generated-gauntlet/`.
- What was learned: the generated packet path preserved targets across the broader first-pass domain set: safe close rate `1.0`, hard failure rate `0.0`, non-sale correctness `1.0`, state packet completeness `1.0`, close-attempt quality `0.915`, and call-control correctness `1.0`.
- Why it matters for the thesis: PROD-009 reduces the risk that the full-sale result is only an SD-card/storage artifact by testing the same generated BRAIN-002 contract across multiple domain and non-sale patterns.
- Open questions: whether harder universal objections and longer calls expose failures that the current first-pass cross-domain cases do not catch.

### 2026-05-09 - PROD-008 generated full-call packets

- Objective: remove the fixture-scored packet shortcut from PROD-007 and test whether local runtime-style logic can create complete BRAIN-002 packets from every call turn.
- Action taken: added a PROD-008 product doc, generated-packet module, runner, validator, fixed case file, generated report/result, command-map coverage, setup coverage, drift coverage, roadmap update, and decision-log entry.
- Data used: the same six synthetic PROD-006-style SD-card/storage call shapes and thirteen turns used for the first full-call gauntlet, with generated BRAIN-002 packet fields derived from turn intent and signal metadata. No provider call, private data read, customer audio, transcript body storage, dataset download, payment handling, checkout handling, vector database, embedding provider, or runtime behavior change was used.
- Output created: `docs/product/PROD_008_GENERATED_FULL_CALL_PACKETS.md`, `scripts/generated_full_call_packets.py`, `scripts/run_prod_008_generated_full_call_packets.py`, `scripts/validate_prod_008_generated_full_call_packets.py`, `research/experiments/cases/prod-008-generated-full-call-packets.json`, and `research/experiments/generated/PROD-008-generated-full-call-packets/`.
- What was learned: the generated packet path preserved the PROD-007 decision gains: safe close rate `1.0`, hard failure rate `0.0`, non-sale correctness `1.0`, state packet completeness `1.0`, close-attempt quality `0.92`, and call-control correctness `1.0`.
- Why it matters for the thesis: PROD-008 makes the full-sale pivot less dependent on fixture answers by showing that the BRAIN-002 contract can be generated turn by turn before expanding scenario coverage.
- Open questions: whether the generated packet logic holds across mixed domains, harder universal objections, and longer calls without sacrificing non-sale correctness.

### 2026-05-09 - PROD-007 full-call gauntlet

- Objective: run the first fixed full-call comparison between the older pre-full-sale core and the BRAIN-002/full-sale candidate before broad runtime changes.
- Action taken: added a PROD-007 gauntlet doc, fixed-case file, local scorer, runner, validator, generated report/result, command-map coverage, setup coverage, drift coverage, roadmap update, and decision-log entry.
- Data used: six synthetic PROD-006-style SD-card/storage calls with thirteen fixed turns covering sale eligibility, unclear compatibility, support-only context, complaint recovery, human escalation, and stop request. No provider call, private data read, customer audio, transcript body storage, dataset download, payment handling, checkout handling, vector database, embedding provider, or runtime behavior change was used.
- Output created: `docs/product/PROD_007_FULL_CALL_GAUNTLET.md`, `scripts/full_call_gauntlet.py`, `scripts/run_prod_007_full_call_gauntlet.py`, `scripts/validate_prod_007_full_call_gauntlet.py`, `research/experiments/cases/prod-007-full-call-gauntlet.json`, and `research/experiments/generated/PROD-007-full-call-gauntlet/`.
- What was learned: the BRAIN-002 candidate improves the fixture-level decision metrics against the older core: safe close rate `1.0` versus `0.0`, hard failure rate `0.0` versus `0.3333`, non-sale correctness `1.0` versus `0.4`, close-attempt quality `0.92` versus `0.55`, and call-control correctness `1.0` versus `0.5`.
- Why it matters for the thesis: PROD-007 makes the full-sale pivot measurable as call-level decisions rather than only response text, while still preserving the warning that fixture-scored evidence is not live product evidence.
- Open questions: whether the next generated-packet test can produce the same BRAIN-002 fields from runtime turn logic instead of pre-scored candidate packets, and how many additional domains are needed before the thesis can claim generalization.

### 2026-05-09 - BRAIN-002 runtime state schema

- Objective: convert the BRAIN-001 architecture and project-wide premortem result into a strict per-turn runtime state packet before building the full-call gauntlet.
- Action taken: added a BRAIN-002 product doc, schema case file, local schema builder, runner, validator, generated report/result, setup coverage, drift coverage, command-map coverage, and call-control policy update.
- Data used: synthetic PROD-006-style SD-card/full-sale examples and project-local architecture boundaries. No provider call, private data read, customer audio, transcript body storage, commercial runtime prompt change, payment handling, checkout handling, vector database, embedding provider, or RAG runtime promotion was used.
- Output created: `docs/brain/BRAIN_002_RUNTIME_STATE_SCHEMA.md`, `scripts/brain_runtime_state_schema.py`, `scripts/run_brain_002_runtime_state_schema.py`, `scripts/validate_brain_002_runtime_state_schema.py`, `research/experiments/cases/brain-002-runtime-state-schema.json`, and `research/experiments/generated/BRAIN-002-runtime-state-schema/`.
- What was learned: the project needs to score structured call-state decisions, not only final wording. `sale_ready` must share the packet with `non_sale_correct`, call control, blocked actions, retrieval status, and evidence logging.
- Why it matters for the thesis: BRAIN-002 makes emotion-aware and persuasion-aware behavior inspectable as a runtime decision contract, which supports later comparison between the older core and the full-sale/RAG candidate.
- Open questions: how the full-call gauntlet should weight close quality against non-sale correctness, and whether any RAG-020/RAG-021 rules should be promoted only after the BRAIN-002 packet is scored on fixed calls.

### 2026-05-08 - PROD-006 full-sale MVP scenario grounding

- Objective: pivot the product plan from appointment-setting only toward a full-sale MVP that can close eligible calls through a safe verbal-commitment outcome, while grounding scenarios in real-world call-center patterns without copying transcript text.
- Action taken: added the `FULL_SALE_MVP_STRATEGY.md` product strategy, a PROD-006 scenario-grounding case file, a local runner, a leakage-aware validator, ignored external dataset storage, setup coverage, command-map coverage, and a thesis reference-registry entry for the CallCenterEN / AIxBlock dataset.
- Data used: public dataset metadata from Hugging Face and the arXiv CallCenterEN paper, plus a project-owned fixture of multi-domain call-center pattern summaries. No dataset ZIP was downloaded, no raw transcript text was stored, no provider call was made, no real customer data was used, and no commercial runtime prompt was populated with transcript-derived text.
- Output created: `docs/product/FULL_SALE_MVP_STRATEGY.md`, `scripts/full_sale_scenario_grounding.py`, `scripts/run_prod_006_full_sale_scenario_grounding.py`, `scripts/validate_prod_006_full_sale_scenario_grounding.py`, `research/experiments/cases/prod-006-full-sale-scenario-grounding.json`, and `research/experiments/generated/PROD-006-full-sale-scenario-grounding/`.
- What was learned: the useful first step is not to copy real scripts; it is to extract multi-domain scenario patterns, require at least three source patterns per scenario, and score both safe close rate and non-sale correctness while treating leakage as a hard failure.
- Why it matters for the thesis: PROD-006 creates a defensible bridge from real-world call-center evidence to controlled simulations without violating the dataset's non-commercial boundary or polluting runtime prompts with transcript-derived text.
- Open questions: how the premortem should revise the full-sale MVP strategy before broad runtime changes, and when explicit approval should be requested to download and scan the full dataset locally.

### 2026-05-08 - RESP-007 German pacing-stability follow-up

- Objective: create a narrow German pacing-stability follow-up after RESP-006 without changing the same customer question or answer content.
- Action taken: added a RESP-007 dry-run/live-capable runner, validator, case file, product doc, generated report/result, setup coverage, and command-map coverage. The validator first failed on the missing runner, then passed after the checkpoint was implemented.
- Data used: local synthetic `RESP-007-DE-PACING-STABILITY-COMPLEX`, the same RESP-006 German question and answer content, the local `PROD-005` B2B software campaign fixture, deterministic guarded response output, and project-local provider-boundary helpers. No provider call, private customer data, private raw audio, transcription, voice cloning, vector database, embedding provider, or RAG runtime promotion was used.
- Output created: `scripts/run_resp_007_german_pacing_stability_follow_up.py`, `scripts/validate_resp_007_german_pacing_stability_follow_up.py`, `research/experiments/cases/resp-007-german-pacing-stability-follow-up.json`, `research/experiments/generated/RESP-007-german-pacing-stability-follow-up/`, and `docs/product/RESP_007_GERMAN_PACING_STABILITY_FOLLOW_UP.md`.
- What was learned: the German issue can be isolated as delivery stability: `old_plain_guarded` needs an opening rush guard and late-drag prevention, while `new_shaped_runtime` needs a speed cap and later answer spacing.
- Why it matters for the thesis: RESP-007 preserves human-listening evidence discipline by changing one delivery surface while keeping answer content fixed and blocking any German voice-personality claim until review.
- Open questions: whether Tarik accepts either stabilized German variant after listening, and whether that acceptance is enough to unblock the bounded voice-personality selector.

### 2026-05-08 - BRAIN-001 project brain architecture

- Objective: define what belongs inside the sales-agent brain before turning the recent RAG and voice work into more runtime behavior.
- Action taken: added a BRAIN-001 product architecture doc and validator that define the brain as a small runtime decision architecture, not a prompt dump or uncontrolled memory.
- Data used: project-local architecture and evidence from `REALTIME_AGENT_ARCHITECTURE.md`, `PRODUCT_BRIEF.md`, RAG-017/RAG-018/RAG-020/RAG-021, RESP-005/RESP-006 listening decisions, and the existing private-data boundary. No new public sources, provider calls, private customer data, raw private audio, raw private transcripts, vector database, embedding provider, or runtime retrieval promotion was used.
- Output created: `docs/brain/BRAIN_001_PROJECT_BRAIN_ARCHITECTURE.md`, `scripts/validate_brain_001_project_brain_architecture.py`, setup-check coverage, command-map coverage, roadmap tracking, and this methodology entry.
- What was learned: the project brain should be a compact live decision system: reusable sales core, `SalesCampaign`, short-term call state, conservative buyer-state/emotion estimates, sales strategy selector, optional guarded retrieval, voice delivery profile, and post-call learning outside the live path.
- Why it matters for the thesis: BRAIN-001 connects RAG, voice, campaign guardrails, and emotional understanding into one inspectable architecture while preserving the evidence gates that prevent premature runtime claims.
- Open questions: whether `BRAIN-002` should next become a strict runtime state schema, or whether the German pacing-stability follow-up should complete first so the voice-personality boundary is clearer.

### 2026-05-08 - RAG-021 buyer trust and conversation-repair source expansion

- Objective: find more source-backed RAG information after RAG-020, with an emphasis on buyer trust, value clarity, conversation repair, and emotion-safe support.
- Action taken: added a new RAG-021 public-source pack with 10 reviewed URLs, 16 project-owned paraphrased advisory rules, a red-first validator, a runner, a product doc, generated evidence, setup coverage, and thesis source registry entries.
- Data used: public web pages and public records only: Bain B2B Elements of Value, organizational trust research, autonomy-support meta-analysis, reactance communication research, Gross emotion regulation, conversation-repair analysis, cognitive-load theory, implementation-intention research, Digital.gov plain-language guidance, and OECD AI Principles. No private customer data, source excerpts, copied scripts, provider calls, NotebookLM API calls, vector database, or embedding provider was used.
- Output created: `scripts/rag_buyer_trust_conversation_repair.py`, `scripts/run_rag_021_buyer_trust_conversation_repair.py`, `scripts/validate_rag_021_buyer_trust_conversation_repair.py`, `research/experiments/cases/rag-021-buyer-trust-conversation-repair.json`, `research/experiments/generated/RAG-021-buyer-trust-conversation-repair/`, and `docs/product/RAG_021_BUYER_TRUST_CONVERSATION_REPAIR.md`.
- What was learned: a stronger sales agent needs more than persuasion tactics. It needs to diagnose value dimension, trust type, buyer autonomy risk, cognitive load, and conversation-repair needs before choosing a close or objection response.
- Why it matters for the thesis: RAG-021 strengthens the emotional-understanding argument by replacing hidden-state guessing with observable repair, trust, clarity, and handoff patterns.
- Open questions: whether RAG-020 and RAG-021 should be imported together into a future RAG-017 registry rebuild and tested against the same retrieval-vs-core simulation before any runtime promotion.

### 2026-05-08 - RAG-020 sales persuasion and emotion-understanding deep dive

- Objective: add deeper RAG information for sales strategy, ethical persuasion, buyer confidence, and emotion understanding while Tarik is away from the project.
- Action taken: added a new RAG-020 public-source pack with 12 reviewed URLs, 20 project-owned paraphrased advisory rules, a red-first validator, a runner, a product doc, generated evidence, setup coverage, and thesis source registry entries.
- Data used: public web pages and public records only: Gartner Challenger sales guidance, Stanford Fogg Behavior Model, COM-B/Behaviour Change Wheel, SAMHSA TIP 35 motivational interviewing, Harvard BATNA guidance, Elaboration Likelihood Model reference material, Barrett emotion-inference limits, Lieberman affect labeling, NIST AI RMF, NIST Generative AI Profile, EU AI Act text, and FTC AI deception guidance. No private customer data, source excerpts, copied scripts, provider calls, NotebookLM API calls, vector database, or embedding provider was used.
- Output created: `scripts/rag_sales_persuasion_emotion_deep_dive.py`, `scripts/run_rag_020_sales_persuasion_emotion_deep_dive.py`, `scripts/validate_rag_020_sales_persuasion_emotion_deep_dive.py`, `research/experiments/cases/rag-020-sales-persuasion-emotion-deep-dive.json`, `research/experiments/generated/RAG-020-sales-persuasion-emotion-deep-dive/`, and `docs/product/RAG_020_SALES_PERSUASION_EMOTION_DEEP_DIVE.md`.
- What was learned: the most useful next RAG material is not more generic closing scripts; it is a safer decision framework that teaches before pitching, lowers buyer friction before next-step asks, preserves autonomy, treats emotion signals as uncertain context, and blocks unvalidated or biometric emotion inference from runtime use.
- Why it matters for the thesis: RAG-020 strengthens the product's research basis for persuasion and emotion awareness while keeping runtime retrieval gated behind RAG-017/RAG-018 validation.
- Open questions: whether RAG-020 should be imported into a future RAG-017 registry rebuild and then tested against the existing retrieval-vs-core simulation before any runtime promotion.

### 2026-05-08 - RESP-006 German runtime A/B listening packet

- Objective: create the German counterpart to RESP-005 before turning the accepted English voice differences into selectable runtime personalities.
- Action taken: added a RESP-006 dry-run/live-capable harness with one synthetic German send-info/trust/boss question, `old_plain_guarded` as direct `RESP-001` final response, and `new_shaped_runtime` as the `RESP-002`/`VOICE-044` provider-rendered German TTS input.
- Data used: local synthetic `RESP-006-SAME-Q-DE-COMPLEX`, the local `PROD-005` B2B software campaign fixture, deterministic guarded response output, and the project-local TTS boundary. No provider call, private customer data, private raw audio, transcription, or voice cloning was used in the default run.
- Output created: `scripts/run_resp_006_german_runtime_version_ab_listening_check.py`, `scripts/validate_resp_006_german_runtime_version_ab_listening_check.py`, `research/experiments/cases/resp-006-german-runtime-version-ab-listening-check.json`, `research/experiments/generated/RESP-006-german-runtime-version-ab-listening-check/`, and `docs/product/RESP_006_GERMAN_RUNTIME_VERSION_AB_LISTENING_CHECK.md`.
- What was learned: the German harness produces two distinct provider inputs for the same longer German answer. Tarik's listening review found that `old_plain_guarded` starts a bit too fast and then becomes a bit too slow, while `new_shaped_runtime` starts strong but becomes a bit too fast later in the answer. The issue is pacing stability, not voice identity.
- Why it matters for the thesis: this prevents an English-only personality decision from being promoted into a multilingual runtime assumption.
- Open questions: which narrow pacing changes can stabilize German delivery while keeping the same question and answer content fixed for comparison.

### 2026-05-08 - RESP-005 same-question runtime A/B listening packet

- Objective: create one old-runtime versus new-runtime listening comparison where both variants answer the same more complex customer question.
- Action taken: added a RESP-005 dry-run/live-capable harness with one synthetic English send-info/trust/boss question, `old_plain_guarded` as direct `RESP-001` final response, and `new_shaped_runtime` as the `RESP-002`/`VOICE-044` provider-rendered TTS input.
- Data used: local synthetic `RESP-005-SAME-Q-EN-COMPLEX`, the local `PROD-005` B2B software campaign fixture, deterministic guarded response output, and the project-local TTS boundary. No provider call, private customer data, private raw audio, transcription, or voice cloning was used in the default run.
- Output created: `scripts/run_resp_005_runtime_version_ab_listening_check.py`, `scripts/validate_resp_005_runtime_version_ab_listening_check.py`, `research/experiments/cases/resp-005-runtime-version-ab-listening-check.json`, `research/experiments/generated/RESP-005-runtime-version-ab-listening-check/`, and `docs/product/RESP_005_RUNTIME_VERSION_AB_LISTENING_CHECK.md`.
- What was learned: the harness produces two clearly different provider inputs for the same longer answer. Tarik's listening review accepted both as strong but different personality directions: `old_plain_guarded` feels like a real laid-back salesperson, while `new_shaped_runtime` feels more serious and lower-energy. The current environment has voice IDs available through ignored local config but no provider API key, so this shell did not create fresh audio.
- Why it matters for the thesis: this gives a tighter human-listening comparison than broad bilingual batches because it controls for question, answer content, provider target, and review criteria.
- Open questions: how to expose these accepted personalities as bounded runtime profiles, and which campaigns or listener types should default to each voice style.

### 2026-05-08 - RAG-018 retrieval-vs-core call simulation

- Objective: answer whether the retrieval-enabled RAG-018 path is better than the older retrieval-disabled core path across a small multi-turn call simulation.
- Action taken: added a fixed `4`-call, `12`-turn local simulation and a validator that compares core and retrieval scores, requires no core wins, preserves protected turns, and blocks default-retrieval promotion from this result alone.
- Data used: local synthetic `PROD-005` campaign fixtures, `research/experiments/cases/rag-018-retrieval-vs-core-call-simulation.json`, the local RAG-017 runtime registry, and deterministic RESP-001 guarded response output. No provider call, private customer data, vector database, embedding provider, or LLM call was used.
- Output created: `scripts/run_rag_018_retrieval_vs_core_call_simulation.py`, `scripts/validate_rag_018_retrieval_vs_core_call_simulation.py`, `research/experiments/cases/rag-018-retrieval-vs-core-call-simulation.json`, `research/experiments/generated/RAG-018-retrieval-vs-core-call-simulation/`, and updated RAG-018 product documentation.
- What was learned: retrieval beats the older core path on the fixed validated objection turns (`4` retrieval wins, `0` core wins, `8` ties, `+8` score delta) while preserving `6/6` protected turns.
- Why it matters for the thesis: this supports the hybrid teach-now/retrieve-live direction for validated objection handling while preserving the conservative default-off retrieval boundary.
- Open questions: whether a larger call-outcome simulation or human review confirms that the improved objection handling also improves appointment-setting without increasing pressure.

### 2026-05-08 - RAG-018 authority and trust influence paths

- Objective: close the two remaining RAG-018 scripted-call quality gaps without making retrieval default.
- Action taken: first changed the scripted-call validator to expect `RAG-018-SIM-C04` and `RAG-018-SIM-C05` to be influenced, watched the validator fail with only `2` influenced cases, then added gated English authority/boss and trust branches that require matching retrieved objection hints.
- Data used: local synthetic `RAG-018-SIM-C04` and `RAG-018-SIM-C05`, the local RAG-017 runtime registry, and deterministic RESP-001 guarded response output. No provider call, private customer data, vector database, embedding provider, or LLM call was used.
- Output created: updated `scripts/generate_guarded_response.py`, `scripts/validate_rag_018_scripted_call_simulation.py`, `research/experiments/cases/rag-018-scripted-call-simulation.json`, refreshed `research/experiments/generated/RAG-018-scripted-call-simulation/`, and updated RAG-018 product documentation.
- What was learned: the authority/boss and trust gaps can be closed with narrow opt-in wording that asks for a shareable summary, one concern, or proof-oriented information instead of widening generic unknown-objection rewriting.
- Why it matters for the thesis: all four current scripted influence paths now improve scored response quality while preserving the opt-in retrieval boundary and protected-context behavior.
- Open questions: whether this should now move to a broader multi-turn call simulation before any default retrieval decision.

### 2026-05-08 - RAG-018 send-me-info influence path

- Objective: expand RAG-018 by one narrow safe behavior after the scripted-call simulation exposed send-me-info as a quality gap.
- Action taken: first changed the scripted-call validator to expect `RAG-018-SIM-C03` to be influenced, watched it fail with only `1` influenced case, then added a gated English send-me-info response branch that only applies when the transcript asks to send information and retrieved hints include send-info/relevance guidance.
- Data used: local synthetic `RAG-018-SIM-C03`, the local RAG-017 runtime registry, and deterministic RESP-001 guarded response output. No provider call, private customer data, vector database, embedding provider, or LLM call was used.
- Output created: updated `scripts/generate_guarded_response.py`, `scripts/validate_rag_018_scripted_call_simulation.py`, `research/experiments/cases/rag-018-scripted-call-simulation.json`, refreshed `research/experiments/generated/RAG-018-scripted-call-simulation/`, and updated RAG-018 product documentation.
- What was learned: send-me-info can safely become the second opt-in RAG influence path when the response asks what information would be relevant instead of sending a generic follow-up.
- Why it matters for the thesis: this shows the hybrid design can expand incrementally with red-first validation while still keeping retrieval opt-in and protected contexts unchanged.
- Open questions: whether authority/boss or trust objections should be the next narrow tested influence path.

### 2026-05-08 - RAG-018 scripted-call simulation gate

- Objective: test whether the first opt-in RAG-018 influence path improves broader call behavior before any default retrieval decision.
- Action taken: added a fixed 10-case scripted-call simulation, scored objection resolution and next-step quality, validated protected-context preservation, and generated a RAG-018 simulation report.
- Data used: local synthetic `PROD-005` campaign fixtures, `research/experiments/cases/rag-018-scripted-call-simulation.json`, the local RAG-017 runtime registry, and deterministic RESP-001 guarded response output. No provider call, private customer data, vector database, embedding provider, or LLM call was used.
- Output created: `scripts/run_rag_018_scripted_call_simulation.py`, `scripts/validate_rag_018_scripted_call_simulation.py`, `research/experiments/cases/rag-018-scripted-call-simulation.json`, `research/experiments/generated/RAG-018-scripted-call-simulation/`, and updated RAG-018 product documentation.
- What was learned: the narrow German price-objection influence path remains safe and improves one scored turn, but send-me-info, authority, and trust objections are still quality gaps because retrieved hints are not yet used by the composer.
- Why it matters for the thesis: the hybrid teach-now/retrieve-live design now has a broader safety gate and an explicit negative result that blocks making retrieval default too early.
- Open questions: which one of the remaining quality gaps should get the next narrow tested influence rule, with send-me-info as the lowest-risk candidate.

### 2026-05-08 - RAG-018 opt-in retrieval influence pass

- Objective: move RAG-018 beyond safe retrieval metadata by allowing one validated advisory hint path to improve runtime wording without making retrieval default.
- Action taken: changed the German price-objection branch so opt-in retrieved objection-diagnosis/autonomy hints can produce a distinct clarifying question, updated RAG-018 and RESP-001 validators to require that influence, and regenerated the RESP-001 retrieval A/B evaluation.
- Data used: local synthetic `PROD-005` campaign fixtures, the local RAG-017 runtime registry, and deterministic RESP-001 guarded response output. No provider call, private customer data, external vector database, embedding provider, or LLM call was used.
- Output created: updated RAG-018/RESP-001 validators, updated guarded response composer, refreshed `research/experiments/generated/RESP-001-retrieval-ab-evaluation/`, and updated RAG-018 product documentation.
- What was learned: live RAG can influence a safe, non-protected response when the composer has a narrow allowed wording path; blocked and protected contexts still prevent retrieval influence.
- Why it matters for the thesis: this is the first evidence that the hybrid teach-now/retrieve-live design can affect runtime behavior while preserving opt-in retrieval, campaign-fact grounding, latency bounds, and guardrail blocks.
- Open questions: which larger scripted call simulation should test whether the influenced wording improves objection resolution or next-step quality before any default retrieval decision.

### 2026-05-08 - RESP-004 VOICE-044 listening-check harness

- Objective: create a separate checkpoint for the VOICE-044 polished-baseline listening test instead of writing new evidence into RESP-003.
- Action taken: added a RESP-004 dry-run/default, live-opt-in runner and validator that reuse RESP-003 as the TTS bridge while keeping RESP-004 as the test identity and artifact owner.
- Data used: the first two official VOICE-044 synthetic focus cases: English fast-filler cleanup and German connector cleanup. No customer audio, raw private audio, transcription, voice cloning, provider call, or secret value was used.
- Output created: `scripts/run_resp_004_voice_044_listening_check.py`, `scripts/validate_resp_004_voice_044_listening_check.py`, `docs/product/RESP_004_VOICE_044_LISTENING_CHECK.md`, and generated RESP-004 dry-run artifacts.
- What was learned: follow-up listening checks should get their own checkpoint identity when they answer a new research question, even if they reuse the existing RESP-003 live-capable TTS bridge internally.
- Why it matters for the thesis: this preserves the evidence chain by separating the stable TTS bridge from the human-listening experiment around VOICE-044.
- Open questions: whether to run the RESP-004 live provider pass now or return directly to RAG-018 opt-in retrieval evaluation.

### 2026-05-08 - VOICE-044 baseline delivery polish

- Objective: improve the accepted baseline shaped runtime after VOICE-043 without promoting the rejected VOICE-041 private-pattern profile.
- Action taken: added a VOICE-044 runtime layer after low-pressure focus and before optional private-pattern settings; removed narrow fast filler/connector artifacts in eligible English and German provider-facing text; added runner, validator, case file, product docs, setup coverage, and RESP-002 integration checks.
- Data used: synthetic campaign fixtures and Tarik's listening feedback about baseline/private-pattern preference and specific voice artifacts. No customer audio, raw private audio read, transcription, voice cloning, provider call, or secret value was used.
- Output created: `scripts/voice_baseline_delivery_polish.py`, `scripts/run_voice_044_baseline_delivery_polish.py`, `research/experiments/cases/voice-044-baseline-delivery-polish.json`, `docs/product/VOICE_044_BASELINE_DELIVERY_POLISH.md`, and generated VOICE-044 dry-run artifacts.
- What was learned: after baseline wins an A/B, the next useful improvement is not broader personalization but targeted cleanup of the exact artifacts that make otherwise good speech sound robotic or rushed.
- Why it matters for the thesis: this demonstrates a conservative human-in-the-loop iteration loop where subjective listening feedback becomes a bounded, testable runtime layer with protected-text and no-provider boundaries.
- Open questions: whether the polished baseline should be checked with a short live RESP-003 listening run before moving back to broader RAG or product-learning work.

### 2026-05-08 - RESP-003 follow-up voice tuning

- Objective: convert Tarik's second RESP-003 bilingual listening feedback into narrow runtime tuning without regressing the English objection and next-step samples that sounded strong.
- Action taken: added RESP-003 validator checks for shaped-runtime speed behavior, nudged the German VOICE-034 lower speed bound from `0.97` to `0.975`, kept German pause text unchanged for the objection case, and then corrected the English trust-repair regression by replacing the brittle `.<break> That's why...` transition with `, so...` while keeping trust speed in a livelier `1.13-1.14` band.
- Data used: synthetic RESP-003 bilingual live A/B prompts and Tarik's human listening feedback only. No customer audio, transcription, voice cloning, private call data, or provider secret values were stored.
- Output created: updated VOICE-034/VOICE-036 docs, RESP-003 human listening notes, validator checks, and regenerated dry-run RESP-003 artifacts.
- What was learned: the English trust issue was not a literal filler insertion. Lowering speed to `1.12` made English sound more robotic, so the better correction is phrase-flow repair plus a livelier bounded speed. The newer German voice ID removed most roboticness, so only a tiny German pacing adjustment is justified.
- Why it matters for the thesis: this preserves a controlled human-in-the-loop voice iteration where qualitative listening feedback is translated into bounded, testable provider settings instead of broad prompt or voice-layer churn.
- Open questions: the corrected live RESP-003 run confirmed the reviewed English trust, English objection, English next-step, and German objection shaped-runtime samples are good enough to keep as the current checkpoint. Broader campaign coverage and production readiness remain future questions.

### 2026-05-07 - RESP-003 bilingual runtime TTS A/B harness

- Objective: prepare a matched English/German listening comparison for the current runtime voice path instead of relying only on offline delivery metadata.
- Action taken: added a RESP-003 live-capable A/B runner and validator comparing plain guarded `final_response` text with RESP-002 shaped provider-ready TTS input across objection, trust-repair, and next-step scenarios.
- Data used: local synthetic campaign fixtures and current RESP-001/RESP-002/RESP-003 runtime packets only. No TTS provider call, customer audio upload, voice cloning, generated audio, private customer data, or API key was used.
- Output created: `research/experiments/generated/RESP-003-bilingual-live-tts-ab/`.
- What was learned: all six matched runtime cases produce a shaped TTS input that differs from plain guarded text while preserving dry-run provider boundaries and requiring human listening review before quality claims.
- Why it matters for the thesis: the next audio review can compare the actual runtime voice path side by side in both languages, rather than testing earlier voice artifacts or metadata alone.
- Open questions: whether the first live provider run should use ElevenLabs only or repeat the matched A/B with Cartesia after the ElevenLabs listening review.

### 2026-05-07 - RESP-003 bilingual live listening review

- Objective: record Tarik's listening review of the first matched RESP-003 bilingual live ElevenLabs A/B run.
- Action taken: reviewed all generated plain-guarded versus shaped-runtime audio files, accepted shaped runtime as clearly better than plain, and converted the German pacing issue into a slower German runtime pacing gate.
- Data used: generated ElevenLabs MP3 files from `research/experiments/generated/RESP-003-bilingual-live-tts-ab/audio/`. No customer audio, voice cloning, private call audio, or secret values were stored in the review.
- Output created: updated RESP-003 A/B result/report plus German pacing profile changes in VOICE-034 and VOICE-036.
- What was learned: shaped runtime is strongly preferred over plain guarded output. English shaped runtime is currently good on naturalness, clarity, emotional tone, and pacing. German shaped runtime is better than plain but still too robotic and too fast.
- Why it matters for the thesis: this is the first direct evidence that runtime delivery shaping improves perceived voice output in both languages, while also identifying a language-specific failure that requires separate German tuning.
- Open questions: whether a better German ElevenLabs voice ID solves most roboticness, and whether the slower German profile improves pacing without making German sound hesitant.

### 2026-05-07 - RESP-002 bilingual voice parity suite

- Objective: ensure English voice-delivery improvements are evaluated in parallel with German improvements.
- Action taken: added a matched local RESP-002 parity runner and validator for German and English objection, trust-repair, and next-step freeform sales responses.
- Data used: local synthetic campaign fixtures only. No TTS provider call, customer audio upload, voice cloning, generated audio, private customer data, or API key was used.
- Output created: `research/experiments/generated/RESP-002-bilingual-voice-parity/`.
- What was learned: both English and German currently show spoken normalization, prosody cues, pacing calibration, emotion smoothing, provider-rendering changes, and protected-text preservation across the matched offline voice-delivery suite.
- Why it matters for the thesis: bilingual voice quality can now be reported with a reproducible side-by-side gate instead of relying on German-heavy test coverage.
- Open questions: whether later live listening tests should require matched English/German audio samples for every new VOICE layer before accepting the layer.

### 2026-05-07 - RESP-001 retrieval A/B evaluation

- Objective: compare the deterministic policy response, always-on core sales delivery playbook, and opt-in live RAG on the same frozen realtime cases.
- Action taken: added `scripts/run_resp_001_retrieval_ab_evaluation.py`, ran it on the 9 frozen `PROD-005` realtime cases, and corrected RESP-001 retrieval instrumentation so `retrieval_used_in_runtime` is true only when the RAG-guided candidate differs from the no-retrieval core-playbook candidate.
- Data used: local campaign fixtures and the local RAG-017 registry only. No provider call, private customer data, external vector database, embedding provider, or LLM call was used.
- Output created: `research/experiments/generated/RESP-001-retrieval-ab-evaluation/`.
- What was learned: the core playbook improves several policy responses without needing live RAG. Live RAG retrieves safe advisory hints quickly, but the current deterministic composer does not yet use those hints to produce different wording.
- Why it matters for the thesis: this creates a reproducible baseline before claiming runtime retrieval improves sales behavior, and it separates safe retrieval availability from actual behavioral influence.
- Open questions: which additional scripted cases should represent appointment setting, partner/boss objections, send-me-info, trust objections, buying signals, and next-step closing before any default retrieval decision.

### 2026-05-07 - Core playbook live RAG implementation slice

- Objective: implement the first working slice of the hybrid teach-now, retrieve-live, learn-later architecture.
- Action taken: added the core sales/delivery playbook, retrieval-before-composition gates, retrieval latency metadata, campaign-fact grounding, core delivery pack handoff, and a 200-note call-pattern learning checkpoint.
- Data used: local project RAG registry, local campaign fixtures, generated artifacts, and synthetic validator notes only. No provider call, private call read, external vector DB, embedding provider, or LLM call was used.
- Output created: core playbook artifacts, guarded response retrieval metadata, voice delivery metadata, and local checkpoint validator output.
- What was learned: live RAG can stay deterministic and fast in the local path while becoming a real pre-composition input. The safest first delivery integration is metadata handoff into RESP-002 while keeping `final_response` unchanged.
- Why it matters for the thesis: the agent can now combine distilled fixed behavior with guarded contextual retrieval while preserving campaign facts and batch-only learning boundaries.
- Open questions: whether to enable stall-for-time fallback in v1 live calls and whether the first relevance threshold should increase after live tests.

### 2026-05-07 - Core sales, delivery, live RAG architecture decision

- Objective: decide how the agent should use the existing RAG corpus before live calls without hard-coding the full registry or relying only on retrieval.
- Action taken: documented a hybrid `teach now + retrieve live + learn later` design that separates safety/compliance, core sales playbook behavior, delivery intelligence, live tactical RAG, and reviewed batch-based pattern learning; added live retrieval latency budgets, relevance/source gates, campaign-fact grounding, and a 200-note learning checkpoint.
- Data used: local RAG-017/RAG-018 docs, guarded response code, current RESP/VOICE delivery docs, and the private-call learning scaffold. No provider call, private data read, external vector DB, embedding provider, or runtime private retrieval was used.
- Output created: `docs/superpowers/specs/2026-05-07-core-sales-delivery-live-rag-design.md`.
- What was learned: the current runtime RAG path is opt-in and source-traced, but retrieval currently arrives after response composition. The next implementation should move allowed retrieval before composition while keeping protected text, campaign facts, latency, relevance thresholds, and final voice safety boundaries intact.
- Why it matters for the thesis: the agent architecture now has a clear separation between fixed safety rules, distilled sales/delivery behavior, contextual retrieval, and reviewed pattern extraction from successful and failed call batches.
- Open questions: which exact artifacts should hold the distilled core playbook and delivery intelligence pack, whether the first batch should stay public-source-only or include reviewed redacted private-call patterns, the first deterministic relevance threshold, and whether stall-for-time fallback should be enabled in v1.

### 2026-05-07 - Project review validator cleanup

- Objective: run a broad local project review and fix review-only failures that prevented the full validator sweep from staying clean.
- Action taken: ran the setup, drift, thesis, private-data, RAG, guarded-response, voice/runtime, and all-script validator sweeps; fixed validators that wrote review scratch artifacts into tracked generated paths instead of `.tmp`; fixed the RAG-001 runner to read UTF-8 BOM JSON case files; regenerated the RESP-001 guarded-response artifact with retrieval metadata.
- Data used: local repo files and generated validation artifacts only. No provider call, private data scan, private audio, NotebookLM API call, embedding provider, external vector database, or runtime retrieval beyond local guarded validation was used.
- Output created: updated validator scratch-output paths, RAG-001 case loading, VOICE-013/VOICE-014 validator assumptions, stale VOICE case artifact paths, and refreshed `research/experiments/generated/RESP-001/` artifacts.
- What was learned: the drift guard was effective at catching validators that still dirtied tracked generated artifacts. The RAG-001 runner also needed BOM-tolerant case loading because some Windows-edited JSON inputs can include a UTF-8 BOM.
- Why it matters for the thesis: review gates should be reproducible from a clean checkout. Validators must not create artifacts that immediately break another guard, and ingestion runners should tolerate common local encoding variants without weakening source or privacy boundaries.
- Open questions: whether a future meta-validator should run all validators inside a temporary output workspace to avoid accidental tracked artifact churn.

### 2026-05-07 - Vinh/AskVinh per-video source metadata cleanup

- Objective: replace the prior title-only Vinh/AskVinh RAG source caveat with explicit per-video metadata where public search could verify it.
- Action taken: compared the `40` titles in the imported Vinh Giang NotebookLM report against public YouTube/search metadata, added verified watch URLs and publication dates to the thesis reference registry, and marked unresolved title-only items explicitly instead of treating them as verified.
- Data used: public YouTube/search metadata, Vinh Giang official channel/resources pages, and existing local RAG import metadata. No transcript text, video downloads, private data, provider calls, or runtime retrieval changes were used.
- Output created: expanded Vinh/AskVinh section in `docs/thesis/THESIS_REFERENCE_REGISTRY.md`.
- What was learned: most imported Vinh RAG titles can be tied to concrete watch URLs, but several titles either changed, are not indexed cleanly, or appear only through podcast/channel mirrors. Those should remain title-only pending exact watch URL confirmation.
- Why it matters for the thesis: this improves provenance for practitioner-source RAG claims while preserving the boundary that Vinh material is communication-training inspiration, not academic evidence or copied runtime wording.
- Open questions: whether to use a YouTube metadata tool/API later to resolve the remaining pending titles without relying on search snippets or third-party transcript mirrors.

### 2026-05-07 - RAG-019 sales communication source expansion

- Objective: add a broader public-source sales communication layer to the guarded RAG without copying scripts or enabling unreviewed retrieval.
- Action taken: researched public sources across cold calling, objections, closing, consultative selling, sales psychology, emotional intelligence, negotiation, voice delivery, conversation design, call-center behavior, persuasion, storytelling, German sales communication, real call breakdowns, and ethics/compliance; converted the relevant guidance into source-traced, project-owned advisory rules; wired the new source pack into RAG-017 registry generation.
- Data used: public web sources only, including sales-methodology pages, academic/encyclopedic decision and manipulation references, conversation-design/provider documentation, call-center guidance, FTC guidance, and German telemarketing/UWG references. No private customer data, private audio, raw call transcripts, copied source passages, NotebookLM API call, provider call, embedding provider, or external vector database was used.
- Output created: `research/experiments/cases/rag-019-sales-communication-source-expansion.json`, `docs/product/RAG_019_SALES_COMMUNICATION_SOURCE_EXPANSION.md`, RAG-019 runner/validator scripts, RAG-017 registry source-URL trace support, setup/command documentation updates, and this thesis reference update.
- What was learned: broad sales guidance can be made useful only after it is narrowed into consent-aware, low-pressure, observable-signal-only rules. The most important boundaries are no hidden emotion inference, no protected-trait inference, no pressure escalation, no copied scripts, no compliance-text changes, and no runtime retrieval unless explicitly enabled.
- Why it matters for the thesis: the sales agent now has a traceable public-source advisory corpus for practical sales behavior while preserving the thesis safety claim that persuasive knowledge is gated, paraphrased, local, reviewable, and subordinate to campaign/compliance guardrails.
- Open questions: which of these RAG-019 items should be evaluated first in reviewed campaign simulations, and whether future source intake should separate peer-reviewed evidence from practitioner playbooks more strictly.

### 2026-05-07 - Generated artifact folderization and drift guard

- Objective: make the accumulated experiment evidence easier to audit before pushing the full project checkpoint to GitHub.
- Action taken: grouped prior flat generated artifacts under milestone folders, added `research/experiments/generated/RAG-002-notebooklm-extraction-automation-bridge/imports/README.md`, expanded generated-audio ignore rules, and extended the project drift guard to fail on unexpected flat generated-root files.
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
- Error or correction preserved: updating `runtime/config/local/voice_ids.json` from Windows PowerShell wrote UTF-8 with a BOM. Python rejected the file during VOICE-027 with `JSONDecodeError: Unexpected UTF-8 BOM`. The local voice-config loader was hardened to accept `utf-8-sig`, and a regression check was added so ignored local voice config remains usable after PowerShell edits.
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
- Error or correction preserved: VOICE-035's German output was too fast/compressed for clear review. VOICE-036 originally restored a tiny `0.08s` breath and relaxed German speed to `1.065`; the later RESP-003 matched A/B listening review superseded that speed target with a slower German range.
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
- Action taken: added a failing VOICE-025 validator first, changed `scripts/speech_realism.py` from mid-clause insertion to boundary-aware insertion, added German-specific `also`, `Ã¤hm`, `Ã¤h`, and `hm` placement rules, added a VOICE-025 runner/case set/report, updated setup checks, and regenerated the VOICE-023/VOICE-025 offline reports in organized generated folders.
- Data used: VOICE-024 listening feedback, VOICE-025 filler-placement research, German filler-particle and German turn-beginning sources, and synthetic English/German sales-response cases.
- Output created: `research/experiments/generated/VOICE-025-filler-placement/results.json`, `research/experiments/generated/VOICE-025-filler-placement/report.md`, `docs/product/VOICE_025_FILLER_PLACEMENT.md`, `scripts/run_voice_025_filler_placement.py`, and `scripts/validate_voice_025_filler_placement.py`.
- What was learned: the old rule could split fluent clause frames such as `the important thing is that` and `Wichtig ist, dass`; the new rule moves fillers before the planning sentence or to a sentence boundary. German needed its own profile rather than translated English markers, especially for `also`, `Ã¤h`, and `Ã¤hm`.
- Why it matters for the thesis: this is a clear example of using human listening feedback plus linguistic literature to refine an AI voice behavior layer under guardrails.
- Open questions: the next live audio test should compare whether German `Ã¤h`/`Ã¤hm` are rendered naturally by ElevenLabs or whether some German campaigns should prefer `also`/pause-only cues.

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

- Stored the four raw voice IDs in ignored `runtime/config/local/voice_ids.json`.
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
- Generated `research/experiments/generated/VOICE-022/VOICE-022-spoken-text-normalization.json`.
- Generated `research/experiments/generated/VOICE-022/VOICE-022-spoken-text-normalization-report.md`.
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
  - `research/experiments/generated/VOICE-008/VOICE-008-local-tts-smoke.json`
  - `research/experiments/generated/VOICE-008/VOICE-008-local-tts-smoke-report.md`
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
  - `research/experiments/generated/VOICE-007/VOICE-007-provider-readiness.json`
  - `research/experiments/generated/VOICE-007/VOICE-007-provider-readiness-report.md`
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
  - `research/experiments/generated/PROD-001/PROD-001-rule-baseline-results.json`
  - `research/experiments/generated/PROD-001/PROD-001-rule-baseline-report.md`
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
  - `research/experiments/generated/PROD-001/PROD-001-db-records.json`
  - `docs/product/LEAD_DATABASE_DESIGN.md`
- Output created:
  - `runtime/persistence/sqlite_schema.sql`
  - `scripts/import_simulation_records.py`
  - `runtime/persistence/SQLITE_PROTOTYPE.md`
  - `research/experiments/generated/PROD-001/PROD-001.sqlite`
  - `research/experiments/generated/PROD-001/PROD-001-sqlite-report.md`
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
  - `research/experiments/generated/PROD-001/PROD-001-db-records.json`
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
  - `runtime/prompts/product-qualification-agent.txt`
  - `docs/product/SIMULATION_CONTRACT.md`
- Output created:
  - updated `scripts/run_product_simulation.py`
  - updated `research/experiments/generated/PROD-001/PROD-001-evaluation-packet.md`
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
  - `research/experiments/generated/PROD-001/PROD-001-evaluation-packet.md`
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
  - `runtime/prompts/product-qualification-agent.txt`
  - `scripts/run_product_simulation.py`
  - `research/experiments/generated/PROD-001/PROD-001-evaluation-packet.md`
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
  - `research/experiments/generated/PROD-001/PROD-001-simulation-packet.md`
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
  - `research/experiments/generated/EXP-002/EXP-002-prompt-packet.md`
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
  - `research/experiments/generated/PROD-004/PROD-004-rule-baseline-results.json`
  - `research/experiments/generated/PROD-004/PROD-004-rule-baseline-report.md`
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
  - `research/experiments/generated/VOICE-009/VOICE-009-tts-provider-research.json`
  - `research/experiments/generated/VOICE-009/VOICE-009-tts-provider-research-report.md`
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
  - `research/experiments/generated/VOICE-010/VOICE-010-cartesia-tts-smoke.json`
  - `research/experiments/generated/VOICE-010/VOICE-010-cartesia-tts-smoke-report.md`
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
  - `research/experiments/generated/VOICE-010/VOICE-010-cartesia-tts-smoke.json`
  - `research/experiments/generated/VOICE-010/VOICE-010-cartesia-tts-smoke-report.md`
  - user listening feedback on the two generated WAV files
- Output updated:
  - `docs/product/VOICE_010_CARTESIA_TTS_SMOKE_TEST.md`
  - `research/experiments/VOICE-010-cartesia-tts-smoke.md`
  - `research/experiments/generated/VOICE-010/VOICE-010-cartesia-tts-smoke.json`
  - `research/experiments/generated/VOICE-010/VOICE-010-cartesia-tts-smoke-report.md`
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
  - `research/experiments/generated/VOICE-010/VOICE-010-cartesia-tts-smoke.json`
  - `research/experiments/generated/VOICE-010/VOICE-010-cartesia-tts-smoke-report.md`
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
  - `research/experiments/generated/VOICE-011/VOICE-011-cartesia-websocket-smoke.json`
  - `research/experiments/generated/VOICE-011/VOICE-011-cartesia-websocket-smoke-report.md`
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
  - `research/experiments/generated/VOICE-011/VOICE-011-cartesia-websocket-smoke.json`
  - `research/experiments/generated/VOICE-011/VOICE-011-cartesia-websocket-smoke-report.md`
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
  - `research/experiments/generated/VOICE-012/VOICE-012-speech-naturalness.json`
  - `research/experiments/generated/VOICE-012/VOICE-012-speech-naturalness-report.md`
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
  - `research/experiments/generated/VOICE-013/VOICE-013-elevenlabs-tts-smoke.json`
  - `research/experiments/generated/VOICE-013/VOICE-013-elevenlabs-tts-smoke-report.md`
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
  - `research/experiments/generated/VOICE-013/VOICE-013-elevenlabs-tts-smoke.json`
  - `research/experiments/generated/VOICE-013/VOICE-013-elevenlabs-tts-smoke-report.md`
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
  - `research/experiments/generated/VOICE-013/VOICE-013-elevenlabs-tts-smoke.json`
  - `research/experiments/generated/VOICE-013/VOICE-013-elevenlabs-tts-smoke-report.md`
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
  - `research/experiments/generated/VOICE-011/VOICE-011-cartesia-websocket-smoke.json`
  - `research/experiments/generated/VOICE-013/VOICE-013-elevenlabs-tts-smoke.json`
  - local ignored WAV and MP3 files from the successful live runs
- Output created:
  - `docs/product/VOICE_014_PROVIDER_LISTENING_COMPARISON.md`
  - `research/experiments/VOICE-014-provider-listening-comparison.md`
  - `research/experiments/cases/voice-014-provider-listening-comparison.json`
  - `research/experiments/generated/VOICE-014/VOICE-014-provider-listening-comparison.json`
  - `research/experiments/generated/VOICE-014/VOICE-014-provider-listening-comparison-report.md`
  - `research/experiments/generated/VOICE-014/VOICE-014-provider-listening-comparison.html`
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
  - `research/experiments/generated/VOICE-015/VOICE-015-prosody-naturalness.json`
  - `research/experiments/generated/VOICE-015/VOICE-015-prosody-naturalness-report.md`
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
  - `research/experiments/generated/VOICE-015/VOICE-015-prosody-naturalness.json`
  - current provider documentation for Cartesia Sonic 3 SSML-style tags and ElevenLabs pause controls
- Output created:
  - `scripts/provider_prosody_rendering.py`
  - `scripts/run_voice_016_provider_prosody_rendering.py`
  - `scripts/validate_voice_016_provider_prosody_rendering.py`
  - `research/experiments/cases/voice-016-provider-prosody-rendering.json`
  - `research/experiments/generated/VOICE-016/VOICE-016-provider-prosody-rendering.json`
  - `research/experiments/generated/VOICE-016/VOICE-016-provider-prosody-rendering-report.md`
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
  - `research/experiments/generated/VOICE-016/VOICE-016-provider-prosody-rendering.json`
  - previously validated ElevenLabs HTTP streaming and Cartesia WebSocket provider paths
- Output created:
  - `scripts/run_voice_017_live_ab_audio.py`
  - `scripts/validate_voice_017_live_ab_audio.py`
  - `research/experiments/cases/voice-017-live-ab-audio.json`
  - `research/experiments/generated/VOICE-017/VOICE-017-live-ab-audio.json`
  - `research/experiments/generated/VOICE-017/VOICE-017-live-ab-audio-report.md`
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
  - `research/experiments/generated/VOICE-017/VOICE-017-live-ab-audio.json`
  - `research/experiments/generated/VOICE-017/VOICE-017-live-ab-audio-report.md`
  - local ignored VOICE-017 ElevenLabs MP3 files
- Output created:
  - `research/experiments/generated/VOICE-017/VOICE-017-human-listening-review.md`
  - updated `research/experiments/generated/VOICE-017/VOICE-017-live-ab-audio.json`
  - updated `research/experiments/generated/VOICE-017/VOICE-017-live-ab-audio-report.md`
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
  - `research/experiments/generated/RESP-002/RESP-002-runtime-voice-delivery-result.json`
  - `research/experiments/generated/RESP-002/RESP-002-runtime-voice-delivery-report.md`
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
  - `runtime/providers/VOICE_PROVIDER_RUN_BOUNDARY.md`
  - `runtime/providers/VOICE_GENERATED_AUDIO_ASSET_LOG.md`
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
  - `research/experiments/generated/RESP-003/RESP-003-runtime-live-tts-result.json`
  - `research/experiments/generated/RESP-003/RESP-003-runtime-live-tts-report.md`
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
  - `research/experiments/generated/RESP-003/RESP-003-live-elevenlabs-de-result.json`
  - `research/experiments/generated/RESP-003/RESP-003-live-elevenlabs-de-report.md`
  - `research/experiments/generated/RESP-003/RESP-003-live-elevenlabs-en-result.json`
  - `research/experiments/generated/RESP-003/RESP-003-live-elevenlabs-en-report.md`
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
  - `research/experiments/generated/RESP-003/RESP-003-campaign-prod-005-b2c-telecom-de-elevenlabs-efb86453.mp3`
  - `research/experiments/generated/RESP-003/RESP-003-campaign-prod-005-b2b-software-en-elevenlabs-00aae825.mp3`
- Output created:
  - `research/experiments/generated/RESP-003/RESP-003-bilingual-human-listening-review.md`
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
  - `research/experiments/generated/VOICE-016/VOICE-016-provider-prosody-rendering.json`
  - first VOICE-017 and RESP-003 listening feedback
  - existing protected-segment taxonomy from VOICE-012 through VOICE-016
- Output created:
  - `scripts/sales_voice_tuning.py`
  - `scripts/run_voice_018_sales_voice_tuning.py`
  - `scripts/validate_voice_018_sales_voice_tuning.py`
  - `research/experiments/cases/voice-018-sales-voice-tuning.json`
  - `research/experiments/generated/VOICE-018/VOICE-018-sales-voice-tuning.json`
  - `research/experiments/generated/VOICE-018/VOICE-018-sales-voice-tuning-report.md`
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
  - `research/experiments/generated/VOICE-018/VOICE-018-sales-voice-tuning.json`
  - `research/experiments/cases/voice-017-live-ab-audio.json`
- Output created:
  - `scripts/run_voice_019_sales_tuned_live_ab_audio.py`
  - `scripts/validate_voice_019_sales_tuned_live_ab_audio.py`
  - `research/experiments/cases/voice-019-sales-tuned-live-ab-audio.json`
  - `research/experiments/generated/VOICE-019/VOICE-019-sales-tuned-live-ab-audio.json`
  - `research/experiments/generated/VOICE-019/VOICE-019-sales-tuned-live-ab-audio-report.md`
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
  - `research/experiments/generated/VOICE-019/VOICE-019-sales-tuned-live-ab-audio.json`
  - `research/experiments/generated/VOICE-019/VOICE-019-sales-tuned-live-ab-audio-report.md`
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
  - `research/experiments/generated/VOICE-020/VOICE-020-elevenlabs-voice-design.json`
  - `research/experiments/generated/VOICE-020/VOICE-020-elevenlabs-voice-design-report.md`
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
  - added ignored local config support at `runtime/config/local/voice_ids.json`
  - wired local voice-ID lookup into ElevenLabs live paths used by `VOICE-013`, `VOICE-017`/`VOICE-019`, and `RESP-003`
  - kept environment variables as the override path and kept API keys environment-only
- Data used:
  - project-owner screenshot of ElevenLabs Voice Design showing `loudness`, `guidance_scale`, and generated preview text behavior
  - project-owner feedback that generated Voice Design voices sounded robotic, phone-like/muffled, and too slow
- Output created:
  - `runtime/config/local/.gitignore`
  - `runtime/config/local/voice_ids.example.json`
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
  - updated `research/experiments/generated/VOICE-020/VOICE-020-elevenlabs-voice-design.json`
  - updated `research/experiments/generated/VOICE-020/VOICE-020-elevenlabs-voice-design-report.md`
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
  - `research/experiments/generated/PRIVATE-CALL-LEARNING-001/PRIVATE-CALL-LEARNING-001.json`
  - `research/experiments/generated/PRIVATE-CALL-LEARNING-001/PRIVATE-CALL-LEARNING-001-report.md`
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

### 2026-05-08 - VOICE-030D recurring private speech-pattern extraction

- Objective: correct the private speech-review method so it extracts recurring acoustic delivery patterns from the available sample set, not only from files that already had a runtime-candidate wrapper
- Action taken:
  - updated `scripts/run_voice_030d_private_feature_review.py` to derive candidate values from every usable VOICE-030C feature file
  - kept all feature files counted for coverage while excluding no-measurable-speech files from recurring-pattern bands
  - added plain-language private pattern interpretation for rhythm density, expressiveness variation, vocal presence, and diagnostic-only pause behavior
  - added validator coverage so feature-only files are included in VOICE-030D summaries
- Current private result:
  - feature files read: 121
  - usable for recurring-pattern summary: 119
  - excluded from recurring-pattern summary: 2 no-measurable-speech feature files
  - provider calls, transcription, voice cloning, and runtime profile application: false
- What was learned:
  - the earlier VOICE-030D summary underused the sample set because it only summarized `runtime_learning_candidates`
  - the same acoustic values were present under `features`, so a safe local fallback can summarize recurring patterns without reading raw audio paths or transcripts
  - long pause metrics should remain diagnostic-only because owner recordings can include thinking pauses that should not become sales-agent pacing
- Why it matters for the thesis:
  - it documents a privacy-preserving path from owner speech samples to reviewed aggregate delivery signals
  - it separates recurring acoustic pattern extraction from voice cloning, provider upload, and automatic runtime personalization
  - it gives future voice-personalization claims a clearer audit trail

### 2026-05-08 - VOICE-041 accepted abstract private-pattern runtime bridge

- Objective: add a guarded way for reviewed private speech-pattern findings to influence runtime voice delivery without reading private audio at runtime or cloning a voice
- Action taken:
  - added `scripts/voice_private_pattern_profile.py` as an opt-in layer after RESP-002 low-pressure focus
  - added `scripts/validate_voice_041_private_pattern_profile.py` to lock no-provider, no-cloning, no-raw-audio-read, no-text-rewrite, and protected-segment no-op behavior
  - integrated `voice_delivery.voice_private_pattern_profile` into RESP-002 output and validation
  - documented `VOICE_041_PRIVATE_PATTERN_PROFILE.md`
- Current behavior:
  - default runtime behavior remains disabled
  - an accepted abstract profile can adjust bounded ElevenLabs expressiveness settings for eligible freeform text
  - rhythm density is metadata-only for now, so accepted pacing is not changed silently
  - low vocal-presence findings are blocked from direct copying
- What was learned:
  - private owner speech can support abstract delivery hints without becoming voice cloning or automatic identity imitation
  - provider settings must stay campaign-gated because they can affect the whole rendered segment
  - protected responses must block the profile completely
- Why it matters for the thesis:
  - it shows a privacy-preserving middle path between ignoring private samples and training/cloning from them
  - it keeps private evidence out of public generated artifacts while allowing reviewed aggregate behavior to be tested locally
  - it preserves auditability for future claims about personalized delivery improvement

### 2026-05-08 - VOICE-042 private-pattern listening A/B harness

- Objective: test whether accepted VOICE-041 provider-setting hints improve perceived voice quality without confounding the result with text or pacing changes
- Action taken:
  - added `scripts/run_voice_042_private_pattern_live_ab.py`
  - added `scripts/validate_voice_042_private_pattern_live_ab.py`
  - added `research/experiments/cases/voice-042-private-pattern-live-ab.json`
  - documented `VOICE_042_PRIVATE_PATTERN_LIVE_AB.md`
- Method:
  - compare `baseline_shaped_runtime` against `private_pattern_profile`
  - keep provider-facing TTS text identical across both variants
  - vary only accepted VOICE-041 provider settings
  - keep dry-run as default and require `--live --limit-cases` for provider calls
- Boundary:
  - no raw private audio read at runtime
  - no transcription
  - no private/customer audio upload
  - no voice cloning
  - no quality claim before human listening review
- Why it matters for the thesis:
  - it creates an experiment design that can isolate private-pattern provider settings from text-generation changes
  - it keeps the personalization claim testable without moving private recordings into provider training
  - it preserves the distinction between technical generation success and subjective listening evidence

### 2026-05-08 - VOICE-042 private-pattern listening feedback and profile softening

- Objective: incorporate Tarik's first subjective listening feedback on the private-pattern A/B without overclaiming quality
- Feedback:
  - the private-pattern direction sounded good
  - the profile was too loud
  - the loudness made roboticness more obvious
- Action taken:
  - reduced VOICE-041 ElevenLabs `style` target from `0.12` to `0.06`
  - reduced the maximum style cap from `0.16` to `0.08`
  - reduced the stability delta from `-0.03` to `-0.01`
  - regenerated VOICE-041 and VOICE-042 dry-run artifacts
- Boundary:
  - no raw private audio was read
  - no transcription or voice cloning was used
  - no customer or private audio was uploaded
  - no quality acceptance claim was made
- Why it matters for the thesis:
  - it shows that private-pattern personalization must be tuned conservatively
  - it records a human listening review as evidence without treating one pass as proof
  - it keeps voice personalization tied to bounded provider settings and repeatable A/B checks

### 2026-05-08 - VOICE-042 baseline preferred over private-pattern profile

- Objective: record the second listening outcome after the softened VOICE-041 profile was tested
- Feedback:
  - baseline shaped runtime sounded better than the private-pattern profile
- Decision:
  - keep baseline shaped runtime as the preferred voice path
  - do not promote VOICE-041 as a runtime quality improvement
  - keep VOICE-041 available only as an experimental A/B harness for future variants
- Boundary:
  - no raw private audio was read
  - no transcription or voice cloning was used
  - no customer or private audio was uploaded
  - no quality improvement claim was made for private-pattern delivery
- Why it matters for the thesis:
  - it preserves negative evidence instead of forcing personalization into the runtime
  - it shows that subjective listening can reject an apparently reasonable provider-setting change
  - it keeps the current voice stack grounded in measured comparison rather than assumptions about private-pattern benefit

### 2026-05-08 - VOICE-043 baseline shaped runtime acceptance

- Objective: convert Tarik's VOICE-042 baseline preference into a reusable runtime guard
- Action taken:
  - added `scripts/run_voice_043_baseline_shaped_runtime_acceptance.py`
  - added `scripts/validate_voice_043_baseline_shaped_runtime_acceptance.py`
  - added `research/experiments/cases/voice-043-baseline-shaped-runtime-acceptance.json`
  - documented `VOICE_043_BASELINE_SHAPED_RUNTIME_ACCEPTANCE.md`
  - generated `VOICE-043-baseline-shaped-runtime-acceptance` dry-run artifacts
- Method:
  - test English freeform, German freeform, and protected do-not-call turns
  - require `voice_private_pattern_profile.enabled` and `applied` to remain false by default
  - require ElevenLabs `style` to remain `0.0`
  - require protected text to stay exact
- Boundary:
  - dry-run only
  - no provider calls
  - no raw private audio read
  - no transcription or voice cloning
  - no private or customer audio upload
- Why it matters for the thesis:
  - it shows how subjective listening feedback becomes an engineering guard
  - it preserves a clear baseline for future voice-personalization experiments
  - it prevents a rejected personalization variant from silently entering runtime behavior

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

### 2026-05-15 - RUNTIME-IMPORT-001 canonical runtime import migration

- Objective: keep the project runnable after moving runtime dependencies from script-local modules into the `runtime` package
- Action taken:
  - migrated active operational script imports from legacy `scripts/*` module names to canonical `runtime.*` module paths
  - kept the `scripts/*` wrapper modules as backward-compatible command shims instead of deleting or rewriting them
  - added explicit repo-root `sys.path` bootstraps where direct script execution now imports `runtime.*`
  - left historical generated artifacts and ignored temporary outputs untouched
- Verification method:
  - used syntax-only Python compilation with bytecode writes disabled because existing `__pycache__` files were not writable in this workspace
  - checked for remaining active wrapper imports in `scripts/*.py`
  - reran runtime manifest, PROD, RAG, and VOICE validators relevant to the moved imports
- Boundary:
  - no provider calls
  - no LLM calls
  - no customer or private audio read
  - no runtime response text or policy behavior intentionally changed
- Why it matters for the thesis:
  - it records a maintenance migration that affects reproducibility of prior checkpoints
  - it keeps legacy command names usable while making the runtime package the source of truth
  - it separates engineering import hygiene from product behavior evidence
