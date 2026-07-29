# Checkpoint Index

This index groups checkpoint docs by work track. Runners, validators, cases, and generated reports stay in `scripts/`, `research/experiments/cases/`, and `research/experiments/generated/`.

Runtime-affecting files now live under `runtime/` and are mapped in `runtime/runtime_manifest.json`; use it before editing spoken-text, call-control, campaign-contract, retrieval, or provider-delivery behavior. Legacy `scripts/*` runtime files are compatibility wrappers.

Complete Phase C0 synthetic mechanics checkpoint: `EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics`, documented in `research/experiments/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics.md`, is an accepted offline aggregate checkpoint for synthetic mechanics only. Candidate decision: `keep`; all `30/30` scenarios passed, including `8` rejection cases, and independent candidate review returned `C0/I0/M0`. Policy/scenario/result/report SHA-256 values are `9BB996F886E9AFFBCDA40A6FB71BE10E1CD07D3B114B4E3FBCDAA1DF71171F15`, `D01FBD7677537A0A91D01E0EA8354D079491C13BBD81EC8BAC97E7BBC4520FB0`, `3BBB7FC8F4DFB223837EA8D8B8E92EC46AA0ACF70EA1A6CA4649D41266E43030`, and `FD1ADA58FD5C0B614DB429AD6B5434C988E95942FBEB1FEB87D779C14F9E4EA4`. Implementation trace: aggregate runner `fd92aae6acf146d9271888bb264ecd29269cb870`, independent validator `5c461612f667e1a8727eedb9d2c08d9951b3aed0`, direct-launch correction `4c77f72bf7dc85e2e4587b9c03646716e5aec0ff`, candidate acceptance `77a2fb50ba00210cc75d410240c17115be83a415`, and pair-only commit `62b6b65cf307270bfc2e98c7c08617252859948d`. The guarded ledger passed Phase C0 `177/177`, pinned Phase B `16/16`, four validator sections, five repository gates, and the four LF/compile/protected-runtime/diff checks. Phase B lockbox remains closed and cannot be reused; this checkpoint grants no runtime, provider, data, or Phase D authority.

Current public-data feasibility checkpoint: `EMOTION-STATE-002-phase-b-public-data-feasibility`, documented in `research/experiments/EMOTION-STATE-002-phase-b-public-data-feasibility.md`, completed Task 12 as an `accepted` offline checkpoint with `lockbox_open_count=1` and decision `revise`. Transaction `559ccc55b0b5412ba455ca7fe3e3a6b7` produced result SHA-256 `5829BF4A1FBE86BDD6B19B7CF8B07033BF79744B12F7AF1D493F8D3F10D0073C` and report SHA-256 `56140D4ABDD0B2A6924749E719C66D3972483E0F4191F63201E9DDFCA0A23482`; the exact pair-only commit is `f887989597f23f438e8e537ba5bfbd05823a3587`. Its fail-closed validator exposes `source`, `contracts`, `environment`, `synthetic`, receipt-bound `candidate`, and accepted-pair `checkpoint` sections. The output contract excludes filenames, row records, media identifiers, transcripts, model serialization, probabilities, credentials, and the five project operational signals. This is offline acted-perception research evidence, not production readiness or evidence of customer internal emotion, real-call performance, provider/PSTN/ASR/latency feasibility, runtime readiness, or commercial effectiveness. Push, merge, Phase C, provider, private-data, call, simulation, source-adaptation, and runtime work remain outside this checkpoint.

Current ElevenLabs package checkpoint: `ELEVENLABS-001-universal-sales-core`, documented in `docs/product/ELEVENLABS_001_UNIVERSAL_SALES_CORE.md`, creates the first compact repo-owned universal sales KB and baseline test source under `runtime/providers/elevenlabs_agents/`. It treats ElevenLabs as the managed runtime and manual upload surface while preserving the repo as source of truth. It makes no live provider call, uploads no customer data, does not create a provider-side agent, and does not promote production customer calls.

Current ElevenLabs automation checkpoint: `ELEVENLABS-002-agent-automation`, documented in `docs/product/ELEVENLABS_002_AGENT_AUTOMATION.md`, adds `scripts/run_elevenlabs_agent_automation.py` and `runtime/providers/elevenlabs_agents/automation.py` to convert repo-owned package manifests into dry-run API-ready KB upload requests, LLM response test creation requests, and run-tests request drafts. Live provider writes remain default-off and require `--live --confirm-provider-write`; automatic agent config patching stays blocked until the copied dashboard JSON config is available.

Current ElevenLabs config-patching checkpoint: `ELEVENLABS-003-agent-config-patcher`, documented in `docs/product/ELEVENLABS_003_AGENT_CONFIG_PATCHER.md`, uses a sanitized copy of the current `web design` agent JSON shape to draft an update-agent PATCH payload. It attaches returned KB document IDs under `conversation_config.agent.prompt.knowledge_base`, enables RAG, preserves the existing prompt/first message/model/voice settings, and strips response-only identity fields from the patch output. Live PATCH remains gated by `--live --confirm-provider-write` and `ELEVENLABS_API_KEY`.

Current ElevenLabs dynamic-test checkpoint: `ELEVENLABS-004-mikes-kitchen-dynamic-tests`, documented in `docs/product/ELEVENLABS_004_MIKES_KITCHEN_DYNAMIC_TESTS.md`, adds a repo-owned Mike's Kitchen restaurant website campaign test pack with suite-level dynamic variables and ten detailed LLM response tests. The tests can be created through the ElevenLabs test API with `--operation create-tests`; they are not attached to the agent by PATCH in this checkpoint, and live provider output is stored only as safe response summaries.

