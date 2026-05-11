# Product Command Map

Run commands from the repo root:

```powershell
cd D:\Codex\active\emotion-aware-ai-sales-agent
```

Default commands should stay local and offline. Commands that can call external providers are listed separately under "Explicit opt-in provider commands".

## Setup

Check the local product workspace without installing dependencies, calling providers, or printing secret values:

```powershell
python scripts\check_setup.py
```

Machine-readable setup check:

```powershell
python scripts\check_setup.py --json
```

Validate the setup checker itself:

```powershell
python scripts\validate_check_setup.py
```

Validate that required project policies are local to Emotion Aware and scripts do not hard-depend on other `D:\Codex` workspace projects:

```powershell
python scripts\validate_self_contained_project_policy.py
```

Detect project drift such as missing guard docs, conflict markers, secret-like values, unignored generated audio, or hidden dependencies on another local workspace project:

```powershell
python scripts\check_project_drift.py
```

Machine-readable drift check:

```powershell
python scripts\check_project_drift.py --json
```

Validate the drift guard itself:

```powershell
python scripts\validate_project_drift_guard.py
```

Check that external source URLs used in docs, research cases, scripts, and prompt/runtime notes are captured in the thesis reference registry or third-party inspiration log:

```powershell
python scripts\check_thesis_reference_registry.py
```

Validate the thesis reference registry guard:

```powershell
python scripts\validate_thesis_reference_registry.py
```

Check that product, research, runtime, prompt, data, or workflow changes are accompanied by thesis-tracking documentation before a GitHub checkpoint:

```powershell
python scripts\check_thesis_update_gate.py
```

Validate the thesis update gate:

```powershell
python scripts\validate_thesis_update_gate.py
```

Validate the private call-center data boundary without scanning private file contents:

```powershell
python scripts\validate_private_data_boundary.py
```

Check the private call-center learning scaffold without scanning private file contents:

```powershell
python scripts\check_private_call_learning_pipeline.py
```

Validate the private call-center learning checker and policy:

```powershell
python scripts\validate_private_call_learning_pipeline.py
```

Preview the ignored private-call learning workspace folders:

```powershell
python scripts\init_private_call_learning_workspace.py --dry-run
```

Create the ignored private-call learning workspace folders when private audio is ready:

```powershell
python scripts\init_private_call_learning_workspace.py
```

Validate local voice-ID config resolution without printing raw voice IDs:

```powershell
python scripts\validate_local_voice_config.py
```

Optional local ElevenLabs voice IDs can be stored in ignored config:

```powershell
Copy-Item config\local\voice_ids.example.json config\local\voice_ids.json
```

Then edit `config\local\voice_ids.json` locally. Do not put API keys in this file.

## Relevant File Reading

Use this when a file is large and you only need the useful part. It reads local repo files only, blocks secret/private paths, makes no network calls, and returns small slices.

Project working rule: use `scripts/read_relevant.py` before full-file reads for large Markdown docs, thesis logs, roadmaps, command maps, generated reports, policy files, and review-gate files. Start with `outline`, `section`, `find`, or `slice`, then do a full read only when the smaller read is not enough.

Show headings and lightweight symbols:

```powershell
python scripts\read_relevant.py outline --path docs\product\COMMANDS.md
```

Read a bounded line range:

```powershell
python scripts\read_relevant.py slice --path docs\product\COMMANDS.md --start 11 --end 30
```

Find matching lines with nearby context:

```powershell
python scripts\read_relevant.py find --path docs\product\COMMANDS.md --query "Cartesia" --context 1
```

Read a Markdown section by heading:

```powershell
python scripts\read_relevant.py section --path docs\product\COMMANDS.md --heading "Setup"
```

Validate the reader:

```powershell
python scripts\validate_read_relevant.py
```

Validate that the automatic context-reading rule is still wired into project instructions and docs:

```powershell
python scripts\validate_context_reading_policy.py
```

## RAG Source Intake

Run the RAG-001 NotebookLM source-intake bridge in local dry-run mode:

```powershell
python scripts\run_rag_001_notebooklm_source_intake.py
```

Default RAG-001 output folder:

```text
research\experiments\generated\RAG-001-notebooklm-source-intake-bridge\
```

Validate RAG-001 source taxonomy, source manifest rules, NotebookLM extraction prompt, source-tracked chunks, and no-private-data/no-provider boundary:

```powershell
python scripts\validate_rag_001_notebooklm_source_intake.py
```

Run the RAG-002 NotebookLM extraction automation bridge to create bounded per-topic report prompts, optional JSON prompts, and import folders:

```powershell
python scripts\run_rag_002_notebooklm_extraction_automation.py
```

Use `research\experiments\generated\RAG-002-notebooklm-extraction-automation-bridge\prompts\00-configure-chat-custom-instructions.md` in NotebookLM Configure Chat > Custom before creating reports. Keep NotebookLM response length set to `Longer`.

For each topic, use `01-create-report-file.md` inside NotebookLM Reports / Create report first. Use `02-chat-json-extraction.md` only if a stricter JSON handoff is needed after the report exists.

Default RAG-002 output folder:

```text
research\experiments\generated\RAG-002-notebooklm-extraction-automation-bridge\
```

Validate RAG-002 prompt character limits, exhaustive-report wording, completion markers, and small-batch rejection:

```powershell
python scripts\validate_rag_002_notebooklm_extraction_automation.py
```

Run the RAG-003 report import-readiness audit after NotebookLM reports have been exported or pasted into the RAG-002 imports folder:

```powershell
python scripts\run_rag_003_report_import_readiness.py
```

Default RAG-003 output folder:

```text
research\experiments\generated\RAG-003-report-import-readiness\
```

Validate RAG-003 report scanning, topic coverage, source-ID mapping detection, and no-runtime-retrieval boundary:

```powershell
python scripts\validate_rag_003_report_import_readiness.py
```

Run RAG-004 source manifest normalization after RAG-003 shows all report topics are covered:

```powershell
python scripts\run_rag_004_source_manifest_normalization.py
```

Default RAG-004 output folder:

```text
research\experiments\generated\RAG-004-source-manifest-normalization\
```

Validate RAG-004 stable source-ID generation, metadata-review flags, and no-runtime-retrieval boundary:

```powershell
python scripts\validate_rag_004_source_manifest_normalization.py
```

Run RAG-005 chunk normalization after RAG-004 creates the source manifest:

```powershell
python scripts\run_rag_005_chunk_normalization.py
```

Default RAG-005 output folder:

```text
research\experiments\generated\RAG-005-chunk-normalization\
```

Validate RAG-005 chunk extraction, source-ID mapping, topic review flags, source-excerpt suppression, and no-runtime-retrieval boundary:

```powershell
python scripts\validate_rag_005_chunk_normalization.py
```

Run RAG-006 chunk review packet generation after RAG-005 creates chunk candidates:

```powershell
python scripts\run_rag_006_chunk_review_packet.py
```

Default RAG-006 output folder:

```text
research\experiments\generated\RAG-006-chunk-review-packet\
```

Validate RAG-006 source-mapping queues, topic-review queues, quote-review queues, first-slice candidates, and no-runtime-retrieval/no-promotion boundary:

```powershell
python scripts\validate_rag_006_chunk_review_packet.py
```

Run RAG-007 reviewed first-slice promotion after RAG-006 creates review queues:

```powershell
python scripts\run_rag_007_reviewed_first_slice.py
```

Default RAG-007 output folder:

```text
research\experiments\generated\RAG-007-reviewed-first-slice\
```

Validate RAG-007 reviewed paraphrases, selected chunk IDs, pressure-tactic exclusions, no-source-excerpt storage, and no-runtime-retrieval boundary:

```powershell
python scripts\validate_rag_007_reviewed_first_slice.py
```

Run RAG-008 guarded retrieval policy dry-run after RAG-017 creates the runtime knowledge registry:

```powershell
python scripts\run_rag_008_guarded_retrieval_policy.py
```

Default RAG-008 output folder:

```text
research\experiments\generated\RAG-008-guarded-retrieval-policy\
```

Validate RAG-008 deterministic candidate packets, hard-block contexts, citation traces, advisory-only voice/prosody guidance, and no-runtime-retrieval boundary:

```powershell
python scripts\validate_rag_008_guarded_retrieval_policy.py
```

Run RAG-009 all-source review coverage after RAG-004 through RAG-007 artifacts exist:

```powershell
python scripts\run_rag_009_all_source_review_coverage.py
```

Default RAG-009 output folder:

```text
research\experiments\generated\RAG-009-all-source-review-coverage\
```

Validate RAG-009 all-source/source-chunk accounting, blocked queues, next-promotion candidates, no source-excerpt storage, and no-runtime-retrieval boundary:

