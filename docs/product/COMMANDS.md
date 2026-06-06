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

Validate the runtime boundary map that separates runtime-affecting files from research, generated evidence, validators, temporary files, and private data:

```powershell
python scripts\validate_runtime_manifest.py
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

Validate live-demo voice-ID diagnostics without provider calls or raw voice-ID logging:

```powershell
python scripts\validate_live_demo_voice_id_diagnostics.py
```

Optional local ElevenLabs voice IDs can be stored in ignored config:

```powershell
Copy-Item runtime\config\local\voice_ids.example.json runtime\config\local\voice_ids.json
```

Then edit `config\local\voice_ids.json` locally. Do not put API keys in this file. Live-demo turn packets expose only redacted voice diagnostics: source, ID length, and a short hash.

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

Run the PROD-046C German campaign-field interpolation guard:

```powershell
python scripts\run_prod_046c_german_campaign_field_interpolation_guard.py
```

Validate that PROD-046C blocks malformed German interpolation such as `bei beim` and `um ein kurzer`, while keeping PROD-045, PROD-046A, and PROD-046B regressions passing:

```powershell
python scripts\validate_prod_046c_german_campaign_field_interpolation_guard.py
```

Run the PROD-046D German source-informed wording-quality guard:

```powershell
python scripts\run_prod_046d_german_source_informed_wording_quality_guard.py
```

Validate that PROD-046D removes remaining internal-sounding German customer-facing wording while keeping PROD-045, PROD-046A, PROD-046B, and PROD-046C regressions passing:

```powershell
python scripts\validate_prod_046d_german_source_informed_wording_quality_guard.py
```

Run the PROD-046 core sales-policy human/product review checkpoint:

```powershell
python scripts\run_prod_046_core_sales_policy_human_review.py
```

Validate that PROD-046 accepts the deterministic policy surface for offline regression evidence, keeps it blocked from voice/demo/customer use, records German human-review risk, and recommends the next campaign-profile validator:

```powershell
python scripts\validate_prod_046_core_sales_policy_human_review.py
```

Run the PROD-047 campaign-profile contract validator checkpoint:

```powershell
python scripts\run_prod_047_campaign_profile_contract_validator.py
```

Validate that PROD-047 blocks malformed, internal-sounding, unsafe, or under-reviewed campaign/profile fields before voice, demo, customer use, or runtime promotion:

```powershell
python scripts\validate_prod_047_campaign_profile_contract_validator.py
```

Run the PROD-048A native German review HTML packet checkpoint:

```powershell
python scripts\run_prod_048a_native_german_review_html_packet.py
```

Validate that PROD-048A creates a self-contained German-only reviewer packet with JSON/CSV export while claiming no native German approval, no legal compliance, and no runtime/demo/voice promotion:

```powershell
python scripts\validate_prod_048a_native_german_review_html_packet.py
```

Run the PROD-048A grouped German review HTML and brevity packet checkpoint:

```powershell
python scripts\run_prod_048a_german_review_html_and_brevity_packet.py
```

Validate that the grouped PROD-048A packet keeps every German case internally, groups repeated answers, shortens review-facing German answers where safe, supports JSON/CSV export, and keeps approval/legal/runtime/demo/voice/promotion claims blocked:

```powershell
python scripts\validate_prod_048a_german_review_html_and_brevity_packet.py
```

Run the PROD-048B native German review import checkpoint:

```powershell
python scripts\run_prod_048b_native_german_review_import.py
```

Validate that PROD-048B imports the returned reviewer JSON as partial evidence, recomputes reviewed versus blank rows, records the price wording revision candidate, and keeps approval/legal/runtime/demo/voice/promotion claims blocked:

```powershell
python scripts\validate_prod_048b_native_german_review_import.py
```

Run the PROD-048C German wording feedback patch checkpoint:

```powershell
python scripts\run_prod_048c_german_wording_feedback_patch.py
```

Validate that PROD-048C applies only the reviewed German price-first wording correction, preserves payment/scam/sale-ready boundaries, creates the corrected grouped follow-up review HTML, and keeps approval/legal/runtime-policy/call-control/demo/voice/promotion claims blocked:

```powershell
python scripts\validate_prod_048c_german_wording_feedback_patch.py
```

Run the PROD-049 safe end-call bridge-continue review checkpoint:

```powershell
python scripts\run_prod_049_safe_end_call_bridge_continue_review.py
```

Validate that PROD-049 selects only non-refusal bridge-then-continue candidates, keeps support/cancellation/do-not-call/email-only/payment/scam/sale-ready/callback boundaries protected, and applies no runtime or provider change:

```powershell
python scripts\validate_prod_049_safe_end_call_bridge_continue_review.py
```

Run the PROD-050 safe call-control softening regression checkpoint:

```powershell
python scripts\run_prod_050_safe_call_control_softening_regression.py
```

Validate that PROD-050 proposed-softens all selected non-refusal candidates to bridge-then-continue with low-pressure continuation text, preserves protected boundaries, records no pressure/payment/contract/unsupported-claim violations, and applies no live runtime change:

```powershell
python scripts\validate_prod_050_safe_call_control_softening_regression.py
```

Run the PROD-051 live runtime update with deterministic naturalness audit:

```powershell
python scripts\run_prod_051_safe_call_control_runtime_update.py
```

Validate that PROD-051 applies only the selected answer-and-continue runtime path, preserves protected boundaries, and passes the deeper spoken-response naturalness rubric:

```powershell
python scripts\validate_prod_051_safe_call_control_runtime_update.py
```

Run the PROD-052 language-lane review separation checkpoint:

```powershell
python scripts\run_prod_052_language_lane_review_separation.py
```

Validate that PROD-052 separates English exact spoken-response review from German pending native/source-backed review, keeps multilingual rules policy-only, inventories older mixed review surfaces, and applies no runtime change:

```powershell
python scripts\validate_prod_052_language_lane_review_separation.py
```

Run the PROD-053A English sales psychology deep-dive research checkpoint:

```powershell
python scripts\run_prod_053a_english_sales_psychology_deep_dive.py
```

Validate that PROD-053A preserves source boundaries, stores no source excerpts or copied scripts, creates compact English rule candidates, rejects manipulative tactics, and applies no runtime change:

```powershell
python scripts\validate_prod_053a_english_sales_psychology_deep_dive.py
```

Run the PROD-053B compact English psychology layer review:

```powershell
python scripts\run_prod_053b_compact_english_psychology_layer_review.py
```

Validate that PROD-053B accepts only English deterministic response-shape rules for PROD-053C, flags current English rewrite candidates, keeps rejected tactics blocked, and applies no runtime change:

```powershell
python scripts\validate_prod_053b_compact_english_psychology_layer_review.py
```

Run the PROD-053C English spoken-response expansion review packet:

```powershell
python scripts\run_prod_053c_english_spoken_response_expansion_review.py
```

Validate that PROD-053C creates the English-only review surface, excludes already-approved carry-forward items, keeps German exact-phrase review blocked, and applies no runtime change:

```powershell
python scripts\validate_prod_053c_english_spoken_response_expansion_review.py
```

Run the PROD-053D English review import:

```powershell
python scripts\run_prod_053d_english_review_import.py
```

Validate that PROD-053D imports the owner review export, separates approved-as-written items from rework notes, identifies runtime patch candidates, and applies no runtime change:

```powershell
python scripts\validate_prod_053d_english_review_import.py
```

Run the PROD-053E English runtime wording patch:

```powershell
python scripts\run_prod_053e_english_runtime_wording_patch.py
```

Validate that PROD-053E promotes only accepted and safe English wording into the deterministic realtime runtime, while leaving voicemail action-only behavior, coverage knowledge-policy behavior, and context-sensitive autonomy wording unpromoted:

```powershell
python scripts\validate_prod_053e_english_runtime_wording_patch.py
```

Run the PROD-054 English multi-turn naturalness stress review:

```powershell
python scripts\run_prod_054_english_multi_turn_naturalness_stress_review.py
```

Validate that PROD-054 turns the PROD-053E promoted English responses into a deterministic second-turn stress report, keeps runtime promotion blocked, and preserves no-provider/no-LLM/no-private-data boundaries:

```powershell
python scripts\validate_prod_054_english_multi_turn_naturalness_stress_review.py
```

Run the PROD-055 English multi-turn runtime patch:

```powershell
python scripts\run_prod_055_english_multi_turn_runtime_patch.py
```

Validate that PROD-055 patches the six PROD-054 blocking findings while keeping provider, LLM, private-data, German exact-phrase, payment, contract, and production-promotion boundaries blocked:

```powershell
python scripts\validate_prod_055_english_multi_turn_runtime_patch.py
```

Run the PROD-056 English post-patch multi-turn regression:

```powershell
python scripts\run_prod_056_english_post_patch_multi_turn_regression.py
```

Validate that PROD-056 reruns all 26 promoted English surfaces after the PROD-055 patch, keeps the callback request coherent through scheduling, and preserves no-provider/no-LLM/no-private-data/no-production-promotion boundaries:

```powershell
python scripts\validate_prod_056_english_post_patch_multi_turn_regression.py
```

Run the stable English multi-turn regression guard:

```powershell
python scripts\validate_english_multi_turn_regression_guard.py
```

Run the PROD-057 English multi-turn regression guard decision:

```powershell
python scripts\run_prod_057_english_multi_turn_regression_guard_decision.py
```

Validate that PROD-057 adopts PROD-056 as the stable English multi-turn regression guard, registers the guard in setup checks, and keeps runtime, provider, private-data, German, voice, payment, contract, and production-promotion boundaries blocked:

```powershell
python scripts\validate_prod_057_english_multi_turn_regression_guard_decision.py
```

Run the PROD-058 English runtime promotion blocker inventory:

```powershell
python scripts\run_prod_058_english_runtime_promotion_blocker_inventory.py
```

Validate that PROD-058 inventories remaining English runtime promotion blockers, separates English evidence gaps from product-policy gates and separate German/voice/retrieval/provider/private-data/legal/deployment gates, and keeps runtime, response text, provider, LLM, private-data, German, voice, payment, contract, real-customer, and production-promotion boundaries blocked:

```powershell
python scripts\validate_prod_058_english_runtime_promotion_blocker_inventory.py
```

Run the PROD-059 final English-only runtime readiness review:

```powershell
python scripts\run_prod_059_final_english_only_runtime_readiness_review.py
```

Validate that PROD-059 records human acceptance of the PROD-058 inventory, marks the bounded English deterministic runtime surface `ready_with_exclusions`, explicitly excludes still-blocked policy/separate-track/deployment gates, and keeps runtime, response text, provider, LLM, private-data, German, voice, retrieval, legal, payment, contract, real-customer, public-demo, and production-promotion boundaries blocked:

```powershell
python scripts\validate_prod_059_final_english_only_runtime_readiness_review.py
```

Run the PROD-060 runtime promotion path decision:

```powershell
python scripts\run_prod_060_runtime_promotion_path_decision.py
```

Validate that PROD-060 records human acceptance of the PROD-059 review, selects `internal_guarded_english_baseline_only` only as a local offline synthetic internal regression reference, rejects public-demo, real-customer, provider/private-data, retrieval, voice, German, payment/contract, and production runtime paths, and keeps runtime, response text, provider, LLM, private-data, German, voice, retrieval, legal, payment, contract, real-customer, public-demo, and production-promotion boundaries blocked:

```powershell
python scripts\validate_prod_060_runtime_promotion_path_decision.py
```

Run the PROD-061 English product-policy gate prioritization:

```powershell
python scripts\run_prod_061_english_product_policy_gate_prioritization.py
```

Validate that PROD-061 records human acceptance of the PROD-060 path decision, prioritizes `context_sensitive_autonomy_behavior` as the first English product-policy probe while keeping it still blocked, defers voicemail action-only behavior, coverage knowledge-policy behavior, and broad customer-move classification, and keeps runtime, response text, classifier, provider, LLM, private-data, German, voice, retrieval, legal, payment, contract, real-customer, public-demo, and production-promotion boundaries blocked:

```powershell
python scripts\validate_prod_061_english_product_policy_gate_prioritization.py
```

Run the PROD-062 English context-sensitive autonomy policy probe:

```powershell
python scripts\run_prod_062_english_context_sensitive_autonomy_policy_probe.py
```

Validate that PROD-062 probes the shorter English autonomy wording candidate synthetically only, recommends a separate narrow runtime patch, creates no review HTML, and keeps runtime, response text, classifier, provider, LLM, private-data, German, voice, retrieval, legal, payment, contract, real-customer, public-demo, and production-promotion boundaries blocked:

```powershell
python scripts\validate_prod_062_english_context_sensitive_autonomy_policy_probe.py
```

Run the PROD-063 English autonomy-check runtime wording patch:

```powershell
python scripts\run_prod_063_english_autonomy_check_runtime_wording_patch.py
```

Validate that PROD-063 applies only the approved English `autonomy-check` response text patch, keeps classifier reachability and call-control behavior unchanged, changes no German text, creates no review HTML, and keeps provider, LLM, private-data, German, voice, retrieval, legal, payment, contract, real-customer, public-demo, and production-promotion boundaries blocked:

```powershell
python scripts\validate_prod_063_english_autonomy_check_runtime_wording_patch.py
```

Run the PROD-064 English autonomy post-patch multi-turn regression:

```powershell
python scripts\run_prod_064_english_autonomy_post_patch_multi_turn_regression.py
```

Validate that PROD-064 reruns the stable English guard, verifies the patched autonomy first-turn response, checks autonomy follow-up and protected-boundary routing, creates no review HTML, and keeps runtime, response text, classifier, provider, LLM, private-data, German, voice, retrieval, legal, payment, contract, real-customer, public-demo, and production-promotion boundaries blocked:

```powershell
python scripts\validate_prod_064_english_autonomy_post_patch_multi_turn_regression.py
```

Run the PROD-065 English remaining product-policy gate selection:

```powershell
python scripts\run_prod_065_english_remaining_product_policy_gate_selection.py
```

Validate that PROD-065 selects `voicemail_action_only_behavior` as the next remaining English product-policy gate, keeps coverage and broad customer-move classification deferred, creates no review HTML, and keeps runtime, response text, classifier, provider, LLM, private-data, German, voice, retrieval, legal, payment, contract, real-customer, public-demo, and production-promotion boundaries blocked:

```powershell
python scripts\validate_prod_065_english_remaining_product_policy_gate_selection.py
```

Run the PROD-066 English voicemail action-only policy probe:

```powershell
python scripts\run_prod_066_english_voicemail_action_only_policy_probe.py
```

Validate that PROD-066 imports existing owner voicemail feedback, probes action-only/no-spoken-response voicemail behavior, records the current runtime spoken-response gap, creates no review HTML, and keeps runtime, response text, classifier, provider, LLM, private-data, German, voice, retrieval, legal, payment, contract, real-customer, public-demo, and production-promotion boundaries blocked:

```powershell
python scripts\validate_prod_066_english_voicemail_action_only_policy_probe.py
```

Run the PROD-067 English voicemail action-only runtime patch:

```powershell
python scripts\run_prod_067_english_voicemail_action_only_runtime_patch.py
```

Validate that PROD-067 suppresses the English voicemail spoken response, keeps follow-up logging and end-call behavior, does not change classifier reachability, next action, call-control behavior, German text, provider, LLM, private-data, voice, retrieval, legal, payment, contract, real-customer, public-demo, or production-promotion boundaries, and creates no review HTML:

```powershell
python scripts\validate_prod_067_english_voicemail_action_only_runtime_patch.py
```

Run the PROD-068 English voicemail post-patch regression:

```powershell
python scripts\run_prod_068_english_voicemail_post_patch_regression.py
```

Validate that PROD-068 keeps English voicemail action-only behavior stable, verifies nearby human-speech and protected-boundary cases, reruns the stable English guard, creates no review HTML, changes no runtime behavior, response text, classifier reachability, next action, call-control behavior, provider, LLM, private-data, German, voice, retrieval, legal, payment, contract, real-customer, public-demo, or production-promotion boundaries:

```powershell
python scripts\validate_prod_068_english_voicemail_post_patch_regression.py
```

Run the PROD-069 English remaining product-policy gate selection after voicemail:

```powershell
python scripts\run_prod_069_english_remaining_product_policy_gate_selection_after_voicemail.py
```

Validate that PROD-069 selects `coverage_knowledge_policy_behavior` as the next still-blocked English policy probe, keeps broad customer-move classifier expansion deferred, creates no review HTML, and changes no runtime behavior, response text, classifier reachability, retrieval default, provider, LLM, private-data, German, voice, legal, payment, contract, real-customer, public-demo, or production-promotion boundaries:

```powershell
python scripts\validate_prod_069_english_remaining_product_policy_gate_selection_after_voicemail.py
```

Run the PROD-070 English coverage knowledge-policy probe:

```powershell
python scripts\run_prod_070_english_coverage_knowledge_policy_probe.py
```

Validate that PROD-070 probes the selected English coverage knowledge-policy boundary, records that coverage advice, coverage fact claims, eligibility claims, and reimbursement claims remain blocked, detects the current runtime gaps for `eligible`, `reimbursement`, and `plan covers` phrases, creates no review HTML, and changes no runtime behavior, response text, classifier reachability, retrieval default, provider, LLM, private-data, German, voice, legal, payment, contract, real-customer, public-demo, or production-promotion boundaries:

```powershell
python scripts\validate_prod_070_english_coverage_knowledge_policy_probe.py
```

Run the PROD-071 English coverage knowledge runtime patch:

```powershell
python scripts\run_prod_071_english_coverage_knowledge_runtime_patch.py
```

Validate that PROD-071 routes the three PROD-070 English coverage boundary gap phrases to `coverage-boundary-route`, preserves product-detail, price, and healthcare controls, records `guided_option_selection` as a future persuasion-tactics checkpoint candidate, creates no review HTML, and changes no response text, retrieval default, provider, LLM, private-data, German, voice, legal, payment, contract, real-customer, public-demo, or production-promotion boundaries:

```powershell
python scripts\validate_prod_071_english_coverage_knowledge_runtime_patch.py
```

Run the PROD-072 English coverage knowledge post-patch regression:

```powershell
python scripts\run_prod_072_english_coverage_knowledge_post_patch_regression.py
```

Validate that PROD-072 keeps the PROD-071 coverage boundary patch stable, preserves product-detail, price, healthcare, voicemail, and stable English multi-turn controls, keeps `guided_option_selection` as a future persuasion-tactics checkpoint candidate only, creates no review HTML, and changes no runtime behavior, response text, classifier reachability, next action, call-control behavior, retrieval default, provider, LLM, private-data, German, voice, legal, payment, contract, real-customer, public-demo, or production-promotion boundaries:

```powershell
python scripts\validate_prod_072_english_coverage_knowledge_post_patch_regression.py
```

Run the PROD-073 English customer-move classification gate decision:

```powershell
python scripts\run_prod_073_english_customer_move_classification_gate_decision.py
```

Validate that PROD-073 keeps the remaining broad `customer_move_classification_outside_selected_non_refusal_groups` gate decision-only, blocks a broad classifier patch, requires a narrow slice inventory next, creates no review HTML, and changes no runtime behavior, response text, classifier reachability, retrieval default, provider, LLM, private-data, German, voice, legal, payment, contract, real-customer, public-demo, or production-promotion boundaries:

```powershell
python scripts\validate_prod_073_english_customer_move_classification_gate_decision.py
```

Run the PROD-074 English customer-move classification slice inventory:

```powershell
python scripts\run_prod_074_english_customer_move_classification_slice_inventory.py
```

Validate that PROD-074 inventories the current deterministic classifier surface, identifies `provider-comparison` as the unreachable localized response type, keeps the checkpoint inventory-only, creates no review HTML, recommends the provider-comparison reachability review next, and changes no runtime behavior, response text, classifier reachability, retrieval default, provider, LLM, private-data, German, voice, legal, payment, contract, real-customer, public-demo, or production-promotion boundaries:

```powershell
python scripts\validate_prod_074_english_customer_move_classification_slice_inventory.py
```

Run the PROD-075 English provider-comparison reachability review packet:

```powershell
python scripts\run_prod_075_english_provider_comparison_reachability_review.py
```

Validate that PROD-075 creates only the provider-comparison human review packet, writes the browser review HTML, requires review before the next checkpoint, recommends the review-import checkpoint next, and changes no runtime behavior, response text, classifier reachability, retrieval default, provider, LLM, private-data, German, voice, legal, payment, contract, real-customer, public-demo, or production-promotion boundaries:

```powershell
python scripts\validate_prod_075_english_provider_comparison_reachability_review.py
```

Run the PROD-076 English provider-comparison review import:

```powershell
python scripts\run_prod_076_english_provider_comparison_review_import.py
```

Validate that PROD-076 imports Tarik's provider-comparison review as approve for narrow probe with brevity constraint, records that the response is not approved as exact wording, requires a known comparison target, recommends the narrow-probe design checkpoint next, creates no review HTML, and changes no runtime behavior, response text, classifier reachability, retrieval default, provider, LLM, private-data, German, voice, legal, payment, contract, real-customer, public-demo, or production-promotion boundaries:

```powershell
python scripts\validate_prod_076_english_provider_comparison_review_import.py
```

Run the PROD-077 English provider-comparison narrow probe design:

```powershell
python scripts\run_prod_077_english_provider_comparison_narrow_probe_design.py
```

Validate that PROD-077 designs the narrow `provider-comparison` probe with `compare_or_difference_signal` plus `known_comparison_target_signal`, selects the shorter candidate response, requires insertion before `existing-provider-gap` if patched later, creates no review HTML, recommends the runtime patch checkpoint next, and changes no runtime behavior, response text, classifier reachability, retrieval default, provider, LLM, private-data, German, voice, legal, payment, contract, real-customer, public-demo, or production-promotion boundaries:

```powershell
python scripts\validate_prod_077_english_provider_comparison_narrow_probe_design.py
```

Run the PROD-078 English provider-comparison runtime patch:

```powershell
python scripts\run_prod_078_english_provider_comparison_runtime_patch.py
```

Validate that PROD-078 applies the narrow English `provider-comparison` branch, uses the shorter response, requires a known comparison target, preserves existing-provider, price, generic-product, payment, and sign-up controls, creates no review HTML, recommends post-patch regression next, and keeps retrieval, provider, LLM, private-data, German, voice, legal, payment, contract, real-customer, public-demo, and production-promotion boundaries blocked:

```powershell
python scripts\validate_prod_078_english_provider_comparison_runtime_patch.py
```

Run the PROD-079 English provider-comparison post-patch regression:

```powershell
python scripts\run_prod_079_english_provider_comparison_post_patch_regression.py
```

Validate that PROD-079 preserves provider-comparison positives, existing-provider-gap controls, adjacent price/product/written-info/payment/sign-up controls, reruns the stable English guard, creates no review HTML, recommends remaining-slice selection next, and changes no runtime behavior, response text, classifier reachability, retrieval default, provider, LLM, private-data, German, voice, legal, payment, contract, real-customer, public-demo, or production-promotion boundaries:

```powershell
python scripts\validate_prod_079_english_provider_comparison_post_patch_regression.py
```

Run the PROD-080 English customer-move remaining slice selection:

```powershell
python scripts\run_prod_080_english_customer_move_remaining_slice_selection.py
```

Validate that PROD-080 closes the unreachable-existing-response-types slice, selects `unknown_runtime_signal_subtypes` as the next inventory-only slice, requires protected boundary controls, creates no review HTML, recommends the unknown-runtime-signal inventory next, and changes no runtime behavior, response text, classifier reachability, retrieval default, provider, LLM, private-data, German, voice, legal, payment, contract, real-customer, public-demo, or production-promotion boundaries:

```powershell
python scripts\validate_prod_080_english_customer_move_remaining_slice_selection.py
```

Run the PROD-081 English unknown runtime signal subtype inventory:

```powershell
python scripts\run_prod_081_english_unknown_runtime_signal_subtype_inventory.py
```

Validate that PROD-081 inventories English `unknown-runtime-signal` subtypes, keeps guided option selection as review-gated, requires two real options plus `neither`, `not now`, and `explain the difference` guardrails, verifies protected boundary controls, creates no review HTML, recommends the guided option selection review next, and changes no runtime behavior, response text, classifier reachability, retrieval default, provider, LLM, private-data, German, voice, legal, payment, contract, real-customer, public-demo, or production-promotion boundaries:

```powershell
python scripts\validate_prod_081_english_unknown_runtime_signal_subtype_inventory.py
```

Run the PROD-082 English guided option selection review packet:

```powershell
python scripts\run_prod_082_english_guided_option_selection_review.py
```

Validate that PROD-082 creates the browser HTML review packet for `guided_option_selection_candidate`, includes `$29`/`$59` examples, `neither`, `not now`, `explain the difference`, and `no payment details needed` paths, supports JSON export/import, recommends review import next, and changes no runtime behavior, response text, classifier reachability, retrieval default, provider, LLM, private-data, German, voice, legal, payment, contract, real-customer, public-demo, or production-promotion boundaries:

```powershell
python scripts\validate_prod_082_english_guided_option_selection_review.py
```

Run the PROD-083 English guided option selection review import:

```powershell
python scripts\run_prod_083_english_guided_option_selection_review_import.py
```

Validate that PROD-083 imports Tarik's review as `needs_rewrite_before_probe`, rejects the current examples, requires leaving obvious facts out, avoiding repetition, using a plan feature matrix, approved campaign payment-path explanation, no payment on the call by default, sparse contextual discourse markers instead of random fillers, creates no review HTML, recommends rewrite design next, and changes no runtime behavior, response text, classifier reachability, retrieval default, provider, LLM, private-data, German, voice, legal, payment, contract, real-customer, public-demo, or production-promotion boundaries:

```powershell
python scripts\validate_prod_083_english_guided_option_selection_review_import.py
```

Run the PROD-084 English guided option selection rewrite review packet:

```powershell
python scripts\run_prod_084_english_guided_option_selection_rewrite_design.py
```

Validate that PROD-084 creates the browser HTML review packet for rewritten guided option examples, uses a review-only plan feature matrix, includes sparse contextual discourse markers while blocking random fillers, keeps no payment on the call by default, recommends review import next, and changes no runtime behavior, response text, classifier reachability, retrieval default, provider, LLM, private-data, German, voice, legal, payment, contract, real-customer, public-demo, or production-promotion boundaries:

```powershell
python scripts\validate_prod_084_english_guided_option_selection_rewrite_design.py
```

Run the PROD-085 English guided option selection rewrite review import:

```powershell
python scripts\run_prod_085_english_guided_option_selection_rewrite_review_import.py
```

Validate that PROD-085 imports Tarik's review as approve rewrite for policy probe with payment wording edit, preserves the source artifact, replaces example seven with `No payment on this call. I'll send you the link by email, and you can review the plan and register there.`, removes the `companyname.com` placeholder from the approved candidate packet, creates no review HTML, recommends the narrow policy probe next, and changes no runtime behavior, response text, classifier reachability, retrieval default, provider, LLM, private-data, German, voice, legal, payment, contract, real-customer, public-demo, or production-promotion boundaries:

```powershell
python scripts\validate_prod_085_english_guided_option_selection_rewrite_review_import.py
```

Run the PROD-086 English guided option selection narrow policy probe:

```powershell
python scripts\run_prod_086_english_guided_option_selection_narrow_policy_probe.py
```

Validate that PROD-086 tests the approved-with-edit candidate packet, records policy probe passed: `true`, requires plan feature matrix, customer facts for steering, no payment on this call, shorter email-link payment wording, no `companyname.com` generic payment placeholder, blocks random fillers, creates no review HTML, recommends the runtime patch next, and changes no runtime behavior, response text, classifier reachability, retrieval default, provider, LLM, private-data, German, voice, legal, payment, contract, real-customer, public-demo, or production-promotion boundaries:

```powershell
python scripts\validate_prod_086_english_guided_option_selection_narrow_policy_probe.py
```

Run the PROD-087 English guided option selection runtime patch verification:

```powershell
python scripts\run_prod_087_english_guided_option_selection_runtime_patch.py
```

Validate that PROD-087 applies the narrow English `guided-option-selection` runtime patch, requires plan feature matrix and customer facts for steering, uses `No payment on this call. I'll send you the link by email, and you can review the plan and register there.`, keeps card/payment-detail requests on the protected payment boundary, creates no review HTML, recommends post-patch regression next, changes runtime behavior, response text behavior, and classifier behavior for this branch only, and keeps retrieval, provider, LLM, private-data, German, voice, legal, payment collection, contract, real-customer, public-demo, and production-promotion boundaries blocked:

```powershell
python scripts\validate_prod_087_english_guided_option_selection_runtime_patch.py
```

Run the PROD-088 English guided option selection post-patch regression:

```powershell
python scripts\run_prod_088_english_guided_option_selection_post_patch_regression.py
```

Validate that PROD-088 verifies the guided-option runtime patch after application, records guided option positive failures: `0`, adjacent control failures: `0`, stable English guard passed: `true`, creates no review HTML, recommends the next remaining-slice selection, and changes no runtime behavior, response text behavior, classifier behavior, retrieval default, provider, LLM, private-data, German, voice, legal, payment, contract, real-customer, public-demo, or production-promotion boundaries:

```powershell
python scripts\validate_prod_088_english_guided_option_selection_post_patch_regression.py
```

Run the PROD-089 English customer-move remaining slice selection after guided option:

```powershell
python scripts\run_prod_089_english_customer_move_remaining_slice_selection_after_guided_option.py
```

Validate that PROD-089 re-probes the old unknown-runtime-signal inventory after guided option selection, selects `guided_option_synonym_coverage`, records old unknown cases now guided option: `5`, selected gap count: `2`, requires human review before next checkpoint: `false`, creates no review HTML, recommends `PROD-090-english-guided-option-synonym-coverage-narrow-probe`, and changes no runtime behavior, response text behavior, classifier behavior, retrieval default, provider, LLM, private-data, German, voice, legal, payment, contract, real-customer, public-demo, or production-promotion boundaries:

```powershell
python scripts\validate_prod_089_english_customer_move_remaining_slice_selection_after_guided_option.py
```

Run the PROD-090 English guided option synonym coverage narrow policy probe:

```powershell
python scripts\run_prod_090_english_guided_option_synonym_coverage_narrow_probe.py
```

Validate that PROD-090 tests the two selected guided-option near-synonym gaps, records policy probe passed: `true`, current runtime gap count: `2`, selected gap count: `2`, creates no review HTML, recommends `PROD-091-english-guided-option-synonym-coverage-runtime-patch`, and changes no runtime behavior, response text behavior, classifier behavior, retrieval default, provider, LLM, private-data, German, voice, legal, payment, contract, real-customer, public-demo, or production-promotion boundaries:

```powershell
python scripts\validate_prod_090_english_guided_option_synonym_coverage_narrow_probe.py
```

Run the PROD-091 English guided option synonym coverage runtime patch verification:

```powershell
python scripts\run_prod_091_english_guided_option_synonym_coverage_runtime_patch.py
```

Validate that PROD-091 applies the smallest guided-option synonym runtime patch, records selected gap fixed count: `2`, positive case failures: `0`, control case failures: `0`, creates no review HTML, recommends `PROD-092-english-guided-option-synonym-coverage-post-patch-regression`, changes runtime behavior, response text behavior, and classifier behavior for this branch only, and keeps retrieval, provider, LLM, private-data, German, voice, legal, payment collection, contract, real-customer, public-demo, and production-promotion boundaries blocked:

```powershell
python scripts\validate_prod_091_english_guided_option_synonym_coverage_runtime_patch.py
```

Run the PROD-092 English guided option synonym coverage post-patch regression:

```powershell
python scripts\run_prod_092_english_guided_option_synonym_coverage_post_patch_regression.py
```

Validate that PROD-092 verifies the guided-option synonym runtime patch after application, records synonym positive failures: `0`, adjacent control failures: `0`, stable English guard passed: `true`, creates no review HTML, recommends `PROD-093-english-customer-move-remaining-slice-selection-after-guided-option-synonyms`, and changes no runtime behavior, response text behavior, classifier behavior, retrieval default, provider, LLM, private-data, German, voice, legal, payment, contract, real-customer, public-demo, or production-promotion boundaries:

```powershell
python scripts\validate_prod_092_english_guided_option_synonym_coverage_post_patch_regression.py
```

Run the PROD-093 English customer-move remaining slice selection after guided option synonyms:

```powershell
python scripts\run_prod_093_english_customer_move_remaining_slice_selection_after_guided_option_synonyms.py
```

Validate that PROD-093 selects `next_step_process_clarity`, records selected remaining case: `prod-081-next-step-01`, advice roleplay deferred for review: `true`, generic confusion kept unknown: `true`, requires human review before next checkpoint: `false`, creates no review HTML, recommends `PROD-094-english-next-step-process-clarity-narrow-probe`, and changes no runtime behavior, response text behavior, classifier behavior, retrieval default, provider, LLM, private-data, German, voice, legal, payment, contract, real-customer, public-demo, or production-promotion boundaries:

```powershell
python scripts\validate_prod_093_english_customer_move_remaining_slice_selection_after_guided_option_synonyms.py
```

Run the PROD-094 English next-step process clarity narrow policy probe:

```powershell
python scripts\run_prod_094_english_next_step_process_clarity_narrow_probe.py
```

Validate that PROD-094 probes concise post-yes process wording, records process clarity probe passed: `true`, current runtime gap count: `1`, no payment on this call default: `true`, email link register path allowed: `true`, creates no review HTML, recommends `PROD-095-english-next-step-process-clarity-runtime-patch`, and changes no runtime behavior, response text behavior, classifier behavior, retrieval default, provider, LLM, private-data, German, voice, legal, payment, contract, real-customer, public-demo, or production-promotion boundaries:

```powershell
python scripts\validate_prod_094_english_next_step_process_clarity_narrow_probe.py
```

Run the PROD-095 English next-step process clarity runtime patch verification:

```powershell
python scripts\run_prod_095_english_next_step_process_clarity_runtime_patch.py
```

Validate that PROD-095 applies the smallest English process-clarity runtime patch, records selected gap fixed count: `1`, positive case failures: `0`, control case failures: `0`, no payment on this call default: `true`, email link register path allowed: `true`, creates no review HTML, recommends `PROD-096-english-next-step-process-clarity-post-patch-regression`, changes runtime behavior, response text behavior, and classifier behavior for this branch only, and keeps retrieval, provider, LLM, private-data, German, voice, legal, payment collection, contract, real-customer, public-demo, and production-promotion boundaries blocked:

```powershell
python scripts\validate_prod_095_english_next_step_process_clarity_runtime_patch.py
```

Run the PROD-096 English next-step process clarity post-patch regression:

```powershell
python scripts\run_prod_096_english_next_step_process_clarity_post_patch_regression.py
```

Validate that PROD-096 verifies the process-clarity runtime patch after application, records process clarity positive failures: `0`, adjacent control failures: `0`, stable English guard passed: `true`, creates no review HTML, recommends `PROD-097-english-customer-move-remaining-slice-selection-after-process-clarity`, and changes no runtime behavior, response text behavior, classifier behavior, retrieval default, provider, LLM, private-data, German, voice, legal, payment, contract, real-customer, public-demo, or production-promotion boundaries:

```powershell
python scripts\validate_prod_096_english_next_step_process_clarity_post_patch_regression.py
```

Run the PROD-097 English customer-move remaining slice selection after process clarity:

```powershell
python scripts\run_prod_097_english_customer_move_remaining_slice_selection_after_process_clarity.py
```

Validate that PROD-097 selects `recommendation_roleplay_boundary`, records selected remaining case: `prod-081-recommendation-02`, requires human review before next checkpoint: `true`, creates review HTML, recommends `PROD-098-english-recommendation-roleplay-review-import`, and changes no runtime behavior, response text behavior, classifier behavior, retrieval default, provider, LLM, private-data, German, voice, legal, payment, contract, real-customer, public-demo, or production-promotion boundaries:

```powershell
python scripts\validate_prod_097_english_customer_move_remaining_slice_selection_after_process_clarity.py
```

Run the PROD-098 English recommendation roleplay review import:

```powershell
python scripts\run_prod_098_english_recommendation_roleplay_review_import.py
```

Validate that PROD-098 imports Tarik's recommendation-roleplay review, records approve for policy probe with two wording edits, preserves `if you need to` and `but I can show`, creates no review HTML, recommends `PROD-099-english-recommendation-roleplay-narrow-policy-probe`, and changes no runtime behavior, response text behavior, classifier behavior, retrieval default, provider, LLM, private-data, German, voice, legal, payment, contract, real-customer, public-demo, or production-promotion boundaries:

```powershell
python scripts\validate_prod_098_english_recommendation_roleplay_review_import.py
```

Run the PROD-099 English recommendation-roleplay narrow policy probe:

```powershell
python scripts\run_prod_099_english_recommendation_roleplay_narrow_policy_probe.py
```

Validate that PROD-099 probes `recommendation_roleplay_boundary`, records recommendation roleplay probe passed: `true`, current runtime gap count: `7`, requires customer facts for recommendation: `true`, requires agency preservation: `true`, creates no review HTML, recommends `PROD-100-english-recommendation-roleplay-runtime-patch`, and changes no runtime behavior, response text behavior, classifier behavior, retrieval default, provider, LLM, private-data, German, voice, legal, payment, contract, real-customer, public-demo, or production-promotion boundaries:

```powershell
python scripts\validate_prod_099_english_recommendation_roleplay_narrow_policy_probe.py
```

Run the PROD-100 English recommendation-roleplay runtime patch:

```powershell
python scripts\run_prod_100_english_recommendation_roleplay_runtime_patch.py
```

Validate that PROD-100 applies the English recommendation-roleplay runtime patch, records selected gap fixed count: `7`, positive case failures: `0`, control case failures: `0`, requires customer facts for recommendation: `true`, requires agency preservation: `true`, no agent decides for customer: `true`, no value guarantee: `true`, creates no review HTML, recommends `PROD-101-english-recommendation-roleplay-post-patch-regression`, changes English runtime behavior, response text behavior, and classifier behavior for the selected branch, and leaves retrieval default, provider, LLM, private-data, German, voice, legal, payment, contract, real-customer, public-demo, and production-promotion boundaries blocked:

```powershell
python scripts\validate_prod_100_english_recommendation_roleplay_runtime_patch.py
```

Run the PROD-101 English recommendation-roleplay post-patch regression:

```powershell
python scripts\run_prod_101_english_recommendation_roleplay_post_patch_regression.py
```

Validate that PROD-101 verifies the English recommendation-roleplay runtime patch after application, records recommendation roleplay positive failures: `0`, adjacent control failures: `0`, stable English guard passed: `true`, requires customer facts for recommendation: `true`, requires agency preservation: `true`, no agent decides for customer: `true`, no value guarantee: `true`, review HTML created: `false`, do not open the next checkpoint in this run: `true`, changes no runtime behavior, response text behavior, classifier behavior, retrieval default, provider, LLM, private-data, German, voice, legal, payment, contract, real-customer, public-demo, or production-promotion boundaries:

```powershell
python scripts\validate_prod_101_english_recommendation_roleplay_post_patch_regression.py
```

PROD checkpoints that ask Tarik for review should include a browser-openable HTML review file with concrete examples. For PROD-059:

```text
research\experiments\generated\PROD-059-final-english-only-runtime-readiness-review\prod_059_review.html
```

For PROD-060:

```text
research\experiments\generated\PROD-060-runtime-promotion-path-decision\prod_060_review.html
```

For PROD-075:

```text
research\experiments\generated\PROD-075-english-provider-comparison-reachability-review\prod_075_review.html
```

For PROD-084:

```text
research\experiments\generated\PROD-084-english-guided-option-selection-rewrite-design\prod_084_review.html
```

PROD checkpoints should not generate HTML for routine inventories, prioritization packets, validator evidence, or agent-internal checkpoints where no human review is required.

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

## ElevenLabs Agent Automation

Build the ELEVENLABS-002 dry-run automation plan and API request bundle for the current Atlas/Web Design ElevenLabs agent:

```powershell
python scripts\run_elevenlabs_agent_automation.py --agent-id agent_7801kt0g32zxf4f8x5zkykj7syty
```

Validate the automation lane without provider calls:

```powershell
python scripts\validate_elevenlabs_002_agent_automation.py
```

Validate the copied-config PATCH payload generator without provider calls:

```powershell
python scripts\validate_elevenlabs_003_agent_config_patcher.py
```

Validate the Mike's Kitchen dynamic-variable test pack without provider calls:

```powershell
python scripts\validate_elevenlabs_004_mikes_kitchen_dynamic_tests.py
```

Validate the Mike's Kitchen multi-turn scenario test pack without provider calls:

```powershell
python scripts\validate_elevenlabs_005_mikes_kitchen_scenario_tests.py
```

Validate the web design naturalness patch without provider calls:

```powershell
python scripts\validate_elevenlabs_006_web_design_naturalness_patch.py
```

Validate the web design dynamism/naturalness stress pack without provider calls:

```powershell
python scripts\validate_elevenlabs_007_web_design_dynamism.py
```

Validate the web design value/pricing repair pack without provider calls:

```powershell
python scripts\validate_elevenlabs_008_web_design_value_pricing.py
```

Build the Mike's Kitchen dynamic test API request bundle without provider calls:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_mikes_kitchen_tests.package.json `
  --agent-id agent_7801kt0g32zxf4f8x5zkykj7syty `
  --out research\experiments\generated\ELEVENLABS-004-mikes-kitchen-dynamic-tests\automation_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-004-mikes-kitchen-dynamic-tests\api_requests.json
```

Build the Mike's Kitchen scenario test API request bundle and folder plan without provider calls:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_mikes_kitchen_scenario_tests.package.json `
  --agent-id agent_7801kt0g32zxf4f8x5zkykj7syty `
  --test-folder-name "Atlas Web Studio - Mike's Kitchen Scenarios" `
  --out research\experiments\generated\ELEVENLABS-005-mikes-kitchen-scenario-tests\automation_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-005-mikes-kitchen-scenario-tests\api_requests.json
```

Create the Mike's Kitchen tests in ElevenLabs after loading `ELEVENLABS_API_KEY` into the current process:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_mikes_kitchen_tests.package.json `
  --agent-id agent_7801kt0g32zxf4f8x5zkykj7syty `
  --operation create-tests `
  --live `
  --confirm-provider-write `
  --out research\experiments\generated\ELEVENLABS-004-mikes-kitchen-dynamic-tests\automation_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-004-mikes-kitchen-dynamic-tests\api_requests.json
```

Create the Mike's Kitchen scenario tests in ElevenLabs and move them into a test folder:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_mikes_kitchen_scenario_tests.package.json `
  --agent-id agent_7801kt0g32zxf4f8x5zkykj7syty `
  --test-folder-name "Atlas Web Studio - Mike's Kitchen Scenarios" `
  --operation create-tests `
  --live `
  --confirm-provider-write `
  --out research\experiments\generated\ELEVENLABS-005-mikes-kitchen-scenario-tests\automation_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-005-mikes-kitchen-scenario-tests\api_requests.json
```