Current ElevenLabs scenario-test checkpoint: `ELEVENLABS-005-mikes-kitchen-scenario-tests`, documented in `docs/product/ELEVENLABS_005_MIKES_KITCHEN_SCENARIO_TESTS.md`, adds six Mike's Kitchen multi-turn scenario tests with 8-10 chat-history messages each, suite-level dynamic variables, and a target ElevenLabs test folder named `Atlas Web Studio - Mike's Kitchen Scenarios`. The automation runner now supports explicit `chat_history`, creating or reusing a test folder, and bulk-moving created tests into that folder. It still stores only safe provider response summaries and does not attach tests to an agent by PATCH.

Current ElevenLabs naturalness-patch checkpoint: `ELEVENLABS-006-web-design-naturalness-patch`, documented in `docs/product/ELEVENLABS_006_WEB_DESIGN_NATURALNESS_PATCH.md`, patches the live `web design` agent source prompt, first message, and dynamic-variable placeholders after scenario-test results showed that the dashboard agent had drifted to `You are a helpful assistant.` It keeps the existing KB attachment, avoids new KB uploads, stores only safe provider summaries, and makes the restaurant outreach wording concrete around menu, hours, location, and reservation phone calls.

Current ElevenLabs dynamism/naturalness checkpoint: `ELEVENLABS-007-web-design-dynamism-naturalness`, documented in `docs/product/ELEVENLABS_007_WEB_DESIGN_DYNAMISM_NATURALNESS.md`, adds a stricter Mike's Kitchen naturalness stress pack and patches the live `web design` agent toward less deterministic, less checklist-driven replies. It adds `--agent-temperature` support, targets temperature `0.25` after `0.35` proved unstable on callback/pass-along constraints, shortens the first message, requires the agent to avoid repeating every campaign detail on every turn, and keeps passing dashboard tests subordinate to human naturalness review.

Current ElevenLabs value/pricing repair checkpoint: `ELEVENLABS-008-web-design-value-pricing-repair`, documented in `docs/product/ELEVENLABS_008_WEB_DESIGN_VALUE_PRICING_REPAIR.md`, repairs screenshot-observed failures after the 007 tests passed: internal self-correction leaking to the buyer, price dodging, treating a statement as a question, callback-window overexplaining, and weak restaurant value framing. It updates the universal sales core, Atlas campaign pricing variables, the web design prompt, the 007 naturalness pack's misleading prior turns, and a new value/pricing stress pack for folder `Atlas Web Studio - Value Pricing Stress`.

Current ElevenLabs simulation-test checkpoint: `ELEVENLABS-009-mikes-kitchen-simulation-tests`, documented in `docs/product/ELEVENLABS_009_MIKES_KITCHEN_SIMULATION_TESTS.md`, adds full-conversation Mike's Kitchen Simulation Tests for the dashboard `Simulation test` surface. It replaces fixed next-reply histories with buyer-behavior scenarios, success criteria, dynamic variables, and 12-22 maximum-turn limits for evaluating whether the live agent can sell the next valid step across a dynamic conversation. The current stricter V22c run is not production-green: `7/9` passed, with remaining plain-language and social-objection failures. V22d is only a live prompt patch for gatekeeper callback wording, not a green rerun.

Current ElevenLabs sales-control repair checkpoint: `ELEVENLABS-010-web-design-sales-control-repair`, documented in `docs/product/ELEVENLABS_010_WEB_DESIGN_SALES_CONTROL_REPAIR.md`, repairs human-reviewed simulation failures by stopping after immediate clear refusal, blocking repeated review/send closes, separating Atlas website campaign value from universal sales method, adding stronger restaurant website value angles, answering approved pricing/hosting questions directly, requiring terminal call closings, controlling unapproved bracketed delivery tags, adding optional-booking upsell boundaries, and replacing same-name attached KB docs when patching the live `web design` agent. Current live evidence is improved but not production-ready because V22c remains `7/9`; V22d patched only the remaining gatekeeper wording issue.

Current ElevenLabs remaining-simulation repair checkpoint: `ELEVENLABS-011-web-design-remaining-simulation-repair`, documented in `docs/product/ELEVENLABS_011_WEB_DESIGN_REMAINING_SIMULATION_REPAIR.md`, is the offline continuation after V22c stayed `7/9` and V22d only patched gatekeeper callback wording. It targets the two recorded remaining failures: plain-language abstract wording and social-objection value rotation plus terminal send-path closing. It updates repo-owned prompt, campaign KB, dynamic defaults, manifest, docs, and validator only; no live provider write or simulation rerun has happened yet, so production-green remains blocked until a fresh V22-or-later run passes human review.

Current RAG layer-contract checkpoint: `RAG-022-universal-sales-layer-contract`, documented in `docs/product/RAG_022_UNIVERSAL_SALES_LAYER_CONTRACT.md`, formalizes the three-layer sales knowledge architecture: Universal Sales RAG for reusable sales method, Campaign Sales Overlay for campaign-specific selling adaptation, and Campaign Profile And Facts for approved truth. It adds a repo-owned layer contract, split Atlas Web Studio overlay/profile KB documents, a layered ElevenLabs package manifest, prompt precedence rules, and a validator. The package remains dry-run-first, but after explicit user request on 2026-06-07 the three layered KB files were uploaded to ElevenLabs and the existing `web design` agent was patched with RAG enabled. It still does not claim simulation-green status.

Current RAG category-file checkpoint: `RAG-023-universal-sales-category-files`, documented in `docs/product/RAG_023_UNIVERSAL_SALES_CATEGORY_FILES.md`, makes real universal sales RAG category files the editable source for the universal layer. It adds 21 category files under `runtime/sales_knowledge/universal_sales_rag/categories/`, a category index, a compiler, a compiled universal layer, and a validator that checks category order, source markers, campaign-fact leakage, provider KB freshness, and hash consistency. After explicit user request on 2026-06-07, the compiled universal KB was uploaded to ElevenLabs and the existing `web design` agent was patched with the RAG-023 universal core plus the ELEVENLABS-013 prompt repair. The compiled universal layer still remains subordinate to campaign overlay and campaign profile facts, and this does not claim simulation-green status.

Current ElevenLabs feedback-quality repair checkpoint: `ELEVENLABS-012-web-design-feedback-quality-repair`, documented in `docs/product/ELEVENLABS_012_WEB_DESIGN_FEEDBACK_QUALITY_REPAIR.md`, converts human feedback from the latest simulation screenshots into a repair package. It targets repeated same-angle value arguments, weak first-sentence assurance on free/no-strings/sign-up concerns, overlong busy-callback handling, and direct catch answering. It keeps the RAG-022 three-layer KB package order, updates the prompt plus Atlas campaign overlay/profile documents, and rejects literal fake laughter in customer-visible text. After explicit user request on 2026-06-07, the three updated KB files were uploaded to ElevenLabs and the existing `web design` agent was patched with RAG enabled. It still does not claim simulation-green status.

Current ElevenLabs send-path final-confirmation repair checkpoint: `ELEVENLABS-013-send-path-final-confirmation`, documented in `docs/product/ELEVENLABS_013_SEND_PATH_FINAL_CONFIRMATION.md`, adds a narrow prompt repair for the latest failed simulation screenshot: after the send path is already confirmed and closed, a final buyer clarification such as "so I'll get an email with a link" should receive one yes-plus-closing answer and no reopened pitch. It was applied live together with `RAG-023-universal-sales-category-files` on 2026-06-07 and does not claim simulation-green status.

Current ElevenLabs cross-vertical simulation-test checkpoint: `ELEVENLABS-014-cross-vertical-local-business-simulation-tests`, documented in `docs/product/ELEVENLABS_014_CROSS_VERTICAL_LOCAL_BUSINESS_SIMULATION_TESTS.md`, adds deterministic Simulation Tests for synthetic local-business verticals beyond Mike's Kitchen: plumbing, dental, auto repair, HVAC, hair salon, and home cleaning. It checks whether the hosted Atlas Web Studio web-design agent can use per-test dynamic variables, avoid restaurant leakage, preserve price/no-obligation/send-path boundaries, and handle callback or gatekeeper cases outside the restaurant profile. After the user noted that the dashboard still only showed V22, the pack was created live in ElevenLabs folder `tfld_3401ktftfc17evra47vy8qn1ygsp`; no simulation run or production-green claim has been made.

Current ElevenLabs emotional-resistance simulation-test checkpoint: `ELEVENLABS-028-emotional-resistance-dynamic-simulation-tests`, documented in `docs/product/ELEVENLABS_028_EMOTIONAL_RESISTANCE_DYNAMIC_SIMULATION_TESTS.md`, adds a separate Gemini 2.5 Flash simulation pack for angry, avoidant, suspicious, terse, rapid-fire, price-hostile, email-close, and guarantee-only bad-fit buyer behavior. It uses per-test dynamic variables, 16-20 maximum-turn limits, and no provider writes by default.

Current ElevenLabs cross-vertical feedback repair checkpoint: `ELEVENLABS-015-cross-vertical-feedback-repair`, documented in `docs/product/ELEVENLABS_015_CROSS_VERTICAL_FEEDBACK_REPAIR.md`, converts human review of the first cross-vertical screenshots into an offline repair package. It narrows evaluator wording so service/pricing menu language is allowed outside restaurant context while food menu, reservations, tables, and food ordering remain restaurant leakage. It also expands the Atlas web-design value library with safe local visibility, owned trust-page, service/pricing clarity, one-shareable-link, proof-before-purchase, name-capture, contraction, callback-number-gap, and ethical-persuasion conversation-control rules. No live provider write or production-green claim has been made in this checkpoint.

Current ElevenLabs cross-vertical V2 failure repair checkpoint: `ELEVENLABS-016-cross-vertical-v2-failure-repair`, documented in `docs/product/ELEVENLABS_016_CROSS_VERTICAL_V2_FAILURE_REPAIR.md`, repairs the two failed V2 live simulation cases from suite `suite_5001kth9p7j8fjmr4eyg6ay8wyce`: verbal email send-path confirmation after contact capture and gatekeeper callback-window handling without deflecting to email or inventing a found-online address. It was applied live on 2026-06-07 to agent version `agtvrsn_4201kthavgsgfv681k424dkjsy1t` with KB IDs `N2QmA4GDlyn2gpxOgX0n`, `BKHuY0kInQyzT7II0K18`, and `p9YzzB2mFdaqqnYyHIOW`. V3, V4, and V5 remained `4/6`; V6 improved to `5/6` in suite `suite_4001kthb1m7qfjbsb6k1zytzy65r`. Production-green is still not claimed because the auto-repair spoken-email final confirmation remains unproven in the live simulation harness.

Current ElevenLabs natural-control feedback repair checkpoint: `ELEVENLABS-017-natural-control-feedback-repair`, documented in `docs/product/ELEVENLABS_017_NATURAL_CONTROL_FEEDBACK_REPAIR.md`, converts the next human screenshot review into a prompt, KB, and evaluator repair package. It targets premature send-path endings before contact capture, unanswered terminal buyer clarifications, repeated delivery-timing loops, overlong busy callback/email option handling, stronger name capture by the second non-terminal decision-maker turn, plain analogies/perspective checks, short non-guarantee claim boundaries, and a universal problem-solution-gain-curiosity value sequence. After explicit user request on 2026-06-07, it was applied live to agent version `agtvrsn_6701kthngpabe6etedq4rr4a3dpa` with KB IDs `7pyke4f9n9casIzeA25x`, `K6xBUXcBoo8cPDvrmCzL`, and `9pv9mi6v2EdWIOUsAzoH`; revised V2 simulation tests were created in folder `tfld_6201kth9njh3f18rxe63zqd34cgm`. Production-green is still not claimed because no fresh V2 simulation run and human review have passed.

Current ElevenLabs sales-value and contact-control repair checkpoint: `ELEVENLABS-018-sales-value-and-contact-control-repair`, documented in `docs/product/ELEVENLABS_018_SALES_VALUE_AND_CONTACT_CONTROL_REPAIR.md`, repairs the next human-reviewed failures after 017: weak website-value mechanisms after short non-guarantee answers, missing owner/manager name capture, premature send-path endings after contact acceptance, unanswered final send-path clarifications, and hard refusal of buyer-instructed public-profile contact lookup. It changes the preferred web-design value mechanism to local visibility support through an owned indexable page people can check from Google or social before choosing who to call, while still blocking ranking, SEO, customer-growth, patient-growth, job-volume, revenue, booking, and call-volume guarantees. After explicit user request on 2026-06-07, it was applied live to agent version `agtvrsn_8901kthty7p4e69v6pk3ybnve233` with KB IDs `JF3WSPRZOcPS1rki03ot`, `nDldYVCnhKzj4mKW4X4O`, and `sxG793M1gBKfJxzgUWIO`; revised V3 simulation tests were created in folder `tfld_3501ktha7vdsekeshx4m9wajkhhv`, and old same-name Atlas KB docs were removed with `force=false` so the attached source list stays clean. Production-green is not claimed because no fresh V3 simulation run and human review have passed.

Current ElevenLabs demand-capture and conversion-leakage repair checkpoint: `ELEVENLABS-019-demand-capture-conversion-leakage-repair`, documented in `docs/product/ELEVENLABS_019_DEMAND_CAPTURE_CONVERSION_LEAKAGE_REPAIR.md`, repairs the remaining abstract web-design value language by reframing business impact as wasting less existing attention from Google, Instagram, referrals, QR codes, print, word of mouth, and shared links. It adds campaign-safe conversion leakage mechanisms and V4 simulation criteria while still blocking guaranteed customers, calls, bookings, jobs, patients, rankings, traffic, revenue, live outbound calls, provider calls, and production-readiness claims.

Current non-PROD runtime reasoner layer: `DIALOGUE-REASONER-001`, documented in `docs/product/DIALOGUE_REASONER_001_STRUCTURED_RUNTIME_REASONER.md`, freezes 30 live-demo dialogue-act cases and adds `runtime/core/dialogue_reasoner.py` while keeping LLM/provider calls default-off and `PROD-102` closed. `DIALOGUE-REASONER-002`, documented in `docs/product/DIALOGUE_REASONER_002_LLM_PROVIDER_EVALUATION.md`, adds the default-off OpenAI-compatible provider evaluation harness for those same cases. `DIALOGUE-REASONER-003`, documented in `docs/product/DIALOGUE_REASONER_003_HYBRID_GATE_EVALUATION.md`, adds the hybrid gate evaluation where deterministic runtime labels stay protected and provider reasoning can only enrich allowed turns. `DIALOGUE-REASONER-004`, documented in `docs/product/DIALOGUE_REASONER_004_ASYNC_ENRICHMENT.md`, wires that enrichment as an optional async/background packet and attaches it to `LIVE-DEMO-001` private evidence only: deterministic customer response availability is proven before provider results, route override and final-response mutation stay blocked, provider calls remain default-off, and `PROD-102` remains closed.

Current dialogue control-plane checkpoint: `LIVE-DEMO-014-clear-pain-callback-followup`, documented in `docs/product/LIVE_DEMO_014_CLEAR_PAIN_CALLBACK_FOLLOWUP.md`, builds on `DIALOGUE-MANAGER-003-plain-sales-clarity-and-vague-appointment-time` and the manager/pragmatics layer. It acknowledges `it's all clear`, uses stated missed callbacks to move toward a Northstar workflow-review ask without callback-scheduling ambiguity, explains `Growth` if asked, treats appointment hesitation as callback follow-up instead of a stop, and keeps callback-later agreement open until a usable time is captured. It preserves `LIVE-DEMO-001` through `LIVE-DEMO-013`, keeps appointment-setting as the MVP close, does not install or wire a local LLM, and keeps `PROD-102`, payment collection, contracts, provider ASR, provider-hosted durable agents, voice cloning, LLM-written final speech, real customer use, production promotion, and full autonomous sale closure blocked.