```powershell
python scripts\validate_rag_009_all_source_review_coverage.py
```

Run RAG-010 reviewed expansion slice after RAG-009 creates clean next-promotion candidates:

```powershell
python scripts\run_rag_010_reviewed_expansion_slice.py
```

Default RAG-010 output folder:

```text
research\experiments\generated\RAG-010-reviewed-expansion-slice\
```

Validate RAG-010 reviewed paraphrases, cadence-as-weak-context guardrails, no source-excerpt storage, and no-runtime-retrieval boundary:

```powershell
python scripts\validate_rag_010_reviewed_expansion_slice.py
```

Run RAG-011 blocker cleanup packet after RAG-009/RAG-010 identify remaining source-mapping and quote-clearance blockers:

```powershell
python scripts\run_rag_011_blocker_cleanup_packet.py
```

Default RAG-011 output folder:

```text
research\experiments\generated\RAG-011-blocker-cleanup-packet\
```

Validate RAG-011 cleanup proposals, quote-clearance cards, no blocker mutation, no source-excerpt storage, and no-runtime-retrieval boundary:

```powershell
python scripts\validate_rag_011_blocker_cleanup_packet.py
```

Run RAG-012 accepted cleanup after the RAG-011 source-mapping proposals and quote-clearance cards are human-accepted:

```powershell
python scripts\run_rag_012_accepted_cleanup.py
```

Default RAG-012 output folder:

```text
research\experiments\generated\RAG-012-accepted-cleanup\
```

Validate RAG-012 accepted source mappings, project-owned quote-clearance rewrites, follow-up flags, no source-excerpt storage, and no-runtime-retrieval boundary:

```powershell
python scripts\validate_rag_012_accepted_cleanup.py
```

Run RAG-013 cleanup strategy after RAG-012 records accepted cleanup decisions:

```powershell
python scripts\run_rag_013_cleanup_strategy.py
```

Default RAG-013 output folder:

```text
research\experiments\generated\RAG-013-cleanup-strategy\
```

Validate RAG-013 remaining cleanup counts, source-mapping batches, quote-clearance lane counts, recommended next checkpoint, no source-excerpt storage, and no-runtime-retrieval boundary:

```powershell
python scripts\validate_rag_013_cleanup_strategy.py
```

Run RAG-014 source-mapped quote follow-up review after RAG-013 identifies the five follow-up cards:

```powershell
python scripts\run_rag_014_source_mapped_quote_followup.py
```

Default RAG-014 output folder:

```text
research\experiments\generated\RAG-014-source-mapped-quote-followup\
```

Validate RAG-014 accepted project-owned paraphrases, rejected pressure/control candidate, zero remaining source-mapped quote follow-ups, no source-excerpt storage, and no-runtime-retrieval boundary:

```powershell
python scripts\validate_rag_014_source_mapped_quote_followup.py
```

Run RAG-015 source-mapping batches after RAG-014 clears the accepted-source follow-up queue:

```powershell
python scripts\run_rag_015_source_mapping_batches.py
```

Default RAG-015 output folder:

```text
research\experiments\generated\RAG-015-source-mapping-batches\
```

Validate RAG-015 source-mapping group/chunk counts, priority batches, latent quote-follow-up counts, no source-mapping decisions, no source-excerpt storage, and no-runtime-retrieval boundary:

```powershell
python scripts\validate_rag_015_source_mapping_batches.py
```

Run RAG-016 quote-clearance batches after RAG-015 organizes remaining source-mapping work:

```powershell
python scripts\run_rag_016_quote_clearance_batches.py
```

Default RAG-016 output folder:

```text
research\experiments\generated\RAG-016-quote-clearance-batches\
```

Validate RAG-016 quote-clearance chunk counts, ethical-persuasion and voice-delivery lane counts, topic batches, no quote-clearance decisions, no source-excerpt storage, and no-runtime-retrieval boundary:

```powershell
python scripts\validate_rag_016_quote_clearance_batches.py
```

Run RAG-016A quote-clearance decision slice after RAG-016 creates the review batches:

```powershell
python scripts\run_rag_016a_quote_clearance_decision_slice.py
```

Default RAG-016A output folder:

```text
research\experiments\generated\RAG-016A-quote-clearance-decision-slice\
```

Validate RAG-016A accepted ethical-persuasion rules, remaining voice-delivery blockers, no source-excerpt storage, and no-runtime-retrieval boundary:

```powershell
python scripts\validate_rag_016a_quote_clearance_decision_slice.py
```

Run RAG-016B voice-delivery decision slice after RAG-016A:

```powershell
python scripts\run_rag_016b_voice_delivery_decision_slice.py
```

Validate RAG-016B accepted voice/prosody advisory-only rules and blocker exclusions:

```powershell
python scripts\validate_rag_016b_voice_delivery_decision_slice.py
```

Run RAG-019 sales communication source expansion after public-source review:

```powershell
python scripts\run_rag_019_sales_communication_source_expansion.py
```

Default RAG-019 output folder:

```text
research\experiments\generated\RAG-019-sales-communication-source-expansion\
```

Validate RAG-019 public-source extraction, source counts, topic coverage, and no-private-data/no-runtime-default boundaries:

```powershell
python scripts\validate_rag_019_sales_communication_source_expansion.py
```

Run RAG-020 sales persuasion and emotion-understanding deep dive after public-source review:

```powershell
python scripts\run_rag_020_sales_persuasion_emotion_deep_dive.py
```

Default RAG-020 output folder:

```text
research\experiments\generated\RAG-020-sales-persuasion-emotion-deep-dive\
```

Validate RAG-020 source counts, persuasion/emotion topic coverage, and advisory-only/no-runtime-default boundaries:

```powershell
python scripts\validate_rag_020_sales_persuasion_emotion_deep_dive.py
```

RAG-020 is not imported into the runtime registry by default. A separate RAG-017 registry rebuild and RAG-018 guarded-retrieval evaluation are required before runtime use.

Run RAG-021 buyer trust and conversation-repair source expansion after public-source review:

```powershell
python scripts\run_rag_021_buyer_trust_conversation_repair.py
```

Default RAG-021 output folder:

```text
research\experiments\generated\RAG-021-buyer-trust-conversation-repair\
```

Validate RAG-021 source counts, trust/repair topic coverage, and advisory-only/no-runtime-default boundaries:

```powershell
python scripts\validate_rag_021_buyer_trust_conversation_repair.py
```

RAG-021 is not imported into the runtime registry by default. A separate RAG-017 registry rebuild and RAG-018 guarded-retrieval evaluation are required before runtime use.

Run RAG-017 runtime knowledge registry after accepted RAG slices through RAG-016B and the RAG-019 sales communication expansion:

```powershell
python scripts\run_rag_017_runtime_knowledge_registry.py
```

Validate RAG-017 registry scope, opt-in boundary, and excluded source-mapping blockers:

```powershell
python scripts\validate_rag_017_runtime_knowledge_registry.py
```

Validate RAG-018 guarded runtime retrieval integration:

```powershell
python scripts\validate_rag_018_guarded_runtime_retrieval.py
```

Validate the larger RAG-018 scripted-call simulation:

```powershell
python scripts\validate_rag_018_scripted_call_simulation.py
```

## Core Product Contract

Validate the BRAIN-001 project brain architecture boundary:

```powershell
python scripts\validate_brain_001_project_brain_architecture.py
```

Build the BRAIN-002 runtime state schema packet:

```powershell
python scripts\run_brain_002_runtime_state_schema.py
```

Validate the BRAIN-002 runtime state schema, call-control values, retrieval default-off boundary, voice/provider boundary, and non-sale correctness examples:

```powershell
python scripts\validate_brain_002_runtime_state_schema.py
```

Validate the runtime output contract used before speaking or logging agent decisions:

```powershell
python scripts\validate_product_agent_output_contract.py
```

Run a single realtime turn:

```powershell
python scripts\realtime_turn_cli.py `
  --campaign campaign-prod-005-b2c-telecom `
  --stage relevance-check `
  --transcript "Nur wenn Sie garantieren koennen, dass es stabil ist."
```

Validate the realtime turn CLI:

```powershell
python scripts\validate_realtime_turn_cli.py
```

## Product Simulations

Render a product simulation packet:

```powershell
python scripts\run_product_simulation.py `
  --cases research\experiments\cases\prod-001-qualification-simulation.json `
  --out research/experiments/generated/PROD-001/PROD-001-evaluation-packet.md `
  --export-records research/experiments/generated/PROD-001/PROD-001-db-records.json
```

Run the deterministic rule baseline:

```powershell
python scripts\run_rule_baseline.py `
  --cases research\experiments\cases\prod-004-sales-difficulty-gauntlet.json `
  --out research/experiments/generated/PROD-004/PROD-004-rule-baseline-results.json `
  --report-out research/experiments/generated/PROD-004/PROD-004-rule-baseline-report.md