Draft an agent PATCH payload after the KB upload returns a document ID:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --agent-config runtime\providers\elevenlabs_agents\fixtures\web_design_agent_config.sanitized.json `
  --kb-document-id <returned_knowledge_base_document_id> `
  --kb-document-name universal_sales_core.md `
  --agent-patch-out research\experiments\generated\ELEVENLABS-002-agent-automation\agent_patch_payload.json
```

Draft the ELEVENLABS-006 web design naturalness PATCH payload without provider calls:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --agent-config runtime\providers\elevenlabs_agents\fixtures\web_design_agent_config.sanitized.json `
  --kb-document-id OyjSKNJnQTc84pyk1Yu0 `
  --kb-document-name universal_sales_core.md `
  --agent-prompt-file runtime\providers\elevenlabs_agents\prompts\web_design_atlas_sales_prompt.md `
  --first-message-file runtime\providers\elevenlabs_agents\prompts\web_design_first_message.txt `
  --dynamic-variable-defaults runtime\providers\elevenlabs_agents\variables\mikes_kitchen_dynamic_variable_defaults.json `
  --agent-patch-out research\experiments\generated\ELEVENLABS-006-web-design-naturalness-patch\agent_patch_payload.json `
  --out research\experiments\generated\ELEVENLABS-006-web-design-naturalness-patch\automation_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-006-web-design-naturalness-patch\api_requests.json
```

Patch the live `web design` dashboard agent after loading `ELEVENLABS_API_KEY` into the current process:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --operation patch-agent `
  --agent-config runtime\providers\elevenlabs_agents\fixtures\web_design_agent_config.sanitized.json `
  --kb-document-id OyjSKNJnQTc84pyk1Yu0 `
  --kb-document-name universal_sales_core.md `
  --agent-prompt-file runtime\providers\elevenlabs_agents\prompts\web_design_atlas_sales_prompt.md `
  --first-message-file runtime\providers\elevenlabs_agents\prompts\web_design_first_message.txt `
  --dynamic-variable-defaults runtime\providers\elevenlabs_agents\variables\mikes_kitchen_dynamic_variable_defaults.json `
  --agent-patch-out research\experiments\generated\ELEVENLABS-006-web-design-naturalness-patch\agent_patch_payload.json `
  --out research\experiments\generated\ELEVENLABS-006-web-design-naturalness-patch\automation_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-006-web-design-naturalness-patch\api_requests.json `
  --live `
  --confirm-provider-write
```

Build the ELEVENLABS-007 Mike's Kitchen naturalness test API request bundle and folder plan without provider calls:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_mikes_kitchen_naturalness_tests.package.json `
  --agent-id agent_7801kt0g32zxf4f8x5zkykj7syty `
  --test-folder-name "Atlas Web Studio - Naturalness Sales Intent Repair" `
  --out research\experiments\generated\ELEVENLABS-007-web-design-dynamism-naturalness\naturalness_tests_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-007-web-design-dynamism-naturalness\naturalness_tests_requests.json
```

Patch the live `web design` dashboard agent for ELEVENLABS-007 after loading `ELEVENLABS_API_KEY` into the current process:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --operation patch-agent `
  --agent-config runtime\providers\elevenlabs_agents\fixtures\web_design_agent_config.sanitized.json `
  --kb-document-id OyjSKNJnQTc84pyk1Yu0 `
  --kb-document-name universal_sales_core.md `
  --agent-prompt-file runtime\providers\elevenlabs_agents\prompts\web_design_atlas_sales_prompt.md `
  --first-message-file runtime\providers\elevenlabs_agents\prompts\web_design_first_message.txt `
  --dynamic-variable-defaults runtime\providers\elevenlabs_agents\variables\mikes_kitchen_dynamic_variable_defaults.json `
  --agent-temperature 0.25 `
  --agent-patch-out research\experiments\generated\ELEVENLABS-007-web-design-dynamism-naturalness\agent_patch_payload.json `
  --out research\experiments\generated\ELEVENLABS-007-web-design-dynamism-naturalness\agent_patch_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-007-web-design-dynamism-naturalness\agent_patch_requests.json `
  --live `
  --confirm-provider-write
```

Create the ELEVENLABS-007 Mike's Kitchen naturalness tests in ElevenLabs and move them into the naturalness stress folder:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_mikes_kitchen_naturalness_tests.package.json `
  --agent-id agent_7801kt0g32zxf4f8x5zkykj7syty `
  --test-folder-name "Atlas Web Studio - Naturalness Sales Intent Repair" `
  --operation create-tests `
  --live `
  --confirm-provider-write `
  --out research\experiments\generated\ELEVENLABS-007-web-design-dynamism-naturalness\naturalness_tests_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-007-web-design-dynamism-naturalness\naturalness_tests_requests.json
```

Build the ELEVENLABS-008 value/pricing test API request bundle and folder plan without provider calls:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_mikes_kitchen_value_pricing_tests.package.json `
  --agent-id agent_7801kt0g32zxf4f8x5zkykj7syty `
  --test-folder-name "Atlas Web Studio - Value Pricing Stress" `
  --out research\experiments\generated\ELEVENLABS-008-web-design-value-pricing-repair\value_pricing_tests_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-008-web-design-value-pricing-repair\value_pricing_tests_requests.json
```

Upload the updated universal sales core KB document for ELEVENLABS-008:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\universal_sales_core.package.json `
  --agent-id agent_7801kt0g32zxf4f8x5zkykj7syty `
  --operation upload-kb `
  --live `
  --confirm-provider-write `
  --out research\experiments\generated\ELEVENLABS-008-web-design-value-pricing-repair\kb_upload_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-008-web-design-value-pricing-repair\kb_upload_requests.json
```

Patch the live `web design` dashboard agent for ELEVENLABS-008 after the KB upload returns a document ID:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --operation patch-agent `
  --agent-config runtime\providers\elevenlabs_agents\fixtures\web_design_agent_config.sanitized.json `
  --kb-document-id <returned_knowledge_base_document_id> `
  --kb-document-name universal_sales_core.md `
  --agent-prompt-file runtime\providers\elevenlabs_agents\prompts\web_design_atlas_sales_prompt.md `
  --first-message-file runtime\providers\elevenlabs_agents\prompts\web_design_first_message.txt `
  --dynamic-variable-defaults runtime\providers\elevenlabs_agents\variables\mikes_kitchen_dynamic_variable_defaults.json `
  --agent-temperature 0.25 `
  --agent-patch-version-scope "ELEVENLABS-008 web design value pricing repair" `
  --agent-patch-out research\experiments\generated\ELEVENLABS-008-web-design-value-pricing-repair\agent_patch_payload.json `
  --out research\experiments\generated\ELEVENLABS-008-web-design-value-pricing-repair\agent_patch_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-008-web-design-value-pricing-repair\agent_patch_requests.json `
  --live `
  --confirm-provider-write
```

Create the ELEVENLABS-008 Mike's Kitchen value/pricing tests in ElevenLabs and move them into the value/pricing stress folder:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_mikes_kitchen_value_pricing_tests.package.json `
  --agent-id agent_7801kt0g32zxf4f8x5zkykj7syty `
  --test-folder-name "Atlas Web Studio - Value Pricing Stress" `
  --operation create-tests `
  --live `
  --confirm-provider-write `
  --out research\experiments\generated\ELEVENLABS-008-web-design-value-pricing-repair\value_pricing_tests_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-008-web-design-value-pricing-repair\value_pricing_tests_requests.json
```

Live provider writes require `ELEVENLABS_API_KEY`, `--live`, and `--confirm-provider-write`.

Validate the ELEVENLABS-009 Mike's Kitchen simulation test package without provider calls:

```powershell
python scripts\validate_elevenlabs_009_mikes_kitchen_simulation_tests.py
```

Build the ELEVENLABS-009 simulation test API request bundle and folder plan without provider calls:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_mikes_kitchen_simulation_tests.package.json `
  --agent-id agent_7801kt0g32zxf4f8x5zkykj7syty `
  --test-folder-name "Atlas Web Studio - Mike's Kitchen Simulation Repair V22" `
  --out research\experiments\generated\ELEVENLABS-009-mikes-kitchen-simulation-tests\simulation_tests_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-009-mikes-kitchen-simulation-tests\simulation_tests_requests.json
```

Create the ELEVENLABS-009 Simulation Tests in ElevenLabs and move them into the simulation folder:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_mikes_kitchen_simulation_tests.package.json `
  --agent-id agent_7801kt0g32zxf4f8x5zkykj7syty `
  --test-folder-name "Atlas Web Studio - Mike's Kitchen Simulation Repair V22" `
  --operation create-tests `
  --live `
  --confirm-provider-write `
  --out research\experiments\generated\ELEVENLABS-009-mikes-kitchen-simulation-tests\simulation_tests_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-009-mikes-kitchen-simulation-tests\simulation_tests_requests.json
```

Run the created ELEVENLABS-009 Simulation Tests against the live `web design` agent:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_mikes_kitchen_simulation_tests.package.json `
  --agent-id agent_7801kt0g32zxf4f8x5zkykj7syty `
  --operation run-tests `
  --created-test-ids <test_id_1> <test_id_2> `
  --live `
  --confirm-provider-write `
  --out research\experiments\generated\ELEVENLABS-009-mikes-kitchen-simulation-tests\simulation_run_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-009-mikes-kitchen-simulation-tests\simulation_run_requests.json
```

Live provider writes require `ELEVENLABS_API_KEY`, `--live`, and `--confirm-provider-write`.

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

## LIVE-DEMO-001 Agent Voice Call

Validate the browser mic -> repo agent -> ElevenLabs voice demo without provider calls:

```powershell
python scripts\validate_live_demo_001_agent_voice_call.py
```

Start the supervised local demo in dry-run mode:

```powershell
python scripts\run_live_demo_001_agent_voice_call.py
```

By default, `LIVE-DEMO-001` starts with the English B2B software campaign (`campaign-prod-005-b2b-software`). The browser UI also includes a campaign selector, automatic `Start Conversation` speech loop, a manual `Send To Agent` fallback, and a local full-session transcript panel with JSON/TXT export.