Preserved live-demo checkpoint IDs include `LIVE-DEMO-002-conversation-stability-callback-disambiguation`, `LIVE-DEMO-003-supervised-live-voice-acceptance`, `LIVE-DEMO-004-realtime-turn-taking-asr-vad`, `LIVE-DEMO-005-interrupt-pace-plan-precision`, `LIVE-DEMO-006-memory-transcript-visibility`, `LIVE-DEMO-007-human-readable-transcript-and-plain-qualification`, `LIVE-DEMO-008-prosody-review-scope-clarity`, `LIVE-DEMO-009-appointment-lead-close`, `LIVE-DEMO-010-live-feedback-route-polish`, `LIVE-DEMO-011-live-followup-stop-and-pain-close`, `LIVE-DEMO-012-soft-stop-and-context-recovery`, `LIVE-DEMO-013-reasoner-route-guard`, and `LIVE-DEMO-014-clear-pain-callback-followup`.

## Brain

- `docs/brain/BRAIN_001_PROJECT_BRAIN_ARCHITECTURE.md`
- `docs/brain/BRAIN_002_RUNTIME_STATE_SCHEMA.md`
- `docs/brain/PROD_011_DIALOGUE_POLICY_HARDENING.md`

## Product Decision Layer

- `PROD_007_FULL_CALL_GAUNTLET.md`
- `PROD_008_GENERATED_FULL_CALL_PACKETS.md`
- `PROD_009_CROSS_DOMAIN_GENERATED_GAUNTLET.md`
- `PROD_010_LONG_CALL_UNIVERSAL_OBJECTIONS.md`
- `PROD_012_CALLCENTEREN_SCENARIO_EVALUATION.md`
- `PROD_013_CALLCENTEREN_PATTERN_EXTRACTION.md`
- `PROD_014_CALLCENTEREN_SCENARIO_BANK.md`
- `PROD_015_CALLCENTEREN_RUNTIME_COMPARISON.md`
- `PROD_016_CALLCENTEREN_RETRIEVAL_NO_GAIN_DIAGNOSIS.md`
- `PROD_017_CALLCENTEREN_SPECIFICITY_SCORING.md`
- `PROD_018_CALLCENTEREN_COMPOSER_HOOK_TEST.md`
- `PROD_019_GUARDED_RUNTIME_COMPOSER_HOOKS.md`
- `PROD_020_NATURALIZED_CUSTOMER_TURN_EVALUATION.md`
- `PROD_021_LIVE_SHAPED_DIALOGUE_POLICY_SIMULATION.md`
- `PROD_022_PROD_021_REVIEW_GAP_PACKET.md`
- `PROD_023_RUNTIME_POLICY_CALL_CONTROL_FIX.md`
- `PROD_024_LIVE_SHAPED_POST_FIX_RERUN.md`
- `PROD_025_BOUNDED_DEMO_READINESS_PACKET.md`
- `PROD_026_LOCAL_DEMO_TRACE_HARNESS.md`
- `PROD_027_FULL_SCENARIO_ROUTE_EVALUATION.md`
- `PROD_028_SYNTHETIC_CAMPAIGN_KNOWLEDGE_GROUNDING.md`
- `PROD_029_GROUNDED_FULL_SCENARIO_RERUN.md`
- `PROD_030_GROUNDED_DEMO_REVIEW.md`
- `PROD_031_INTERACTIVE_GROUNDED_CALL_SIMULATION.md`
- `PROD_032_INTERACTIVE_SIMULATION_REVIEW.md`
- `PROD_033_INTERACTIVE_SIMULATOR_TERMINATION_FIX.md`
- `PROD_034_INTERACTIVE_POST_FIX_REVIEW.md`
- `PROD_035_RUNTIME_DECISION_TRACE_ALIGNMENT.md`
- `PROD_036_INTERACTIVE_DEMO_READINESS_REVIEW.md`
- `PROD_037_LOCAL_INTERACTIVE_TRACE_DEMO_SURFACE.md`
- `PROD_038_LOCAL_DEMO_SURFACE_REVIEW.md`
- `PROD_039_CUSTOMER_REALISM_SIMULATOR_HARDENING.md`
- `PROD_040_CALLCENTEREN_CONDITIONAL_CUSTOMER_SIMULATION.md`
- `PROD_041A_CONDITIONAL_SCENARIO_DIVERSITY_EXPANSION.md`
- `PROD_041_CONDITIONAL_SIMULATION_REVIEW.md`
- `PROD_042_CALLCENTEREN_TURN_PATTERN_PLAYBOOK.md`
- `PROD_043_SALES_PLAYBOOK_RUNTIME_ADAPTER.md`
- `PROD_044_CORE_SALES_POLICY_UPDATE.md` (`PROD-044`)
- `PROD_045_CORE_SALES_POLICY_REGRESSION_RERUN.md`
- `PROD_046A_GERMAN_NATURALIZED_POLICY_REGRESSION.md`
- `PROD_046B_GERMAN_RESPONSE_WORDING_QUALITY_PASS.md`
- `PROD_046C_GERMAN_CAMPAIGN_FIELD_INTERPOLATION_GUARD.md`
- `PROD_046D_GERMAN_SOURCE_INFORMED_WORDING_QUALITY_GUARD.md`
- `PROD_046_CORE_SALES_POLICY_HUMAN_REVIEW.md`
- `PROD_047_CAMPAIGN_PROFILE_CONTRACT_VALIDATOR.md`
- `PROD_048A_NATIVE_GERMAN_REVIEW_HTML_PACKET.md`
- `PROD_048A_GERMAN_REVIEW_HTML_AND_BREVITY_PACKET.md`
- `PROD_048B_NATIVE_GERMAN_REVIEW_IMPORT.md`
- `PROD_048C_GERMAN_WORDING_FEEDBACK_PATCH.md`
- `PROD_049_SAFE_END_CALL_BRIDGE_CONTINUE_REVIEW.md`
- `PROD_050_SAFE_CALL_CONTROL_SOFTENING_REGRESSION.md`
- `PROD_051_SAFE_CALL_CONTROL_RUNTIME_UPDATE.md`
- `PROD_052_LANGUAGE_LANE_REVIEW_SEPARATION.md`
- `PROD_053A_ENGLISH_SALES_PSYCHOLOGY_DEEP_DIVE.md`
- `PROD_053B_COMPACT_ENGLISH_PSYCHOLOGY_LAYER_REVIEW.md`
- `PROD_053C_ENGLISH_SPOKEN_RESPONSE_EXPANSION_REVIEW.md`
- `PROD_053D_ENGLISH_REVIEW_IMPORT.md`
- `PROD_053E_ENGLISH_RUNTIME_WORDING_PATCH.md`
- `PROD_054_ENGLISH_MULTI_TURN_NATURALNESS_STRESS_REVIEW.md`
- `PROD_055_ENGLISH_MULTI_TURN_RUNTIME_PATCH.md`
- `PROD_056_ENGLISH_POST_PATCH_MULTI_TURN_REGRESSION.md`
- `PROD_057_ENGLISH_MULTI_TURN_REGRESSION_GUARD_DECISION.md`
- `PROD_058_ENGLISH_RUNTIME_PROMOTION_BLOCKER_INVENTORY.md`
- `PROD_059_FINAL_ENGLISH_ONLY_RUNTIME_READINESS_REVIEW.md`
- `PROD_060_RUNTIME_PROMOTION_PATH_DECISION.md`
- `PROD_061_ENGLISH_PRODUCT_POLICY_GATE_PRIORITIZATION.md`
- `PROD_062_ENGLISH_CONTEXT_SENSITIVE_AUTONOMY_POLICY_PROBE.md`
- `PROD_063_ENGLISH_AUTONOMY_CHECK_RUNTIME_WORDING_PATCH.md`
- `PROD_064_ENGLISH_AUTONOMY_POST_PATCH_MULTI_TURN_REGRESSION.md`
- `PROD_065_ENGLISH_REMAINING_PRODUCT_POLICY_GATE_SELECTION.md`
- `PROD_066_ENGLISH_VOICEMAIL_ACTION_ONLY_POLICY_PROBE.md`
- `PROD_067_ENGLISH_VOICEMAIL_ACTION_ONLY_RUNTIME_PATCH.md`
- `PROD_068_ENGLISH_VOICEMAIL_POST_PATCH_REGRESSION.md`
- `PROD_069_ENGLISH_REMAINING_PRODUCT_POLICY_GATE_SELECTION_AFTER_VOICEMAIL.md`
- `PROD_070_ENGLISH_COVERAGE_KNOWLEDGE_POLICY_PROBE.md`
- `PROD_071_ENGLISH_COVERAGE_KNOWLEDGE_RUNTIME_PATCH.md`
- `PROD_072_ENGLISH_COVERAGE_KNOWLEDGE_POST_PATCH_REGRESSION.md`
- `PROD_073_ENGLISH_CUSTOMER_MOVE_CLASSIFICATION_GATE_DECISION.md`
- `PROD_074_ENGLISH_CUSTOMER_MOVE_CLASSIFICATION_SLICE_INVENTORY.md`
- `PROD_075_ENGLISH_PROVIDER_COMPARISON_REACHABILITY_REVIEW.md`
- `PROD_076_ENGLISH_PROVIDER_COMPARISON_REVIEW_IMPORT.md`
- `PROD_077_ENGLISH_PROVIDER_COMPARISON_NARROW_PROBE_DESIGN.md`
- `PROD_078_ENGLISH_PROVIDER_COMPARISON_RUNTIME_PATCH.md`
- `PROD_079_ENGLISH_PROVIDER_COMPARISON_POST_PATCH_REGRESSION.md`
- `PROD_080_ENGLISH_CUSTOMER_MOVE_REMAINING_SLICE_SELECTION.md`
- `PROD_081_ENGLISH_UNKNOWN_RUNTIME_SIGNAL_SUBTYPE_INVENTORY.md`
- `PROD_082_ENGLISH_GUIDED_OPTION_SELECTION_REVIEW.md`
- `PROD_083_ENGLISH_GUIDED_OPTION_SELECTION_REVIEW_IMPORT.md`
- `PROD_084_ENGLISH_GUIDED_OPTION_SELECTION_REWRITE_DESIGN.md`
- `PROD_085_ENGLISH_GUIDED_OPTION_SELECTION_REWRITE_REVIEW_IMPORT.md`
- `PROD_086_ENGLISH_GUIDED_OPTION_SELECTION_NARROW_POLICY_PROBE.md`
- `PROD_087_ENGLISH_GUIDED_OPTION_SELECTION_RUNTIME_PATCH.md`
- `PROD_088_ENGLISH_GUIDED_OPTION_SELECTION_POST_PATCH_REGRESSION.md`
- `PROD_089_ENGLISH_CUSTOMER_MOVE_REMAINING_SLICE_SELECTION_AFTER_GUIDED_OPTION.md`
- `PROD_090_ENGLISH_GUIDED_OPTION_SYNONYM_COVERAGE_NARROW_PROBE.md`
- `PROD_091_ENGLISH_GUIDED_OPTION_SYNONYM_COVERAGE_RUNTIME_PATCH.md`
- `PROD_092_ENGLISH_GUIDED_OPTION_SYNONYM_COVERAGE_POST_PATCH_REGRESSION.md`
- `PROD_093_ENGLISH_CUSTOMER_MOVE_REMAINING_SLICE_SELECTION_AFTER_GUIDED_OPTION_SYNONYMS.md`
- `PROD_094_ENGLISH_NEXT_STEP_PROCESS_CLARITY_NARROW_PROBE.md`
- `PROD_095_ENGLISH_NEXT_STEP_PROCESS_CLARITY_RUNTIME_PATCH.md`
- `PROD_096_ENGLISH_NEXT_STEP_PROCESS_CLARITY_POST_PATCH_REGRESSION.md`
- `PROD_097_ENGLISH_CUSTOMER_MOVE_REMAINING_SLICE_SELECTION_AFTER_PROCESS_CLARITY.md`
- `PROD_098_ENGLISH_RECOMMENDATION_ROLEPLAY_REVIEW_IMPORT.md`
- `PROD_099_ENGLISH_RECOMMENDATION_ROLEPLAY_NARROW_POLICY_PROBE.md`
- `PROD_100_ENGLISH_RECOMMENDATION_ROLEPLAY_RUNTIME_PATCH.md`
- `PROD_101_ENGLISH_RECOMMENDATION_ROLEPLAY_POST_PATCH_REGRESSION.md`