```

Run the realtime latency and call-control simulation:

```powershell
python scripts\run_realtime_turn_simulation.py `
  --cases research\experiments\cases\prod-005-realtime-latency-call-control.json `
  --out research/experiments/generated/PROD-005/PROD-005-realtime-results.json `
  --report-out research/experiments/generated/PROD-005/PROD-005-realtime-report.md
```

Build the PROD-006 full-sale scenario-grounding packet without downloading the call-center dataset:

```powershell
python scripts\run_prod_006_full_sale_scenario_grounding.py
```

Validate the PROD-006 full-sale MVP strategy, dataset provenance, pattern-grounding boundary, leakage tests, hard-failure metric, non-sale correctness metric, and no-transcript-copy/no-provider default:

```powershell
python scripts\validate_prod_006_full_sale_scenario_grounding.py
```

Optional ignored local ZIP scan for leakage checks after the dataset is downloaded by explicit approval:

```powershell
python scripts\run_prod_006_full_sale_scenario_grounding.py `
  --raw-zip-dir data\external\callcenteren\raw
```

Run the PROD-007 full-call gauntlet comparing the old core against the BRAIN-002/full-sale candidate on the same fixed calls:

```powershell
python scripts\run_prod_007_full_call_gauntlet.py
```

Validate the PROD-007 full-call gauntlet, fixed-case parity, safe close rate, hard failure rate, non-sale correctness, call-control correctness, retrieval default-off boundary, and no-provider/no-private-data default:

```powershell
python scripts\validate_prod_007_full_call_gauntlet.py
```

Run the PROD-008 generated full-call packet check, where local runtime-style logic creates one BRAIN-002 state packet per turn:

```powershell
python scripts\run_prod_008_generated_full_call_packets.py
```

Validate the PROD-008 generated packet contract, state packet completeness, safe close rate, hard failure rate, non-sale correctness, call-control correctness, retrieval default-off boundary, and no-provider/no-private-data default:

```powershell
python scripts\validate_prod_008_generated_full_call_packets.py
```

Run the PROD-009 cross-domain generated gauntlet across retail, telecom, B2B software, insurance, medical equipment, home service, membership, and automotive-style calls:

```powershell
python scripts\run_prod_009_cross_domain_generated_gauntlet.py
```

Validate the PROD-009 cross-domain generated gauntlet, domain coverage, source-pattern grounding, state packet completeness, safe close rate, hard failure rate, non-sale correctness, call-control correctness, retrieval default-off boundary, and no-provider/no-private-data default:

```powershell
python scripts\validate_prod_009_cross_domain_generated_gauntlet.py
```

Run the PROD-010 long-call universal-objection gauntlet with longer multi-turn calls and repeated buyer objections:

```powershell
python scripts\run_prod_010_long_call_universal_objections.py
```

Validate the PROD-010 long-call universal-objection gauntlet, objection boundary correctness, long-call state continuity, state packet completeness, safe close rate, hard failure rate, non-sale correctness, call-control correctness, retrieval default-off boundary, and no-provider/no-private-data default:

```powershell
python scripts\validate_prod_010_long_call_universal_objections.py
```

Run the PROD-011 dialogue-policy hardening checkpoint over the PROD-010 long-call objection evidence:

```powershell
python scripts\run_prod_011_dialogue_policy_hardening.py
```

Validate the PROD-011 dialogue-policy hardening checkpoint, policy action correctness, objection stack preservation, blocked action avoidance, state-reference completeness, safe close rate, hard failure rate, non-sale correctness, call-control correctness, retrieval default-off boundary, and no-provider/no-private-data default:

```powershell
python scripts\validate_prod_011_dialogue_policy_hardening.py
```

Run the PROD-012 CallCenterEN scenario evaluation with fixed project-owned scenarios and old-core-vs-RAG-018 comparison:

```powershell
python scripts\run_prod_012_callcenteren_scenario_evaluation.py
```

Validate the PROD-012 source boundary, leakage tests, hard failure rate, non-sale correctness, scenario quality, sales/emotional handling score, and retrieval-vs-old-core comparison:

```powershell
python scripts\validate_prod_012_callcenteren_scenario_evaluation.py
```

Run the PROD-013 CallCenterEN pattern extraction checkpoint over approved local CallCenterEN ZIP/JSON/JSONL files, emitting abstract pattern labels only:

```powershell
python scripts\run_prod_013_callcenteren_pattern_extraction.py
```

Run the full local CallCenterEN extraction while capping high-volume sample records:

```powershell
python scripts\run_prod_013_callcenteren_pattern_extraction.py --max-conversations 0 --record-limit 5000
```

Validate the PROD-013 taxonomy coverage, source boundary, no-exact-script leakage guard, pattern-bank shape, timing metrics, and command/doc registration:

```powershell
python scripts\validate_prod_013_callcenteren_pattern_extraction.py
```

Run the PROD-014 scenario-bank generator from the PROD-013 abstract pattern bank:

```powershell
python scripts\run_prod_014_callcenteren_scenario_bank.py
```

Default PROD-014 output folder:

```text
research\experiments\generated\PROD-014-callcenteren-scenario-bank\
```

Validate the PROD-014 scenario packet shape, source-pattern diversity, safe-close boundary, non-sale outcomes, leakage tests, and no-runtime-promotion boundary:

```powershell
python scripts\validate_prod_014_callcenteren_scenario_bank.py
```

Run the PROD-015 old-runtime vs retrieval-runtime comparison on a stratified PROD-014 slice:

```powershell
python scripts\run_prod_015_callcenteren_runtime_comparison.py
```

Run PROD-015 on the full PROD-014 bank:

```powershell
python scripts\run_prod_015_callcenteren_runtime_comparison.py --limit-scenarios 0
```

Validate exact Q/A capture, decision traces, hard failure rate, non-sale correctness, safe-close correctness, leakage checks, and no-runtime-promotion boundary:

```powershell
python scripts\validate_prod_015_callcenteren_runtime_comparison.py
```

Run the PROD-016 diagnosis for the PROD-015 no-gain retrieval result:

```powershell
python scripts\run_prod_016_callcenteren_retrieval_no_gain_diagnosis.py
```

Validate composer influence gap, scoring blind spot, classifier mismatch, campaign/domain mismatch, and no-runtime-promotion boundary:

```powershell
python scripts\validate_prod_016_callcenteren_retrieval_no_gain_diagnosis.py
```

Run the PROD-017 evaluation-only specificity and objection-fit scorer over the fixed PROD-015 rows:

```powershell
python scripts\run_prod_017_callcenteren_specificity_scoring.py
```

Validate specificity scoring, objection-fit scoring, generic-answer penalty, fixed-case boundary, and no-runtime-promotion boundary:

```powershell
python scripts\validate_prod_017_callcenteren_specificity_scoring.py
```

Run the PROD-018 offline composer-hook test over fixed PROD-015 no-gain rows:

```powershell
python scripts\run_prod_018_callcenteren_composer_hook_test.py
```

Validate hook coverage, PROD-017 scoring gains, safety gates, fixed-case boundary, and no-runtime-promotion boundary:

```powershell
python scripts\validate_prod_018_callcenteren_composer_hook_test.py
```

Run the PROD-019 guarded runtime-composer hook candidate behind an explicit opt-in flag:

```powershell
python scripts\run_prod_019_guarded_runtime_composer_hooks.py
```

Validate default-off behavior, opt-in runtime hook behavior, PROD-017 scoring gains, safety gates, and no-default-promotion boundary:

```powershell
python scripts\validate_prod_019_guarded_runtime_composer_hooks.py
```

Run the PROD-020 naturalized customer-turn evaluation for the PROD-019 opt-in runtime hooks:

```powershell
python scripts\run_prod_020_naturalized_customer_turn_evaluation.py
```

Validate naturalized prompts, fixed scorer use, source-pattern reference preservation, safety gates, and no-default-promotion boundary:

```powershell
python scripts\validate_prod_020_naturalized_customer_turn_evaluation.py
```

Run the PROD-021 live-shaped dialogue-policy simulation for the PROD-020 opt-in runtime hooks:

```powershell
python scripts\run_prod_021_live_shaped_dialogue_policy_simulation.py
```

Validate live-shaped multi-turn cases, exact customer/agent trace visibility, protected-context preservation, safety gates, and no-default-promotion boundary:

```powershell
python scripts\validate_prod_021_live_shaped_dialogue_policy_simulation.py
```

Run the PROD-022 PROD-021 review gap packet:

```powershell
python scripts\run_prod_022_prod_021_review_gap_packet.py
```

Validate exact gap-turn extraction, policy-action miss counts, call-control miss counts, fix targets, and no-runtime-change boundary:

```powershell
python scripts\validate_prod_022_prod_021_review_gap_packet.py
```

Run the PROD-023 runtime-policy and call-control fix checkpoint:

```powershell
python scripts\run_prod_023_runtime_policy_call_control_fix.py
```

Validate the exact PROD-022 gap-turn fixes, policy-action correctness, call-control correctness, safety gates, and no-default-promotion boundary:

```powershell
python scripts\validate_prod_023_runtime_policy_call_control_fix.py
```

Run the PROD-024 live-shaped post-fix rerun:

```powershell
python scripts\run_prod_024_live_shaped_post_fix_rerun.py
```

Validate the full post-fix live-shaped policy gate, safety gates, legacy PROD-021 gate interpretation, and no-default-promotion boundary:

```powershell
python scripts\validate_prod_024_live_shaped_post_fix_rerun.py
```

Run the PROD-025 bounded demo readiness packet:

```powershell
python scripts\run_prod_025_bounded_demo_readiness_packet.py
```

Validate the bounded demo scope, blocked claims, trace contract, review gates, and no-live-provider/no-customer-data boundary:

```powershell
python scripts\validate_prod_025_bounded_demo_readiness_packet.py
```

Run the PROD-026 local demo trace harness:

```powershell
python scripts\run_prod_026_local_demo_trace_harness.py
```

Validate exact question/answer visibility, decision-process visibility, static trace outputs, and local-only/manual-review boundaries:

```powershell
python scripts\validate_prod_026_local_demo_trace_harness.py
```

Run the PROD-027 full scenario route evaluation:

```powershell
python scripts\run_prod_027_full_scenario_route_evaluation.py
```

Validate the 20-scenario / 120-turn route set, exact customer/agent traces, policy-action and call-control scoring, and source-safe local-only boundaries:

```powershell
python scripts\validate_prod_027_full_scenario_route_evaluation.py
```

Run the PROD-028 synthetic campaign knowledge grounding checkpoint:

```powershell
python scripts\run_prod_028_synthetic_campaign_knowledge_grounding.py
```

Validate the reality-patterned fictional campaign facts, same-question baseline comparison, direct-answer metrics, source reuse labels, and no-provider/no-runtime-change boundary:

```powershell
python scripts\validate_prod_028_synthetic_campaign_knowledge_grounding.py
```

Run the PROD-029 grounded full-scenario rerun:

```powershell
python scripts\run_prod_029_grounded_full_scenario_rerun.py
```

Validate the unchanged PROD-027 scenario set, old-vs-grounded answer comparison, campaign fact use, direct-answer metrics, and no-provider/no-runtime-change boundary:

```powershell
python scripts\validate_prod_029_grounded_full_scenario_rerun.py
```

Run the PROD-030 grounded demo review checkpoint:

```powershell
python scripts\run_prod_030_grounded_demo_review.py
```

Validate accepted/rejected/revise status per grounded answer and route gap, demo-ready subset selection, runtime-profile promotion block, and no-provider/no-runtime-change boundary:

```powershell
python scripts\validate_prod_030_grounded_demo_review.py
```

Run the PROD-031 interactive grounded call simulation checkpoint:

```powershell
python scripts\run_prod_031_interactive_grounded_call_simulation.py
```

Validate deterministic reactive customer state transitions, exact traces, safety boundaries, and no-provider/no-runtime-change behavior:

```powershell
python scripts\validate_prod_031_interactive_grounded_call_simulation.py
```

Run the PROD-032 interactive simulation review checkpoint:

```powershell
python scripts\run_prod_032_interactive_simulation_review.py
```

Validate trace-level finding classification, first-fix recommendation, product-grounding issue count, safety boundaries, and no-provider/no-runtime-change behavior:

```powershell
python scripts\validate_prod_032_interactive_simulation_review.py
```

Run the PROD-033 interactive simulator termination fix checkpoint:

```powershell
python scripts\run_prod_033_interactive_simulator_termination_fix.py
```

Validate cold-call openings, outcome-driven call endings, no fixed turn-limit outcome, repeat suppression, callback-state preservation, and no-provider/no-runtime-change behavior:

```powershell
python scripts\validate_prod_033_interactive_simulator_termination_fix.py
```

Run the PROD-034 interactive post-fix review checkpoint:

```powershell
python scripts\run_prod_034_interactive_post_fix_review.py
```

Validate the PROD-034 cold-opening fix, outcome-driven termination, no fixed-turn ending, no callback conversion, no repetition loop, remaining decision-snapshot mismatch counts, and no-provider/no-runtime-promotion boundary:

```powershell
python scripts\validate_prod_034_interactive_post_fix_review.py
```

Run the PROD-035 runtime decision-trace alignment checkpoint:

```powershell
python scripts\run_prod_035_runtime_decision_trace_alignment.py
```

Validate the PROD-035 opt-in decision-trace alignment, unchanged spoken answers, cleared direct-answer mismatch counts, cleared unknown-objection counts, and no-provider/no-default-promotion boundary:

```powershell
python scripts\validate_prod_035_runtime_decision_trace_alignment.py
```

Run the PROD-036 interactive demo readiness review checkpoint:

```powershell
python scripts\run_prod_036_interactive_demo_readiness_review.py
```

Validate the PROD-036 exact trace visibility, demo-ready call count, go/no-go decision, aligned decision-process visibility, and no-provider/no-runtime-promotion boundary:

```powershell
python scripts\validate_prod_036_interactive_demo_readiness_review.py
```

Run the PROD-037 local interactive trace demo surface checkpoint:

```powershell
python scripts\run_prod_037_local_interactive_trace_demo_surface.py
```

Validate the PROD-037 static trace demo surface, exact question/answer visibility, selectable call and turn counts, keyboard-accessible controls, and no-provider/no-runtime-promotion boundary:

```powershell
python scripts\validate_prod_037_local_interactive_trace_demo_surface.py
```

Run the PROD-038 local demo surface review checkpoint:

```powershell
python scripts\run_prod_038_local_demo_surface_review.py
```

Validate the PROD-038 customer-response realism rejection gate, blocked demo expansion, and no-provider/no-runtime-promotion boundary:

```powershell
python scripts\validate_prod_038_local_demo_surface_review.py
```

Run the PROD-039 customer realism simulator hardening checkpoint:

```powershell
python scripts\run_prod_039_customer_realism_simulator_hardening.py
```

Validate the PROD-039 same-case customer phrasing improvement, unchanged agent answers, unchanged decision snapshots, unchanged terminal outcomes, unchanged safety flags, and no-provider/no-runtime-promotion boundary:

```powershell
python scripts\validate_prod_039_customer_realism_simulator_hardening.py
```

Run the PROD-040 CallCenterEN conditional customer simulation checkpoint:

```powershell
python scripts\run_prod_040_callcenteren_conditional_customer_simulation.py
```

Validate the PROD-040 agent-conditioned customer replies, unique customer responses, abstract CallCenterEN pattern grounding, leakage boundary, customer-decision endings, and no-provider/no-runtime-promotion boundary:

```powershell
python scripts\validate_prod_040_callcenteren_conditional_customer_simulation.py
```

Run the PROD-041A interactive conditional customer simulation expansion checkpoint:

```powershell
python scripts\run_prod_041a_conditional_scenario_diversity_expansion.py
```

Validate the PROD-041A 40-profile, 120-trace interactive simulator gates, customer reaction policy bank, seeded scenario profiles, agent_action_tags linkage, agent reactivity and previous-customer-intent gates, variable exchange counts, customer state before/after records, reaction_rule_ids, no-static-script boundary, hard-failure boundary, and no-provider/no-runtime-promotion boundary:

```powershell
python scripts\validate_prod_041a_conditional_scenario_diversity_expansion.py
```

Run the PROD-041 conditional simulation human review checkpoint:

```powershell
python scripts\run_prod_041_conditional_simulation_review.py
```

Validate the PROD-041 human review packet, locked PROD-041A source boundary, manual realism findings, rewrite candidates, blocked voice/demo promotion, and no-provider/no-runtime-promotion boundary:

```powershell
python scripts\validate_prod_041_conditional_simulation_review.py
```

Run the PROD-042 CallCenterEN turn-level sales pattern playbook checkpoint:

```powershell
python scripts\run_prod_042_callcenteren_turn_pattern_playbook.py
```

Validate the PROD-042 raw-zip parsing gates, turn-level pattern artifacts, coverage-gap reporting, leakage/commercial-safety boundary, no-scenario-generation boundary, and no-provider/no-runtime-promotion boundary:

```powershell
python scripts\validate_prod_042_callcenteren_turn_pattern_playbook.py
```

Run the PROD-043 sales playbook runtime adapter checkpoint:

```powershell
python scripts\run_prod_043_sales_playbook_runtime_adapter.py
```

Validate the PROD-043 offline customer-move classifier, playbook retrieval cases, deterministic single-turn agent response evaluator, safety boundaries, no-conversation-generation boundary, and no-runtime-modification boundary:

```powershell
python scripts\validate_prod_043_sales_playbook_runtime_adapter.py
```

Run the PROD-044 core sales-policy update review packet:

```powershell
python scripts\run_prod_044_core_sales_policy_update.py
```

Validate that PROD-044 lists only evidence-backed candidate policy updates, blocked updates, required campaign-fact guards, and unchanged runtime/retrieval/provider/private-data boundaries:

```powershell
python scripts\validate_prod_044_core_sales_policy_update.py
```

Run the PROD-045 core sales-policy regression rerun:

```powershell
python scripts\run_prod_045_core_sales_policy_regression_rerun.py
```

Validate that PROD-045 hardens required-action evaluation, rejects generic clarification for required-boundary moves, and applies only deterministic campaign-guarded runtime policy updates while keeping retrieval/provider/LLM/private-data boundaries blocked:

```powershell
python scripts\validate_prod_045_core_sales_policy_regression_rerun.py
```

Run the PROD-046A German naturalized policy regression checkpoint:

```powershell
python scripts\run_prod_046a_german_naturalized_policy_regression.py
```

Validate that PROD-046A covers naturalized de-DE intent-equivalent variants, German false-positive priority behavior, German localized policy responses, and the unchanged retrieval/provider/LLM/private-data boundaries:

```powershell
python scripts\validate_prod_046a_german_naturalized_policy_regression.py
```

Run the PROD-046B German response wording-quality pass:

```powershell
python scripts\run_prod_046b_german_response_wording_quality_pass.py
```

Validate that PROD-046B removes internal-policy wording from German customer-facing responses while keeping PROD-046A German and PROD-045 English regressions passing:

```powershell
python scripts\validate_prod_046b_german_response_wording_quality_pass.py
```

## Guarded Response And Voice Safety

Build and validate the core sales delivery playbook:

```powershell
python scripts\run_core_sales_delivery_playbook.py
python scripts\validate_core_sales_delivery_playbook.py
```

Generate a guarded response packet from the realtime decision path:

```powershell
python scripts\generate_guarded_response.py `
  --campaign campaign-prod-005-b2c-telecom `
  --stage product-detail-check `
  --transcript "Welcher genaue Tarif ist das und wie viel Datenvolumen ist enthalten?" `
  --out research/experiments/generated/RESP-001/RESP-001-guarded-response-result.json `
  --report-out research/experiments/generated/RESP-001/RESP-001-guarded-response-report.md
```