The go-live and MVP boundary is defined in `docs\product\GO_LIVE_MVP_DEFINITION_AND_ROADMAP.md`. That document treats `LIVE-DEMO-001` as the active supervised local-live acceptance front end, not as the product architecture itself. `LIVE-DEMO-002` preserves the corrected text/runtime behavior; `LIVE-DEMO-003` records supervised listening acceptance; `LIVE-DEMO-004` is the narrow browser ASR turn-taking follow-up for premature auto-submit and talk-over risk; `LIVE-DEMO-005-interrupt-pace-plan-precision` follows Tarik's next listening feedback with manual interrupt, slightly faster speech, direct plan-boundary answers, and compact plan-boundary memory; `LIVE-DEMO-006-memory-transcript-visibility` adds local transcript review/export plus compact response subject/signature memory for repetition diagnosis; `LIVE-DEMO-007-human-readable-transcript-and-plain-qualification` makes the transcript human-readable by default and keeps early qualification in plain sales language; `LIVE-DEMO-008-prosody-review-scope-clarity` keeps tight product phrases together in provider-rendered TTS and stops asking buyers to decide internal workflow-review scope; `LIVE-DEMO-009-appointment-lead-close` makes the opener ask one permission question and moves confirmed workflow pain into appointment-setting as the current MVP close; `LIVE-DEMO-010-live-feedback-route-polish` makes opener time refusals heard, moves observed missed-lead pain to the appointment ask, blocks internal runtime phrasing, and avoids the ambiguous spreadsheet-verb pronunciation; `LIVE-DEMO-011-live-followup-stop-and-pain-close` makes callback `never` stop, shortens do-not-call wording, and moves confirmed missed-lead pain directly to the appointment ask; `LIVE-DEMO-012-soft-stop-and-context-recovery` makes soft callback refusal terminal and prevents stale timing context from hijacking purpose and owner/routing follow-up; `LIVE-DEMO-013-reasoner-route-guard` lets deterministic structured reasoning gate only high-confidence CRM/integration and previous-question clarification routes before speech, removes fixture wording from CRM answers, and keeps CRM replacement answers non-terminal; `DIALOGUE-MANAGER-001-root-repair` adds the manager action/trace around the existing policy stack; `DIALOGUE-MANAGER-002-pragmatic-dialogue-repair` adds first-class local pragmatic buyer moves behind that manager for purpose questions, term explanations, relevance challenges, buyer-led agenda repair, CRM boundary answers, previous-question clarification, and missed-pain appointment asks; `DIALOGUE-MANAGER-003-plain-sales-clarity-and-vague-appointment-time` makes purpose recovery customer-plain, blocks runtime-label speech, keeps missed-lead pain moving toward a Northstar workflow-review appointment, and keeps vague appointment timing open for a concrete day/time.

Record the `LIVE-DEMO-002` runtime extraction baseline without provider calls:

```powershell
python scripts\run_live_demo_002_runtime_extraction_baseline.py
```

Validate that `LIVE-DEMO-002` preserves the `LIVE-DEMO-001` baseline while using runtime-owned ASR quality, voice turn-state, session continuity, anti-loop, and product-answer modules:

```powershell
python scripts\validate_live_demo_002_runtime_extraction_baseline.py
```

Validate the narrow `LIVE-DEMO-002-conversation-stability-callback-disambiguation` checkpoint without provider calls. This checks callback workflow-vs-scheduling semantics, compact conversation memory, long-turn stability, customer-echo suppression, seller-led progression, nonblocking async enrichment boundaries, and the optional benchmark scaffold:

```powershell
python scripts\validate_live_demo_002_conversation_stability.py
```

Run the optional local/API async-enrichment benchmark scaffold in provider-off mode:

```powershell
python scripts\run_live_demo_002_llm_enrichment_benchmark.py
```

Generate the `LIVE-DEMO-003` supervised live voice acceptance packet from synthetic dry-run turns without provider calls:

```powershell
python scripts\generate_live_demo_003_acceptance_packet.py
```

This generates `acceptance_packet.json`, `acceptance_report.md`, `manual_review_form.md`, and `manual_review.csv`. The JSON is the machine artifact; use the Markdown form as the guide and the CSV as the fillable review surface.

Validate the `LIVE-DEMO-003` acceptance tooling without running browser ASR, live TTS, or provider LLM calls:

```powershell
python scripts\validate_live_demo_003_supervised_live_voice_acceptance.py
```

After Tarik runs the live demo, convert the ignored private turn JSON files into a private manual-review packet, review form, and CSV:

```powershell
python scripts\generate_live_demo_003_acceptance_packet.py --from-private-turns data\private\live-demo-003\raw-turns --out data\private\live-demo-003\acceptance_packet.json --report-out data\private\live-demo-003\acceptance_report.md --review-form-out data\private\live-demo-003\manual_review_form.md --review-csv-out data\private\live-demo-003\manual_review.csv
```

Fill `data\private\live-demo-003\manual_review.csv`, using `manual_review_form.md` as the plain-language guide. Then evaluate acceptance:

```powershell
python scripts\generate_live_demo_003_acceptance_packet.py --input data\private\live-demo-003\acceptance_packet.json --manual-review-csv data\private\live-demo-003\manual_review.csv --out data\private\live-demo-003\acceptance_packet.reviewed.json --report-out data\private\live-demo-003\acceptance_report.reviewed.md --review-form-out data\private\live-demo-003\manual_review_form.reviewed.md --review-csv-out data\private\live-demo-003\manual_review.reviewed.csv
```

Validate the `LIVE-DEMO-004-realtime-turn-taking-asr-vad` browser ASR turn-taking policy without live microphone, provider ASR, provider TTS, or provider LLM calls:

```powershell
python scripts\validate_live_demo_004_realtime_turn_taking_asr_vad.py
```

`LIVE-DEMO-004` keeps `PROD-102` closed. It does not add production VAD, provider ASR, payment, provider-hosted durable agents, voice cloning, or LLM-written final speech. The live demo still uses browser SpeechRecognition as browser-vendor ASR, but auto-submit now requires a final ASR result, waits through a longer pause window, and cancels pending submit if interim speech continues.

Validate the `LIVE-DEMO-005-interrupt-pace-plan-precision` manual-interrupt, pace, and product-plan answer precision gate without live microphone, provider ASR, provider TTS, or provider LLM calls:

```powershell
python scripts\validate_live_demo_005_interrupt_pace_plan_precision.py
```

`LIVE-DEMO-005` keeps `PROD-102` closed. It does not add true spoken barge-in, provider ASR, payment, provider-hosted durable agents, voice cloning, or LLM-written final speech. The browser demo now provides an `Interrupt Agent` button and `Escape` shortcut that stop current spoken output and return to listening after local microphone consent; true voice barge-in remains a future streaming ASR/VAD checkpoint.

Validate the `LIVE-DEMO-006-memory-transcript-visibility` transcript and memory repetition gate without live microphone, provider ASR, provider TTS, or provider LLM calls:

```powershell
python scripts\validate_live_demo_006_memory_transcript_visibility.py
```

`LIVE-DEMO-006` keeps `PROD-102` closed. It does not add spoken backchannels, true spoken barge-in, provider ASR, payment, provider-hosted durable agents, voice cloning, or LLM-written final speech. The browser demo now exposes a full local text transcript for the current session, with JSON/TXT export, memory/stability/provider-boundary fields, and no audio storage.

Validate the `LIVE-DEMO-007-human-readable-transcript-and-plain-qualification` UI and early-qualification gate without live microphone, provider ASR, provider TTS, or provider LLM calls:

```powershell
python scripts\validate_live_demo_007_human_transcript_plain_qualification.py
```

`LIVE-DEMO-007` keeps `PROD-102` closed. It does not add spoken backchannels, true spoken barge-in, provider ASR, payment, provider-hosted durable agents, voice cloning, or LLM-written final speech. The visible browser transcript now appears before the raw turn packet and defaults to buyer/agent/call-control lines, while diagnostics remain in a collapsible section and JSON export. For live debugging, place browser transcript JSON files under `data\private\live-demo-003\raw-turns\browser-transcript`; do not commit files from that private folder.

Validate the `LIVE-DEMO-008-prosody-review-scope-clarity` provider-rendered phrase-flow and review-scope wording gate without live microphone, provider ASR, provider TTS, or provider LLM calls:

```powershell
python scripts\validate_live_demo_008_prosody_review_scope_clarity.py
```

`LIVE-DEMO-008` keeps `PROD-102` closed. It does not add spoken backchannels, true spoken barge-in, provider ASR, payment, provider-hosted durable agents, voice cloning, or LLM-written final speech. It ensures provider-rendered TTS does not insert breaks inside `callback reminders` or `owner and reminder`, and it changes callback-gap follow-up text so the agent states what the workflow review would focus on before asking whether that buyer gap is worth checking. Continue placing browser transcript JSON files under `data\private\live-demo-003\raw-turns\browser-transcript`; do not commit private transcript files.

Validate the `LIVE-DEMO-009-appointment-lead-close` opening and appointment-setting close gate without live microphone, provider ASR, provider TTS, or provider LLM calls:

```powershell
python scripts\validate_live_demo_009_appointment_lead_close.py
```

`LIVE-DEMO-009` keeps `PROD-102` closed. It does not add spoken backchannels, true spoken barge-in, provider ASR, payment, provider-hosted durable agents, voice cloning, or LLM-written final speech. It makes the opener ask one permission question before qualification, treats appointment-setting as the current MVP close after a selected workflow gap and buyer agreement, preserves explicit callback scheduling, and confirms workflow-review times only after appointment context. Continue placing browser transcript JSON files under `data\private\live-demo-003\raw-turns\browser-transcript`; do not commit private transcript files.

Validate the `LIVE-DEMO-010-live-feedback-route-polish` gate without live microphone, provider ASR, provider TTS, provider LLM calls, or local LLM calls:

```powershell
python scripts\validate_live_demo_010_live_feedback_route_polish.py
```

`LIVE-DEMO-010` keeps `PROD-102` closed. It does not add spoken backchannels, true spoken barge-in, provider ASR, payment, provider-hosted durable agents, voice cloning, local LLM wiring, or LLM-written final speech. It makes `no I don't` after the opener route to callback timing instead of qualification, moves observed missed-lead pain toward the Northstar workflow-review appointment ask, keeps non-time confirmations after appointment context on the time request, blocks internal runtime phrases from customer speech, and avoids the ambiguous spreadsheet-verb TTS phrase. Continue placing browser transcript JSON files under `data\private\live-demo-003\raw-turns\browser-transcript`; do not commit private transcript files.

Validate the `LIVE-DEMO-011-live-followup-stop-and-pain-close` gate without live microphone, provider ASR, provider TTS, provider LLM calls, or local LLM calls:

```powershell
python scripts\validate_live_demo_011_live_followup_stop_and_pain_close.py
```

`LIVE-DEMO-011` keeps `PROD-102` closed. It does not add spoken backchannels, true spoken barge-in, provider ASR, payment, provider-hosted durable agents, voice cloning, local LLM wiring, or LLM-written final speech. It makes `never` after a callback-time request end the call, shortens explicit do-not-call wording, maps ASR-style `Leeds` to missed leads, and moves confirmed missed-lead pain directly to the Northstar workflow-review appointment ask. Continue placing browser transcript JSON files under `data\private\live-demo-003\raw-turns\browser-transcript`; do not commit private transcript files.