Current PROD-041A scope: interactive conditional customer simulation with `customer_reaction_policy_bank.json`, `interactive_scenario_profiles.json`, and `interaction_traces.json`; it is not a fixed scripted-dialogue generator. It now validates agent reactivity too: each agent turn must address the immediately previous customer intent, avoid repeated answers, avoid looping questions, and avoid false safe closes.
Current forward layer: `PROD-101-english-recommendation-roleplay-post-patch-regression`, which verifies the approved English `recommendation-roleplay-boundary` runtime route after `PROD-100` applied it. It records recommendation roleplay positive failures: `0`, adjacent control failures: `0`, stable English guard passed: `true`, requires customer facts for recommendation: `true`, requires agency preservation: `true`, no agent decides for customer: `true`, no value guarantee: `true`, review HTML created: `false`, do not open the next checkpoint in this run: `true`, changes no runtime behavior, response text behavior, or classifier behavior inside the regression checkpoint, and keeps retrieval defaults, provider calls, LLM calls, private-data reads, German exact-phrase promotion, voice playback, public demo use, real customer use, payment collection, contract signing, legal compliance, and production runtime promotion blocked. `PROD-048D-native-german-followup-review-import` remains parked until the corrected native German reviewer export exists. Full native German approval, legal compliance, German exact-phrase acceptance, broad customer-move classification expansion, retrieval defaults, provider calls, LLM calls, private-data reads, voice playback, public demo use, real customer use, payment collection, contract signing, and production runtime promotion remain blocked.
Current live-demo/control-plane checkpoint: `LIVE-DEMO-014-clear-pain-callback-followup` is the resumed work before any `PROD-102` or production-promotion effort. It is supervised demo hardening after `DIALOGUE-MANAGER-003`: clear/no-pain replies should be acknowledged, stated missed callbacks should lead toward the workflow-review ask without callback-scheduling ambiguity, unexplained `Growth` wording should be corrected if asked, appointment hesitation should become low-pressure callback follow-up, and appointment-setting remains the current MVP close, not full production sales closure, payment collection, or LLM-driven final speech.