Opt in to local guarded retrieval for the same response path:

```powershell
python scripts\generate_guarded_response.py `
  --campaign campaign-prod-005-b2c-telecom `
  --stage relevance-check `
  --transcript "Das klingt zu teuer und ich weiss nicht, ob sich der Aufwand lohnt." `
  --retrieval-enabled `
  --retrieval-registry research\experiments\generated\RAG-017-runtime-knowledge-registry\result.json `
  --retrieval-max-results 4 `
  --retrieval-min-score 1 `
  --retrieval-target-latency-ms 150 `
  --retrieval-acceptable-latency-ms 300
```

Opt in to guarded retrieval plus runtime composer hooks for the same response path:

```powershell
python scripts\generate_guarded_response.py `
  --campaign campaign-prod-005-b2b-software `
  --stage relevance-check `
  --transcript "Customer raises too_expensive and needs a timeline_question before any close." `
  --retrieval-enabled `
  --retrieval-registry research\experiments\generated\RAG-017-runtime-knowledge-registry\result.json `
  --retrieval-max-results 4 `
  --retrieval-min-score 1 `
  --retrieval-target-latency-ms 150 `
  --retrieval-acceptable-latency-ms 300 `
  --composer-hooks-enabled
```

Run the controlled RESP-001 policy/core-playbook/live-RAG comparison:

```powershell
python scripts\run_resp_001_retrieval_ab_evaluation.py
```

Run the RAG-018 scripted-call simulation with scored objection resolution and next-step quality:

```powershell
python scripts\run_rag_018_scripted_call_simulation.py
```

Outputs:

```text
research\experiments\generated\RESP-001-retrieval-ab-evaluation\
research\experiments\generated\RAG-018-scripted-call-simulation\
```

Generate a runtime voice-delivery packet from the guarded response path:

```powershell
python scripts\generate_runtime_voice_delivery.py `
  --campaign campaign-prod-005-b2c-telecom `
  --stage relevance-check `
  --transcript "Das klingt zu teuer und ich weiss nicht, ob sich der Aufwand lohnt." `
  --out research\experiments\generated\RESP-002\RESP-002-runtime-voice-delivery-result.json `
  --report-out research\experiments\generated\RESP-002\RESP-002-runtime-voice-delivery-report.md
```

