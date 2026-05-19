# Checkpoint Index

This index groups checkpoint docs by work track. Runners, validators, cases, and generated reports stay in `scripts/`, `research/experiments/cases/`, and `research/experiments/generated/`.

Runtime-affecting files now live under `runtime/` and are mapped in `runtime/runtime_manifest.json`; use it before editing spoken-text, call-control, campaign-contract, retrieval, or provider-delivery behavior. Legacy `scripts/*` runtime files are compatibility wrappers.

Current non-PROD runtime reasoner layer: `DIALOGUE-REASONER-001`, documented in `docs/product/DIALOGUE_REASONER_001_STRUCTURED_RUNTIME_REASONER.md`, freezes 30 live-demo dialogue-act cases and adds `runtime/core/dialogue_reasoner.py` while keeping LLM/provider calls default-off and `PROD-102` closed. `DIALOGUE-REASONER-002`, documented in `docs/product/DIALOGUE_REASONER_002_LLM_PROVIDER_EVALUATION.md`, adds the default-off OpenAI-compatible provider evaluation harness for those same cases. `DIALOGUE-REASONER-003`, documented in `docs/product/DIALOGUE_REASONER_003_HYBRID_GATE_EVALUATION.md`, adds the hybrid gate evaluation where deterministic runtime labels stay protected and provider reasoning can only enrich allowed turns. `DIALOGUE-REASONER-004`, documented in `docs/product/DIALOGUE_REASONER_004_ASYNC_ENRICHMENT.md`, wires that enrichment as an optional async/background packet and attaches it to `LIVE-DEMO-001` private evidence only: deterministic customer response availability is proven before provider results, route override and final-response mutation stay blocked, provider calls remain default-off, and `PROD-102` remains closed.

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

Older product simulation notes live in `research/experiments/` as `PROD-001` through `PROD-005`, with product strategy docs in this folder.

## Retrieval And RAG

- `RAG_001_NOTEBOOKLM_SOURCE_INTAKE_BRIDGE.md` through `RAG_018_GUARDED_RUNTIME_RETRIEVAL.md`
- `RAG_019_SALES_COMMUNICATION_SOURCE_EXPANSION.md`
- `RAG_020_SALES_PERSUASION_EMOTION_DEEP_DIVE.md`
- `RAG_021_BUYER_TRUST_CONVERSATION_REPAIR.md`

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
- `FULL_SALE_MVP_STRATEGY.md`
- `CLIENT_MVP_WORKFLOW.md`
- `runtime/architecture/REALTIME_AGENT_ARCHITECTURE.md`
- `runtime/entrypoints/REALTIME_TURN_CLI.md`
- `runtime/policy/CALL_TERMINATION_POLICY.md`
- `SALES_DIFFICULTY_TAXONOMY.md`
- `CORE_SALES_DELIVERY_PLAYBOOK.md`
- `COMMANDS.md`