Older product simulation notes live in `research/experiments/` as `PROD-001` through `PROD-005`, with product strategy docs in this folder.

## Retrieval And RAG

- `RAG_001_NOTEBOOKLM_SOURCE_INTAKE_BRIDGE.md` through `RAG_018_GUARDED_RUNTIME_RETRIEVAL.md`
- `RAG_019_SALES_COMMUNICATION_SOURCE_EXPANSION.md`
- `RAG_020_SALES_PERSUASION_EMOTION_DEEP_DIVE.md`
- `RAG_021_BUYER_TRUST_CONVERSATION_REPAIR.md`
- `RAG_022_UNIVERSAL_SALES_LAYER_CONTRACT.md`

Runtime rule: retrieval remains disabled by default unless a separate RAG gate explicitly promotes it.

## Response Runtime

- `RESP_001_GUARDED_RESPONSE_GENERATION.md`
- `RESP_002_RUNTIME_VOICE_DELIVERY.md`
- `RESP_003_RUNTIME_LIVE_TTS.md`
- `RESP_004_VOICE_044_LISTENING_CHECK.md`
- `RESP_005_RUNTIME_VERSION_AB_LISTENING_CHECK.md`
- `RESP_006_GERMAN_RUNTIME_VERSION_AB_LISTENING_CHECK.md`
- `RESP_007_GERMAN_PACING_STABILITY_FOLLOW_UP.md`