Validate RESP-002 guarded response voice delivery:

```powershell
python scripts\validate_resp_002_runtime_voice_delivery.py
```

Run and validate English/German RESP-002 voice parity:

```powershell
python scripts\run_resp_002_bilingual_voice_parity.py
python scripts\validate_resp_002_bilingual_voice_parity.py
```

Outputs:

```text
research\experiments\generated\RESP-002-bilingual-voice-parity\
```

Validate the 200-note call pattern learning checkpoint:

```powershell
python scripts\validate_call_pattern_learning_checkpoint.py
```

Generate a runtime TTS-delivery packet in dry-run mode:

```powershell
python scripts\generate_runtime_tts_delivery.py `
  --campaign campaign-prod-005-b2c-telecom `
  --stage relevance-check `
  --transcript "Das klingt zu teuer und ich weiss nicht, ob sich der Aufwand lohnt." `
  --out research/experiments/generated/RESP-003/RESP-003-runtime-live-tts-result.json `
  --report-out research/experiments/generated/RESP-003/RESP-003-runtime-live-tts-report.md
```

Validate RESP-003 runtime live-capable TTS delivery without provider calls:

```powershell
python scripts\validate_resp_003_runtime_live_tts.py
```

Run matched English/German RESP-003 plain-guarded vs shaped-runtime TTS A/B in dry-run mode:

```powershell
python scripts\run_resp_003_bilingual_live_tts_ab.py
```

Validate RESP-003 bilingual live-capable TTS A/B without provider calls:

```powershell
python scripts\validate_resp_003_bilingual_live_tts_ab.py
```

Run the separate RESP-004 VOICE-044 polished-baseline listening check in dry-run mode. RESP-003 remains the TTS bridge; RESP-004 owns this new test's evidence:

```powershell
python scripts\run_resp_004_voice_044_listening_check.py
```

Default RESP-004 output folder:

```text
research\experiments\generated\RESP-004-voice-044-listening-check\
```

Validate RESP-004 dry-run output, forced missing-key fallback, secret redaction, and no-provider/private-audio boundary:

```powershell
python scripts\validate_resp_004_voice_044_listening_check.py
```

Run one same-question old-runtime versus new-runtime listening check in dry-run mode:

```powershell
python scripts\run_resp_005_runtime_version_ab_listening_check.py
```

Validate RESP-005 same-question coverage, artifact shape, secret redaction, and no-provider/private-audio boundary:

```powershell
python scripts\validate_resp_005_runtime_version_ab_listening_check.py
```

Default RESP-005 output folder:

```text
research\experiments\generated\RESP-005-runtime-version-ab-listening-check\
```

Recorded RESP-005 human listening decision:

```text
research\experiments\generated\RESP-005-runtime-version-ab-listening-check\human-listening-decision.md
```

Run the German same-question old-runtime versus new-runtime listening check in dry-run mode:

```powershell
python scripts\run_resp_006_german_runtime_version_ab_listening_check.py
```

Validate RESP-006 German same-question coverage, artifact shape, secret redaction, and no-provider/private-audio boundary:

```powershell
python scripts\validate_resp_006_german_runtime_version_ab_listening_check.py
```

Default RESP-006 output folder:

```text
research\experiments\generated\RESP-006-german-runtime-version-ab-listening-check\
```

Recorded RESP-006 German listening decision:

```text
research\experiments\generated\RESP-006-german-runtime-version-ab-listening-check\human-listening-decision.md
```

Run the RESP-007 German pacing-stability follow-up in dry-run mode:

```powershell
python scripts\run_resp_007_german_pacing_stability_follow_up.py
```

Validate RESP-007 same-answer-content preservation, pacing-only delivery changes, secret redaction, and no-provider/private-audio boundary:

```powershell
python scripts\validate_resp_007_german_pacing_stability_follow_up.py
```

Default RESP-007 output folder:

```text
research\experiments\generated\RESP-007-german-pacing-stability-follow-up\
```

Evaluate provider readiness without API calls or audio upload:

```powershell
python scripts\evaluate_voice_provider_readiness.py `
  --candidates research\experiments\cases\voice-007-provider-readiness-candidates.json `
  --out research/experiments/generated/VOICE-007/VOICE-007-provider-readiness.json `
  --report-out research/experiments/generated/VOICE-007/VOICE-007-provider-readiness-report.md
```