Validate the `LIVE-DEMO-012-soft-stop-and-context-recovery` gate without live microphone, provider ASR, provider TTS, provider LLM calls, or local LLM calls:

```powershell
python scripts\validate_live_demo_012_soft_stop_and_context_recovery.py
```

`LIVE-DEMO-012` keeps `PROD-102` closed. It does not add spoken backchannels, true spoken barge-in, provider ASR, payment, provider-hosted durable agents, voice cloning, local LLM wiring, or LLM-written final speech. It makes soft callback refusal after callback timing end the call, makes ASR-shaped purpose questions override stale timing context, resets purpose recovery to qualification, and keeps owner/routing answers on the sales workflow track. Continue placing browser transcript JSON files under `data\private\live-demo-003\raw-turns\browser-transcript`; do not commit private transcript files.

Validate the `LIVE-DEMO-013-reasoner-route-guard` gate without live microphone, provider ASR, provider TTS, provider LLM calls, or local LLM calls:

```powershell
python scripts\validate_live_demo_013_reasoner_route_guard.py
```

`LIVE-DEMO-013` keeps `PROD-102` closed. It does not add spoken backchannels, true spoken barge-in, provider ASR, payment, provider-hosted durable agents, voice cloning, local LLM wiring, or LLM-written final speech. It moves deterministic structured reasoning before final speech only for narrow CRM/integration and previous-question clarification routes, removes customer-facing fixture labels such as `fictional profile`, keeps CRM replacement answers open for qualification, and defers to more specific existing repair routes when they match. Continue placing browser transcript JSON files under `data\private\live-demo-003\raw-turns\browser-transcript`; do not commit private transcript files.

Validate the `DIALOGUE-MANAGER-001-root-repair` gate without live microphone, provider ASR, provider TTS, provider LLM calls, or local LLM calls:

```powershell
python scripts\validate_dialogue_manager_001_root_repair.py
```

`DIALOGUE-MANAGER-001` keeps `PROD-102` closed. It does not install or wire a local LLM, does not add provider ASR, does not allow LLM-written final speech, and does not broaden appointment-setting into full sale/payment/contract closure. It adds `runtime\core\dialogue_manager.py` as the live-demo control-plane shell so each tested final response carries one manager action, template id, state trace, final-response source, repair chain, and call-control trace around the existing policy stack. Continue placing browser transcript JSON files under `data\private\live-demo-003\raw-turns\browser-transcript`; do not commit private transcript files.

Validate the `DIALOGUE-MANAGER-002-pragmatic-dialogue-repair` gate without live microphone, provider ASR, provider TTS, provider LLM calls, or local LLM calls:

```powershell
python scripts\validate_dialogue_manager_002_pragmatic_dialogue_repair.py
```

`DIALOGUE-MANAGER-002` keeps `PROD-102` closed. It does not install or wire a local LLM, does not add provider ASR, does not allow LLM-written final speech, and does not broaden appointment-setting into full sale/payment/contract closure. It adds `runtime\core\dialogue_pragmatics.py` behind the manager so small human dialogue moves become explicit manager-owned actions instead of scattered policy exceptions. Continue placing browser transcript JSON files under `data\private\live-demo-003\raw-turns\browser-transcript`; do not commit private transcript files.

Validate the `DIALOGUE-MANAGER-003-plain-sales-clarity-and-vague-appointment-time` gate without live microphone, provider ASR, provider TTS, provider LLM calls, or local LLM calls:

```powershell
python scripts\validate_dialogue_manager_003_plain_sales_clarity_and_vague_appointment_time.py
```

`DIALOGUE-MANAGER-003` keeps `PROD-102` closed. It does not install or wire a local LLM, does not add provider ASR, does not allow LLM-written final speech, and does not broaden appointment-setting into full sale/payment/contract closure. It keeps the manager/pragmatics architecture, but tightens spoken purpose recovery, missed-lead pain progression, already-stated-problem acknowledgement, customer-facing jargon guards, and vague appointment-time clarification. Continue placing browser transcript JSON files under `data\private\live-demo-003\raw-turns\browser-transcript`; do not commit private transcript files.

Validate the `LIVE-DEMO-014-clear-pain-callback-followup` gate without live microphone, provider ASR, provider TTS, provider LLM calls, or local LLM calls:

```powershell
python scripts\validate_live_demo_014_clear_pain_callback_followup.py
```

`LIVE-DEMO-014` keeps `PROD-102` closed. It does not install or wire a local LLM, does not add provider ASR, does not allow LLM-written final speech, and does not broaden appointment-setting into full sale/payment/contract closure. It acknowledges `it's all clear`, moves stated missed callbacks toward a Northstar workflow-review ask without callback-scheduling ambiguity, explains `Growth` if asked, treats `think about it` as callback follow-up instead of a stop, and keeps callback-later agreement open until a usable callback time is captured. Continue placing browser transcript JSON files under `data\private\live-demo-003\raw-turns\browser-transcript`; do not commit private transcript files.

Run the `DIALOGUE-REASONER-001` structured runtime reasoner baseline over 30 frozen live-demo dialogue-act cases without provider calls:

```powershell
python scripts\run_dialogue_reasoner_001_baseline.py
```

Validate that `DIALOGUE-REASONER-001` keeps LLM reasoning default-off, sends no transcript text to a provider, preserves live-demo response behavior, maps every frozen case to strict intent/strategy JSON, records generated evidence, and keeps `PROD-102` closed:

```powershell
python scripts\validate_dialogue_reasoner_001.py
```

Run the `DIALOGUE-REASONER-002` LLM provider evaluation dry-run without network calls:

```powershell
python scripts\run_dialogue_reasoner_002_provider_evaluation.py
```

Validate that `DIALOGUE-REASONER-002` keeps provider calls default-off, blocks live mode without explicit config, does not log API key values, records planned 30-case provider evaluation evidence, and keeps `PROD-102` closed:

```powershell
python scripts\validate_dialogue_reasoner_002_provider_evaluation.py
```

Create/fill the ignored local dialogue-reasoner env file at `runtime\config\local\dialogue_reasoner.env`, using `runtime\config\local\dialogue_reasoner.env.example` as the shape.

Run a live OpenAI-compatible dialogue-reasoner provider evaluation only after filling `DIALOGUE_REASONER_API_KEY`, `DIALOGUE_REASONER_BASE_URL`, and `DIALOGUE_REASONER_MODEL` in that local env file or in the same shell:

```powershell
python scripts\run_dialogue_reasoner_002_provider_evaluation.py --live --consent-confirmed
```

Run the `DIALOGUE-REASONER-003` hybrid gate dry-run without provider calls. This preserves the 30 guard cases, checks 30 provider-invocation gate cases, plans 40 reasoning-only provider cases, blocks runtime-route override, and keeps `PROD-102` closed:

```powershell
python scripts\run_dialogue_reasoner_003_hybrid_gate.py
```

Validate that `DIALOGUE-REASONER-003` keeps deterministic routing in control, blocks provider calls by default and with missing config, validates the 30 guard / 30 invocation / 40 reasoning case shape, does not log API key values, and keeps `PROD-102` closed:

```powershell
python scripts\validate_dialogue_reasoner_003_hybrid_gate.py
```

Run the live hybrid reasoning-provider evaluation only after filling the ignored dialogue-reasoner env file and confirming synthetic transcript upload. The default reasoner temperature is `1`; override it only after a benchmark proves the lower setting works for the selected provider/model:

```powershell
python scripts\run_dialogue_reasoner_003_hybrid_gate.py --live --consent-confirmed --temperature 1
```

Run the `DIALOGUE-REASONER-004` async enrichment dry-run without provider calls. This proves deterministic customer responses are available before provider enrichment, queues 40 allowed enrichment packets, blocks route/final-response mutation, and keeps `PROD-102` closed:

```powershell
python scripts\run_dialogue_reasoner_004_async_enrichment.py
```

Validate that `DIALOGUE-REASONER-004` keeps async enrichment nonblocking, blocks provider calls by default and with missing config, records response fingerprints without customer-facing response text, and keeps `PROD-102` closed:

```powershell
python scripts\validate_dialogue_reasoner_004_async_enrichment.py
```

Run a one-case live async enrichment smoke only after filling the ignored dialogue-reasoner env file and confirming synthetic transcript upload. The default reasoner temperature is `1`; override it only after a benchmark proves the lower setting works for the selected provider/model:

```powershell
python scripts\run_dialogue_reasoner_004_async_enrichment.py --live --consent-confirmed --temperature 1 --max-reasoning-cases 1
```

Start it with ElevenLabs TTS after setting `ELEVENLABS_API_KEY` and an English ElevenLabs voice ID. The live demo also loads ignored `runtime\config\local\elevenlabs.env` automatically, so the API key can live there instead of being pasted into every PowerShell command. Voice IDs can stay in ignored `config\local\voice_ids.json`, `runtime\config\local\voice_ids.json`, or shell env vars.

```powershell
python scripts\run_live_demo_001_agent_voice_call.py `
  --live-tts `
  --consent-confirmed `
  --timeout-seconds 8