Current voice blocker: record the `RESP-007` German pacing-stability listening decision before promoting a voice-personality selector.

## Voice

- `VOICE_001_TTS_PROTOTYPE.md` through `VOICE_044_BASELINE_DELIVERY_POLISH.md`
- Provider boundary: `runtime/providers/VOICE_PROVIDER_RUN_BOUNDARY.md`
- Generated audio log: `runtime/providers/VOICE_GENERATED_AUDIO_ASSET_LOG.md`

Default rule: dry-run/offline unless a command explicitly uses `--live` and provider boundary review is complete.

## Core Product Docs

- `PRODUCT_BRIEF.md`
- `GO_LIVE_MVP_DEFINITION_AND_ROADMAP.md`
- `LIVE_DEMO_001_AGENT_VOICE_CALL.md`
- `LIVE_DEMO_002_RUNTIME_EXTRACTION_BASELINE.md`
- `LIVE_DEMO_002_CONVERSATION_STABILITY_CALLBACK_DISAMBIGUATION.md`
- `LIVE_DEMO_003_SUPERVISED_LIVE_VOICE_ACCEPTANCE.md`
- `LIVE_DEMO_004_REALTIME_TURN_TAKING_ASR_VAD.md`
- `LIVE_DEMO_005_INTERRUPT_PACE_PLAN_PRECISION.md`
- `LIVE_DEMO_006_MEMORY_TRANSCRIPT_VISIBILITY.md`
- `LIVE_DEMO_007_HUMAN_TRANSCRIPT_PLAIN_QUALIFICATION.md`
- `LIVE_DEMO_008_PROSODY_REVIEW_SCOPE_CLARITY.md`
- `LIVE_DEMO_009_APPOINTMENT_LEAD_CLOSE.md`
- `LIVE_DEMO_010_LIVE_FEEDBACK_ROUTE_POLISH.md`
- `LIVE_DEMO_011_LIVE_FOLLOWUP_STOP_AND_PAIN_CLOSE.md`
- `LIVE_DEMO_012_SOFT_STOP_AND_CONTEXT_RECOVERY.md`
- `LIVE_DEMO_013_REASONER_ROUTE_GUARD.md`
- `DIALOGUE_MANAGER_001_ROOT_REPAIR.md`
- `DIALOGUE_MANAGER_002_PRAGMATIC_DIALOGUE_REPAIR.md`
- `DIALOGUE_MANAGER_003_PLAIN_SALES_CLARITY_AND_VAGUE_APPOINTMENT_TIME.md`
- `FULL_SALE_MVP_STRATEGY.md`
- `CLIENT_MVP_WORKFLOW.md`
- `runtime/architecture/REALTIME_AGENT_ARCHITECTURE.md`
- `runtime/entrypoints/REALTIME_TURN_CLI.md`
- `runtime/policy/CALL_TERMINATION_POLICY.md`
- `SALES_DIFFICULTY_TAXONOMY.md`
- `CORE_SALES_DELIVERY_PLAYBOOK.md`
- `COMMANDS.md`