Validate the provider readiness gate:

```powershell
python scripts\validate_voice_007_provider_readiness.py
```

Run the local TTS smoke test in forced fallback mode:

```powershell
python scripts\run_voice_008_local_tts_smoke.py --force-fallback
```

Validate local TTS smoke behavior:

```powershell
python scripts\validate_voice_008_local_tts_smoke.py
```

Run the Cartesia TTS smoke test in no-key fallback mode:

```powershell
python scripts\run_voice_010_cartesia_tts_smoke.py --force-key-missing
```

Validate Cartesia smoke behavior without live provider calls:

```powershell
python scripts\validate_voice_010_cartesia_tts_smoke.py
```

Run the VOICE-011 Cartesia WebSocket smoke test in no-key fallback mode:

```powershell
python scripts\run_voice_011_cartesia_websocket_smoke.py --live --force-key-missing
```

Validate VOICE-011 Cartesia WebSocket smoke behavior without live provider calls:

```powershell
python scripts\validate_voice_011_cartesia_websocket_smoke.py
```

Run the VOICE-012 speech naturalness renderer:

```powershell
python scripts\run_voice_012_speech_naturalness.py
```

Validate VOICE-012 segment-aware speech naturalness:

```powershell
python scripts\validate_voice_012_speech_naturalness.py
```

Run the VOICE-013 ElevenLabs TTS smoke test in no-key fallback mode:

```powershell
python scripts\run_voice_013_elevenlabs_tts_smoke.py --live --force-key-missing
```

Validate VOICE-013 ElevenLabs smoke behavior without live provider calls:

```powershell
python scripts\validate_voice_013_elevenlabs_tts_smoke.py
```

Build the VOICE-014 local provider listening comparison:

```powershell
python scripts\run_voice_014_provider_listening_comparison.py
```

Validate VOICE-014 provider listening comparison:

```powershell
python scripts\validate_voice_014_provider_listening_comparison.py
```

Run the VOICE-015 provider-neutral prosody naturalness planner:

```powershell
python scripts\run_voice_015_prosody_naturalness.py
```

Validate VOICE-015 bounded prosody cues and protected-segment locks:

```powershell
python scripts\validate_voice_015_prosody_naturalness.py
```

Render VOICE-016 provider-specific prosody previews without provider calls:

```powershell
python scripts\run_voice_016_provider_prosody_rendering.py
```

Validate VOICE-016 provider-specific prosody rendering:

```powershell
python scripts\validate_voice_016_provider_prosody_rendering.py
```

Run the VOICE-017 plain-vs-prosody A/B harness in dry-run mode:

```powershell
python scripts\run_voice_017_live_ab_audio.py
```

Validate VOICE-017 dry-run and forced-missing-key fallback behavior:

```powershell
python scripts\validate_voice_017_live_ab_audio.py
```

Run the VOICE-018 offline professional-sales voice tuning preview:

```powershell
python scripts\run_voice_018_sales_voice_tuning.py
```

Validate VOICE-018 sales voice pacing, emotion intents, and protected-text locks:

```powershell
python scripts\validate_voice_018_sales_voice_tuning.py
```

Run the VOICE-019 prosody-vs-sales-tuned live-capable A/B harness in dry-run mode:

```powershell
python scripts\run_voice_019_sales_tuned_live_ab_audio.py
```

Validate VOICE-019 dry-run and forced-missing-key fallback behavior:

```powershell
python scripts\validate_voice_019_sales_tuned_live_ab_audio.py
```

Build the VOICE-020 ElevenLabs-first voice design packet without provider calls:

```powershell
python scripts\run_voice_020_elevenlabs_voice_design.py
```

Validate VOICE-020 voice-design prompts, settings candidates, protected-text locks, and private-data boundary:

```powershell
python scripts\validate_voice_020_elevenlabs_voice_design.py
```

Run the VOICE-021 custom ElevenLabs voice comparison harness in dry-run mode:

```powershell
python scripts\run_voice_021_custom_voice_comparison.py
```

Validate VOICE-021 custom voice comparison safety and local voice-ID redaction:

```powershell
python scripts\validate_voice_021_custom_voice_comparison.py
```

Run a limited live VOICE-021 comparison after setting `ELEVENLABS_API_KEY` in the current shell:

```powershell
python scripts\run_voice_021_custom_voice_comparison.py --live --language en --limit-scripts 1 --timeout-seconds 8
python scripts\run_voice_021_custom_voice_comparison.py --live --language de --limit-scripts 1 --timeout-seconds 8
```

Run the VOICE-022 bilingual spoken-text normalization layer:

```powershell
python scripts\run_voice_022_spoken_text_normalization.py
```

Validate VOICE-022 English contractions, German spoken equivalents, runtime integration, and protected-text locks:

```powershell
python scripts\validate_voice_022_spoken_text_normalization.py
```

Run the VOICE-023 speech-realism layer:

```powershell
python scripts\run_voice_023_speech_realism.py
```

Validate VOICE-023 bounded thinking fillers, English/German language fit, runtime integration, and protected-text locks:

```powershell
python scripts\validate_voice_023_speech_realism.py
```

Run the VOICE-024 speech-realism A/B harness in dry-run mode:

```powershell
python scripts\run_voice_024_speech_realism_live_ab.py
```

Default VOICE-024 output folder:

```text
research\experiments\generated\VOICE-024-speech-realism-live-ab\
```

Validate VOICE-024 dry-run safety, forced-missing-key fallback, local voice-ID redaction, and protected-text locks:

```powershell
python scripts\validate_voice_024_speech_realism_live_ab.py
```

Run the VOICE-025 boundary-aware filler-placement checkpoint:

```powershell
python scripts\run_voice_025_filler_placement.py
```

Default VOICE-025 output folder:

```text
research\experiments\generated\VOICE-025-filler-placement\
```

Validate VOICE-025 English/German filler placement and protected German campaign text:

```powershell
python scripts\validate_voice_025_filler_placement.py
```

Run the VOICE-026 interaction-prosody checkpoint:

```powershell
python scripts\run_voice_026_interaction_prosody.py
```

Default VOICE-026 output folder:

```text
research\experiments\generated\VOICE-026-interaction-prosody\
```

Validate VOICE-026 bilingual lookup acknowledgements, neutral backchannels, sales pace cues, unsafe-agreement guards, and protected campaign text:

```powershell
python scripts\validate_voice_026_interaction_prosody.py
```

Run the VOICE-027 live-capable A/B harness comparing VOICE-025 baseline vs VOICE-026 interaction prosody:

```powershell
python scripts\run_voice_027_interaction_prosody_live_ab.py
```

Default VOICE-027 output folder:

```text
research\experiments\generated\VOICE-027-interaction-prosody-live-ab\
```

Validate VOICE-027 dry-run safety, forced-missing-key fallback, local voice-ID redaction, protected-text locks, and unsafe-agreement guards:

```powershell
python scripts\validate_voice_027_interaction_prosody_live_ab.py
```

Run the VOICE-028 controlled delivery imperfections checkpoint:

```powershell
python scripts\run_voice_028_controlled_imperfections.py
```

Default VOICE-028 output folder:

```text
research\experiments\generated\VOICE-028-controlled-imperfections\
```

Validate VOICE-028 English/German controlled imperfections, protected-text locks, unsafe-claim suppression, and no-provider boundary:

```powershell
python scripts\validate_voice_028_controlled_imperfections.py
```

Run the VOICE-029 local speech-profile checkpoint on synthetic fixtures:

```powershell
python scripts\run_voice_029_local_speech_profile.py
```

Default VOICE-029 output folder:

```text
research\experiments\generated\VOICE-029-local-speech-profile-learning\
```

Validate VOICE-029 local speech profile extraction, private-read guard, workspace initializer, and no-provider/no-cloning boundary:

```powershell
python scripts\validate_voice_029_local_speech_profile.py
```

Preview the ignored private personal speech-learning workspace:

```powershell
python scripts\init_personal_speech_learning_workspace.py --dry-run
```

Create the ignored private personal speech-learning workspace when redacted local transcripts are ready:

```powershell
python scripts\init_personal_speech_learning_workspace.py
```

Run VOICE-029 on reviewed local redacted transcripts only. Outputs remain inside `data\private\`:

```powershell
python scripts\run_voice_029_local_speech_profile.py `
  --input-dir data\private\tarik-speech-samples\transcripts-redacted `
  --allow-private-read