```

This demo keeps the agent brain inside the repo. `Start Conversation` first routes a runtime-owned `agent-open` turn so the agent speaks before browser ASR starts; the opener uses `caller_identity` and `target_account_context` to say `Maya` is `calling from Northstar Workflow Labs, the team behind RouteSignal CRM`, checks time, says it is looking for the person handling inbound demo follow-up, states the missed-callback/handoff problem, and asks a qualification question. Browser speech recognition then creates later transcripts, the local guarded runtime chooses the answer, and ElevenLabs is used only as TTS output. Browser playback volume is locally calibrated to `0.68` for both ElevenLabs audio playback and the browser fallback voice; this does not alter provider audio files or provider request shape. Session continuity handles short follow-up answers such as `price`, longer observed phrases such as `start with the price`, first-turn explicit topics such as `I want to talk about the price`, noisy ASR variants such as `price star`, ASR variants around `reviewing/viewing options is worth my time`, buyer clarification requests such as `I did not understand what you asked before` through `previous_question_clarified`, caller identity recall such as `where were you calling from again` through `caller_identity_recalled`, and bare negative replies such as `no` through `ambiguous_negative_clarified`. Greeting turns now open like a sales call with a permission/time check instead of a topic menu. Resolved focus slots persist across later turns, weak acknowledgements after the opener or after price advance into proactive guided selling instead of replaying the price sentence, generic follow-ups such as `can you tell me more` and `what else should I know` progress price, fit, timing, and feature/detail topics without replaying or reopening focus menus, and demo focus responses block `That makes sense`, focus-restatement loops, long sentence shapes, canned prior-question advancement, bare-negative obliviousness, anti-loop repair leaks, and internal guardrail/process wording. The English B2B software demo now loads the fictional `Northstar Workflow Labs` / `RouteSignal CRM` campaign profile from `research\experiments\cases\live-demo-001-fictional-b2b-sales-campaign.json`, using public lead-routing pages only as inspiration. It answers product, pricing, plan-difference, manual-tracking, small-team-fit, unnecessary-handoff, integration, and security questions from synthetic campaign facts while blocking copied real-company text, unsupported ROI/conversion/security claims, unnecessary specialist handoff for basics, and `PROD-102` opening. The demo uses a transport-neutral voice turn-state contract (`idle`, `listening`, `agent_thinking`, `agent_speaking`, `paused`) so the current browser page and later telephony/WebRTC adapters can share `voice_turn_state` semantics. Recognition stops before agent response generation, listening is blocked while the agent is thinking or speaking, and listening restarts only after voice output ends. Low-confidence browser ASR below `0.45` asks for a repeat instead of entering sales logic. Private demo turns and generated audio stay under ignored `data/private/live-demo-001/`; no provider agent, voice cloning, runtime behavior change, or live provider default is allowed.

The `LIVE-DEMO-002` guard now covers `sales_context_variety`, `sales_emphasis_priority`, `sales_context_variety_and_emphasis`, `previous_question_clarification`, `ambiguous_negative_clarification`, `caller_identity_recall`, and `internal_repair_speech_blocked`. Low-information qualification follow-ups must produce distinct seller-led responses with broader campaign context such as inbound demo ownership, routing, callbacks, handoff review, reminders, visibility, spreadsheet/shared-inbox leakage, or Slack alerts. Buyer requests to clarify the previous question must explain the prior sales question in plain terms and ask a clearer version instead of advancing canned qualification copy. Caller identity questions must answer where the agent is calling from instead of becoming fit/price/topic-menu turns. Bare negative replies must ask whether the buyer rejects timing or the problem itself instead of falling through to menus or another qualification line. Internal anti-loop repair phrases such as `avoid repeating the same question` are blocked from customer-facing speech. Voice prosody cues must emphasize problem/value targets, not greeting text or small talk. The first opener keeps pacing/emphasis cues but does not insert filler words between `calling from Northstar Workflow Labs, the team behind RouteSignal CRM` and the permission check.

The callback scheduling boundary is runtime-owned: if the buyer says `I do not have time`, the agent asks for a callback time through `callback_request_time_needed`; if the buyer then says `call me 10 a.m. tomorrow`, the agent confirms through `callback_time_confirmed`, `scheduling-confirmation`, and `schedule-and-end` instead of reopening product-topic menus.

Call-context recovery is runtime-owned: if the buyer says variants of `what do you want exactly`, `you called me`, `what is the next step`, `you are wasting time`, or `I don't know what you're talking about`, the agent answers that dialogue act with one concrete RouteSignal workflow question instead of reopening `price, fit, timing, or exact product details` or leaking anti-loop repair wording.

The audible runtime-upgrade path is also covered by the `LIVE-DEMO-001` validator. Browser fallback speech now uses markup-free RESP-003 shaped TTS input, so bounded fillers and voice naturalization are heard even without an ElevenLabs audio file. The demo enables local guarded retrieval only when the `RAG-017` registry exists; campaign facts override RAG, protected contexts block retrieval influence, and an eligible price-worth turn must prove real retrieval influence without opening `PROD-102`.

## UltraVox Bounded Evaluation

Generate the ULTRAVOX-001 bounded realtime voice evaluation without provider calls:

```powershell
python scripts\evaluate_ultravox_001_bounded_realtime_voice.py `
  --cases research\experiments\cases\ultravox-001-bounded-realtime-voice-evaluation.json `
  --out research\experiments\generated\ULTRAVOX-001\ULTRAVOX-001-bounded-realtime-voice-evaluation.json `
  --report-out research\experiments\generated\ULTRAVOX-001\ULTRAVOX-001-bounded-realtime-voice-evaluation-report.md
```

Validate that ULTRAVOX-001 keeps UltraVox as a bounded provider evaluation, recommends the hosted API provider-adapter as the first empirical test, keeps self-hosting as a research lane, keeps the hosted console agent out of the product runtime, preserves RESP-003 as the baseline, makes no API calls, uploads no audio, requires no secrets, creates no durable provider agent, and does not open `PROD-102`:

```powershell
python scripts\validate_ultravox_001_bounded_realtime_voice.py
```

Validate the ULTRAVOX-002 synthetic live smoke harness without provider calls:

```powershell
python scripts\validate_ultravox_002_synthetic_live_smoke.py
```

Run the approved one-call UltraVox synthetic live smoke after adding `ULTRAVOX_API_KEY` to ignored `runtime/config/local/ultravox.env`:

```powershell
python scripts\run_ultravox_002_synthetic_live_smoke.py `
  --live `
  --timeout-seconds 8
```

If provider cleanup reports that the call is still ongoing or unbilled, wait briefly and delete the recent call by the redacted suffix from the smoke output:

```powershell
python scripts\cleanup_ultravox_call_by_suffix.py --suffix <last-eight-call-id-chars>
```

Validate the ULTRAVOX-003 synthetic customer-audio turn harness without provider calls:

```powershell
python scripts\validate_ultravox_003_synthetic_audio_turn.py
```

Run the approved one-turn UltraVox synthetic customer-audio test after adding `ULTRAVOX_API_KEY` to ignored `runtime/config/local/ultravox.env`:

```powershell
python scripts\run_ultravox_003_synthetic_audio_turn.py `
  --live `
  --timeout-seconds 10
```

ULTRAVOX-003 generates synthetic customer audio locally when possible, or reuses the prior ignored `ULTRAVOX-002` synthetic audio fixture if local speech synthesis is unavailable. It streams synthetic PCM to UltraVox over server WebSocket, listens for transcript and agent audio, closes the socket, and attempts to delete the call. It must not use real customer audio, voice cloning, durable provider agents, runtime behavior changes, or open `PROD-102`.

## Explicit Opt-In Provider Commands

These commands can contact external providers. Do not run them as default setup checks.

Validate the ElevenLabs 010 sales-control repair without provider calls:

```powershell
python scripts\validate_elevenlabs_010_web_design_sales_control_repair.py
```

Validate the ElevenLabs 011 remaining simulation repair without provider calls:

```powershell
python scripts\validate_elevenlabs_011_web_design_remaining_simulation_repair.py
```

Validate the ElevenLabs 012 feedback-quality repair without provider calls:

```powershell
python scripts\validate_elevenlabs_012_web_design_feedback_quality_repair.py
```

Live ELEVENLABS-010 KB upload and agent patch requires `ELEVENLABS_API_KEY` in
the current shell and explicit `--live --confirm-provider-write`:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_sales_control_repair.package.json `
  --operation upload-kb `
  --live `
  --confirm-provider-write `
  --out research\experiments\generated\ELEVENLABS-010-web-design-sales-control-repair\kb_upload_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-010-web-design-sales-control-repair\kb_upload_requests.json
```

After the two returned KB document IDs are known:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_sales_control_repair.package.json `
  --operation patch-agent `
  --agent-config runtime\providers\elevenlabs_agents\fixtures\web_design_agent_config.sanitized.json `
  --kb-document-id <universal_sales_core_document_id> `
  --kb-document-name universal_sales_core.md `
  --kb-document-id <atlas_web_studio_campaign_document_id> `
  --kb-document-name atlas_web_studio_web_design_campaign.md `
  --agent-prompt-file runtime\providers\elevenlabs_agents\prompts\web_design_atlas_sales_prompt.md `
  --first-message-file runtime\providers\elevenlabs_agents\prompts\web_design_first_message.txt `
  --dynamic-variable-defaults runtime\providers\elevenlabs_agents\variables\mikes_kitchen_dynamic_variable_defaults.json `
  --agent-temperature 0.25 `
  --agent-patch-version-scope "ELEVENLABS-010 web design sales control repair" `
  --agent-patch-out research\experiments\generated\ELEVENLABS-010-web-design-sales-control-repair\agent_patch_payload.json `
  --out research\experiments\generated\ELEVENLABS-010-web-design-sales-control-repair\agent_patch_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-010-web-design-sales-control-repair\agent_patch_requests.json `
  --live `
  --confirm-provider-write
```

Live ELEVENLABS-011 follows the same explicit provider-write boundary with the
011 manifest and generated output folder:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_remaining_simulation_repair.package.json `
  --operation upload-kb `
  --live `
  --confirm-provider-write `
  --out research\experiments\generated\ELEVENLABS-011-web-design-remaining-simulation-repair\kb_upload_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-011-web-design-remaining-simulation-repair\kb_upload_requests.json
```

After the two returned KB document IDs are known:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_remaining_simulation_repair.package.json `
  --operation patch-agent `
  --agent-config runtime\providers\elevenlabs_agents\fixtures\web_design_agent_config.sanitized.json `
  --kb-document-id <universal_sales_core_document_id> `
  --kb-document-name universal_sales_core.md `
  --kb-document-id <atlas_web_studio_campaign_document_id> `
  --kb-document-name atlas_web_studio_web_design_campaign.md `
  --agent-prompt-file runtime\providers\elevenlabs_agents\prompts\web_design_atlas_sales_prompt.md `
  --first-message-file runtime\providers\elevenlabs_agents\prompts\web_design_first_message.txt `
  --dynamic-variable-defaults runtime\providers\elevenlabs_agents\variables\mikes_kitchen_dynamic_variable_defaults.json `
  --agent-temperature 0.25 `
  --agent-patch-version-scope "ELEVENLABS-011 web design remaining simulation repair" `
  --agent-patch-out research\experiments\generated\ELEVENLABS-011-web-design-remaining-simulation-repair\agent_patch_payload.json `
  --out research\experiments\generated\ELEVENLABS-011-web-design-remaining-simulation-repair\agent_patch_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-011-web-design-remaining-simulation-repair\agent_patch_requests.json `
  --live `
  --confirm-provider-write
```

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

Validate the RAG-022 universal sales layer contract without provider calls:

```powershell
python scripts\validate_rag_022_universal_sales_layer_contract.py
```

## Safety Rules

- Do not commit API keys, private transcripts, raw private audio, customer exports, or client-specific sensitive details.
- Default validation should not require `OPENAI_API_KEY`, `CARTESIA_API_KEY`, or `CARTESIA_VOICE_ID`.
- Local voice IDs may be stored in ignored `runtime\config\local\voice_ids.json`; API keys remain environment-only.
- Raw private call-center audio and raw transcripts must stay under ignored `data\private\` and must not be uploaded to providers by default.
- Only redacted, minimized, human-reviewed sales-pattern notes may leave `data\private\`.
- Use `--live` only when provider, consent, retention, and logging assumptions have been reviewed.
- Keep generated artifacts under `research\experiments\generated` unless a script documents another output path.
- Keep required checklists, templates, workflows, and scripts inside this repository. Do not make Emotion Aware depend on `D:\Codex\shared` or another active project folder.