## Current Phase C1 evidence-admission checkpoint: `EMOTION-STATE-004`

Canonical status: accepted. Overall decision: defer_c2. Per-signal decisions:
hesitation=defer; frustration=defer; confusion=defer; interest=defer;
disengagement=defer. C2-eligible signals: none. Counts:
queries=88; sources=0; cards=0.

Protocol/search/source/source-review SHA-256:
`2540A1BA430F78B9F660BA466F6CFD7099CFFCAA6F1C1D1AC373F4BA1D4D2CCD` /
`A6FCAA50123E4D67FF92D36E9755B4ED7C82306FCAA50B72ED26A478361365DB` /
`81FB1301287F0E3E8FA0E21840B1B596028509C11FAAC75D6D6F8914051D0B58` /
`4B489D77BFC948B84F8A6BC73A30DC1068138D6ABD2A563EB7FD43BFE9224E11`.
Candidate receipt / validation / review SHA-256:
`B0CB4466B5AEA3C76A890F9BE5523448FC609888705B2F6815587E21453D6424` /
`5478BE04D396356A4CFE80F048F39D6B4AB855395EB3404FC2B58F4699DDFB0D` /
`3B8D9F874990C9C2FBE1664FE1155392984D278FFB4F5E9BB74913469F8D0336`.
Canonical result / report SHA-256:
`8F9B8D1EB088CC7025F77F34FF83928C53DA2112A0A0D300E59DD5C7A7C3D637` /
`15B5285A8B18E9E8C5A36A71CBB8202EF0F72370C91F9CB8AD80271F8BF38CDD`.
Source review: admitted (C0/I0/M0). Candidate review: admitted (C0/I0/M0).
The pair-only checkpoint commit is `d1f78f321f4d01512944dfa7499d819cb10d7a5c`.

The pair is an immutable rowless admission-defer checkpoint. It does not infer
customer emotion or prove model, real-call, provider, latency, safety,
conversion, production, or commercial behavior; it authorizes neither C2 nor
runtime. No private data, dataset/annotation rows, audio, or transcripts were
read. No provider access, call, simulation, model evaluation, runtime
modification/activation, or Phase B lockbox access occurred. Push and merge
remain separate gates.