```

Start the VOICE-030B localhost recorder for Tarik speech samples. Browser uploads are encoded to WAV locally and saved under `data\private\tarik-speech-samples\raw-audio\`:

```powershell
python scripts\run_voice_030b_local_speech_capture.py --serve
```

Import an existing local audio file into the same private raw-audio folder:

```powershell
python scripts\run_voice_030b_local_speech_capture.py `
  --import-file "<local-speech-sample.wav>" `
  --language en `
  --label "tarik local speech sample"
```

Validate VOICE-030B local capture/import, localhost-only serving, and no-provider/no-transcription/no-cloning boundary:

```powershell
python scripts\validate_voice_030b_local_speech_capture.py
```

Validate VOICE-030C private learning queue, automatic WAV analysis hook, non-WAV conversion status, Turkish-native speaker context, and no-runtime/no-provider boundary:

```powershell
python scripts\validate_voice_030c_private_learning_queue.py
```

Run VOICE-030D private feature review on local Tarik speech-sample features only. Outputs remain inside `data\private\`:

```powershell
python scripts\run_voice_030d_private_feature_review.py --allow-private-read
```

Validate VOICE-030D private review summaries, diagnostic-only pause metrics, no-runtime/no-provider boundary, and private-read guard:

```powershell
python scripts\validate_voice_030d_private_feature_review.py
```

Run VOICE-031 reviewed feature-to-runtime mapping gate on a synthetic public fixture:

```powershell
python scripts\run_voice_031_feature_runtime_mapping.py
```

Default VOICE-031 output folder:

```text
research\experiments\generated\VOICE-031-feature-runtime-mapping\
```

Run VOICE-031 on a reviewed private VOICE-030D summary only. Outputs remain inside `data\private\`:

```powershell
python scripts\run_voice_031_feature_runtime_mapping.py `
  --summary-json data\private\tarik-speech-samples\derived\review\voice-030d-feature-review-summary.json `
  --allow-private-review-read
```

Validate VOICE-031 proposal-only mapping, blocked pause metrics, private-read guard, private-output guard, and WhatsApp reminder:

```powershell
python scripts\validate_voice_031_feature_runtime_mapping.py
```

Put exported WhatsApp `.ogg` voice notes here:

```text
data\private\tarik-speech-samples\whatsapp-voice-notes\
```

Convert local WhatsApp `.ogg` voice notes to WAV under `data\private\` and queue successful WAVs into VOICE-030C:

```powershell
python scripts\run_voice_032_local_audio_conversion.py
```

If `ffmpeg` is missing, VOICE-032 records `converter_missing_needs_local_ffmpeg` instead of failing silently.

Validate VOICE-032 OGG-first local conversion, missing-ffmpeg status, private boundary, and VOICE-030C queue integration:

```powershell
python scripts\validate_voice_032_local_audio_conversion.py
```

Check whether private Tarik speech samples are ready for a VOICE-030D review without reading raw audio content:

```powershell
python scripts\run_voice_033_private_sample_readiness.py --allow-private-metadata-read
```

Private VOICE-033 output folder:

```text
data\private\tarik-speech-samples\derived\readiness\
```

Validate VOICE-033 private metadata-only readiness statuses, thresholds, recommendations, and no-audio-content boundary:

```powershell
python scripts\validate_voice_033_private_sample_readiness.py
```

Run the VOICE-034 pacing calibration V2 checkpoint:

```powershell
python scripts\run_voice_034_pacing_calibration.py
```

Default VOICE-034 output folder:

```text
research\experiments\generated\VOICE-034-pacing-calibration-v2\
```

Validate VOICE-034 English/German pacing calibration, German word-gap reduction, protected-text locks, and no-provider boundary:

```powershell
python scripts\validate_voice_034_pacing_calibration.py
```

Run the VOICE-035 connected-speech phrase-flow checkpoint:

```powershell
python scripts\run_voice_035_connected_speech.py
```

Default VOICE-035 output folder:

```text
research\experiments\generated\VOICE-035-connected-speech\
```

Validate VOICE-035 English/German phrase-flow joins, VOICE-034 speed-bound preservation, protected-text locks, and no-provider boundary:

```powershell
python scripts\validate_voice_035_connected_speech.py
```

Run the VOICE-036 listening-feedback calibration checkpoint:

```powershell
python scripts\run_voice_036_listening_calibration.py
```

Default VOICE-036 output folder:

```text
research\experiments\generated\VOICE-036-listening-calibration\
```

Validate VOICE-036 German connected-speech relaxation, emphasis-target guard, protected-text locks, and no-provider boundary:

```powershell
python scripts\validate_voice_036_listening_calibration.py
```

Run the VOICE-037 emotion-transition smoothing checkpoint:

```powershell
python scripts\run_voice_037_emotion_smoothing.py
```

Default VOICE-037 output folder:

```text
research\experiments\generated\VOICE-037-emotion-smoothing\
```

Validate VOICE-037 emotional inertia, provider stability/style bounds, protected-text locks, and no-provider boundary:

```powershell
python scripts\validate_voice_037_emotion_smoothing.py
```

Run the VOICE-038 semantic emphasis/rhythm diagnosis for the preferred English voice:

```powershell
python scripts\run_voice_038_semantic_emphasis_diagnosis.py
```

Default VOICE-038 output folder:

```text
research\experiments\generated\VOICE-038-semantic-emphasis-diagnosis\
```

Validate VOICE-038 dry-run safety, forced-missing-key fallback, semantic variants, and no-provider/private-data boundary:

```powershell
python scripts\validate_voice_038_semantic_emphasis_diagnosis.py
```

Run the VOICE-039 runtime semantic-emphasis checkpoint through RESP-002/RESP-003 in dry-run mode:

```powershell
python scripts\run_voice_039_runtime_semantic_emphasis.py
```

Default VOICE-039 output folder:

```text
research\experiments\generated\VOICE-039-runtime-semantic-emphasis\
```

Validate VOICE-039 runtime promotion, protected-text locks, German language lock, and no-provider/private-data boundary:

```powershell
python scripts\validate_voice_039_runtime_semantic_emphasis.py
```

Run the VOICE-040 low-pressure focus checkpoint through RESP-002/RESP-003 in dry-run mode:

```powershell
python scripts\run_voice_040_low_pressure_focus.py
```

Default VOICE-040 output folder:

```text
research\experiments\generated\VOICE-040-low-pressure-focus\
```

Validate VOICE-040 low-pressure phrase correction, protected-text locks, German language lock, and no-provider/private-data boundary:

```powershell
python scripts\validate_voice_040_low_pressure_focus.py
```

Run the VOICE-041 private pattern profile checkpoint through RESP-002 in dry-run mode:

```powershell
python scripts\run_voice_041_private_pattern_profile.py
```

Default VOICE-041 output folder:

```text
research\experiments\generated\VOICE-041-private-pattern-profile\
```

Validate VOICE-041 private pattern profile application, protected-text locks, no-runtime private audio read, no-provider, and no-cloning boundary:

```powershell
python scripts\validate_voice_041_private_pattern_profile.py
```

Run the VOICE-042 private-pattern live-capable A/B checkpoint in dry-run mode:

```powershell
python scripts\run_voice_042_private_pattern_live_ab.py
```

Default VOICE-042 output folder:

```text
research\experiments\generated\VOICE-042-private-pattern-live-ab\
```

Validate VOICE-042 same-text A/B isolation, live limit guard, missing-key fallback, redacted provider preview, no-runtime private audio read, no-provider in dry-run, and no-cloning boundary:

```powershell
python scripts\validate_voice_042_private_pattern_live_ab.py
```

Run the VOICE-043 baseline shaped runtime acceptance checkpoint in dry-run mode:

```powershell
python scripts\run_voice_043_baseline_shaped_runtime_acceptance.py
```

Default VOICE-043 output folder:

```text
research\experiments\generated\VOICE-043-baseline-shaped-runtime-acceptance\
```

Validate that baseline shaped runtime remains preferred, VOICE-041 is not promoted, private-pattern settings are off by default, protected text stays exact, and no provider/private-audio boundary is crossed:

```powershell
python scripts\validate_voice_043_baseline_shaped_runtime_acceptance.py
```

Run the VOICE-044 baseline delivery polish checkpoint in dry-run mode:

```powershell
python scripts\run_voice_044_baseline_delivery_polish.py
```

Default VOICE-044 output folder:

```text
research\experiments\generated\VOICE-044-baseline-delivery-polish\
```

Validate narrow English/German baseline polish, VOICE-041 staying off by default, protected-text locks, and no-provider/private-audio boundary:

```powershell
python scripts\validate_voice_044_baseline_delivery_polish.py
```

Run the VOICE-030A raw WAV audio reader on synthetic fixtures:

```powershell
python scripts\run_voice_030_raw_audio_reader.py
```

Default VOICE-030A output folder:

```text
research\experiments\generated\VOICE-030A-raw-audio-local-reader\
```

Validate VOICE-030A local WAV feature extraction, private-read guard, and no-transcription/no-provider/no-cloning boundary:

```powershell
python scripts\validate_voice_030_raw_audio_reader.py
```

Run VOICE-030A on private WAV recordings only. Outputs remain inside `data\private\`:

```powershell
python scripts\run_voice_030_raw_audio_reader.py `
  --input-dir data\private\tarik-speech-samples\raw-audio `
  --allow-private-read
```

Run a limited live VOICE-027 comparison after setting `ELEVENLABS_API_KEY` in the current shell and confirming local ignored voice IDs exist:

```powershell
python scripts\run_voice_027_interaction_prosody_live_ab.py --live --language en --limit-scripts 1 --timeout-seconds 8
python scripts\run_voice_027_interaction_prosody_live_ab.py --live --language de --limit-scripts 1 --timeout-seconds 8
```

## Guarded Local Demo Server

Use the guarded launcher for browser demos so long-lived servers do not hang the terminal:

```powershell
python scripts\start_guarded_local_server.py `
  --name VOICE-004 `
  --host 127.0.0.1 `
  --port 8765 `
  --startup-timeout 8 `
  --pid-out research\experiments\generated\VOICE-004-server.pid `
  --stdout-log research\experiments\generated\VOICE-004-server.stdout.log `
  --stderr-log research\experiments\generated\VOICE-004-server.stderr.log `
  -- python scripts\run_browser_speech_demo.py
```

## Explicit Opt-In Provider Commands

These commands can contact external providers. Do not run them as default setup checks.

Live VOICE-024 audio generation requires `ELEVENLABS_API_KEY` in the current shell and local voice IDs in ignored config:

```powershell
python scripts\run_voice_024_speech_realism_live_ab.py --live --timeout-seconds 8
```

Live LLM product-agent evaluation requires an environment-only API key:

```powershell
python scripts\run_llm_product_agent.py `
  --cases research\experiments\cases\prod-004-sales-difficulty-gauntlet.json `
  --out research/experiments/generated/PROD-004/PROD-004-llm-agent-results.json `
  --report-out research/experiments/generated/PROD-004/PROD-004-llm-agent-report.md `
  --limit 1
```

Live Cartesia TTS smoke testing requires `CARTESIA_API_KEY`, `CARTESIA_VOICE_ID`, and an explicit `--live` flag:

```powershell
python scripts\run_voice_010_cartesia_tts_smoke.py --live
```

Live VOICE-011 Cartesia WebSocket smoke testing requires `CARTESIA_API_KEY`, an explicit `--live` flag, and either language-specific voice IDs or the default voice ID:

```powershell
python scripts\run_voice_011_cartesia_websocket_smoke.py --live
```

Live VOICE-013 ElevenLabs TTS smoke testing requires `ELEVENLABS_API_KEY`, an explicit `--live` flag, and either language-specific voice IDs or the default voice ID:

```powershell
python scripts\run_voice_013_elevenlabs_tts_smoke.py --live
```

Live VOICE-017 ElevenLabs plain-vs-prosody A/B testing requires `ELEVENLABS_API_KEY`, an explicit `--live` flag, and either language-specific voice IDs or the default voice ID:

```powershell
python scripts\run_voice_017_live_ab_audio.py --provider elevenlabs --live --timeout-seconds 8
```

Live VOICE-017 Cartesia plain-vs-prosody A/B testing requires `CARTESIA_API_KEY`, an explicit `--live` flag, and either language-specific voice IDs or the default voice ID:

```powershell
python scripts\run_voice_017_live_ab_audio.py --provider cartesia --live --timeout-seconds 8
```

Live VOICE-017 with both providers in one run is intentionally blocked unless `--allow-both-live` is also set.

Live VOICE-038 semantic emphasis/rhythm diagnosis requires `ELEVENLABS_API_KEY`, an explicit `--live` flag, and an English voice ID in `ELEVENLABS_VOICE_ID_EN` or ignored local config:

```powershell
python scripts\run_voice_038_semantic_emphasis_diagnosis.py --live --timeout-seconds 8
```

Live VOICE-039 full-runtime semantic-emphasis listening check requires `ELEVENLABS_API_KEY`, an explicit `--live` flag, `--limit-cases`, and an English voice ID in `ELEVENLABS_VOICE_ID_EN` or ignored local config:

```powershell
python scripts\run_voice_039_runtime_semantic_emphasis.py --live --provider elevenlabs --limit-cases 1 --timeout-seconds 8
```

Live VOICE-040 low-pressure focus listening check requires `ELEVENLABS_API_KEY`, an explicit `--live` flag, `--limit-cases`, and an English voice ID in `ELEVENLABS_VOICE_ID_EN` or ignored local config:

```powershell
python scripts\run_voice_040_low_pressure_focus.py --live --provider elevenlabs --limit-cases 1 --timeout-seconds 8
```

Live VOICE-042 private-pattern A/B listening check requires `ELEVENLABS_API_KEY`, an explicit `--live` flag, `--limit-cases`, and an English voice ID in `ELEVENLABS_VOICE_ID_EN` or ignored local config:

```powershell
python scripts\run_voice_042_private_pattern_live_ab.py --provider elevenlabs --live --limit-cases 1 --timeout-seconds 8
```

Live VOICE-019 ElevenLabs prosody-vs-sales-tuned A/B testing requires `ELEVENLABS_API_KEY`, an explicit `--live` flag, and either language-specific voice IDs or the default voice ID:

```powershell
python scripts\run_voice_019_sales_tuned_live_ab_audio.py --provider elevenlabs --live --timeout-seconds 8 --limit 2
```

Live VOICE-019 Cartesia prosody-vs-sales-tuned A/B testing requires `CARTESIA_API_KEY`, an explicit `--live` flag, and either language-specific voice IDs or the default voice ID:

```powershell
python scripts\run_voice_019_sales_tuned_live_ab_audio.py --provider cartesia --live --timeout-seconds 8 --limit 2
```

Live RESP-003 runtime TTS with ElevenLabs requires the local provider boundary review, `ELEVENLABS_API_KEY`, an explicit `--live` flag, and either language-specific voice IDs or the default voice ID:

```powershell
python scripts\generate_runtime_tts_delivery.py `
  --campaign campaign-prod-005-b2c-telecom `
  --stage relevance-check `
  --transcript "Das klingt zu teuer und ich weiss nicht, ob sich der Aufwand lohnt." `
  --provider elevenlabs `
  --live `
  --timeout-seconds 8
```

Live RESP-003 runtime TTS with Cartesia requires the local provider boundary review, `CARTESIA_API_KEY`, an explicit `--live` flag, and either language-specific voice IDs or the default voice ID:

```powershell
python scripts\generate_runtime_tts_delivery.py `
  --campaign campaign-prod-005-b2c-telecom `
  --stage relevance-check `
  --transcript "Das klingt zu teuer und ich weiss nicht, ob sich der Aufwand lohnt." `
  --provider cartesia `
  --live `
  --timeout-seconds 8
```

Live RESP-004 VOICE-044 listening check requires the local provider boundary review, an explicit `--live` flag, and provider-specific key/voice ID environment variables. Use this instead of overwriting RESP-003 evidence for the VOICE-044 follow-up test:

```powershell
python scripts\run_resp_004_voice_044_listening_check.py --provider elevenlabs --live --timeout-seconds 8
```

Live RESP-007 German pacing-stability listening check requires the local provider boundary review, an explicit `--live` flag, and provider-specific key/German voice ID environment variables:

```powershell
python scripts\run_resp_007_german_pacing_stability_follow_up.py --provider elevenlabs --live --timeout-seconds 8
```

## Safety Rules

- Do not commit API keys, private transcripts, raw private audio, customer exports, or client-specific sensitive details.
- Default validation should not require `OPENAI_API_KEY`, `CARTESIA_API_KEY`, or `CARTESIA_VOICE_ID`.
- Local voice IDs may be stored in ignored `config\local\voice_ids.json`; API keys remain environment-only.
- Raw private call-center audio and raw transcripts must stay under ignored `data\private\` and must not be uploaded to providers by default.
- Only redacted, minimized, human-reviewed sales-pattern notes may leave `data\private\`.
- Use `--live` only when provider, consent, retention, and logging assumptions have been reviewed.
- Keep generated artifacts under `research\experiments\generated` unless a script documents another output path.
- Keep required checklists, templates, workflows, and scripts inside this repository. Do not make Emotion Aware depend on `D:\Codex\shared` or another active project folder.
