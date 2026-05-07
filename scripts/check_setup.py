#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any


PROJECT_NAME = "emotion-aware-ai-sales-agent"
ROOT = Path(__file__).resolve().parents[1]
MIN_PYTHON = (3, 10)

REQUIRED_DIRS = [
    ("dir.scripts", "scripts", "Script directory"),
    ("dir.docs_product", "docs/product", "Product documentation"),
    ("dir.docs_data", "docs/data", "Data documentation"),
    ("dir.research_experiments", "research/experiments", "Experiment notes"),
    ("dir.research_experiments_cases", "research/experiments/cases", "Experiment case files"),
    ("dir.research_experiments_generated", "research/experiments/generated", "Generated experiment artifacts"),
    ("dir.packages_prompts", "packages/prompts", "Prompt package"),
    ("dir.data_public", "data/public", "Public data folder"),
    ("dir.data_rag", "data/rag", "Source-tracked RAG data workspace"),
    ("dir.data_private", "data/private", "Local-only private call-center data folder"),
    ("dir.data_processed", "data/processed", "Processed data folder"),
    ("dir.config_local", "config/local", "Local ignored configuration folder"),
]

OPTIONAL_DIRS = [
    ("dir.data_private_restricted", "data/private-restricted", "Restricted data folder"),
]

REQUIRED_FILES = [
    ("file.agents", "AGENTS.md", "Project-local Codex instructions"),
    ("file.readme", "README.md", "Project README"),
    ("file.program", "program.md", "Research program"),
    ("file.docs_third_party_inspirations", "docs/third-party-inspirations.md", "Third-party inspiration and attribution notes"),
    ("file.docs_thesis_speech_realism_references", "docs/thesis/SPEECH_REALISM_REFERENCES.md", "Speech realism thesis references"),
    ("file.docs_thesis_reference_registry", "docs/thesis/THESIS_REFERENCE_REGISTRY.md", "Thesis reference registry"),
    ("file.docs_thesis_writing_guide", "docs/thesis/THESIS_WRITING_GUIDE.md", "Thesis writing guide"),
    ("file.docs_product_review_gates", "docs/product-review-gates.md", "Product review gates"),
    ("file.docs_product_commands", "docs/product/COMMANDS.md", "Product command map"),
    ("file.docs_product_product_brief", "docs/product/PRODUCT_BRIEF.md", "Product brief"),
    ("file.docs_product_client_mvp_workflow", "docs/product/CLIENT_MVP_WORKFLOW.md", "Client MVP workflow"),
    ("file.docs_product_context_reading_policy", "docs/product/CONTEXT_READING_POLICY.md", "Context reading policy"),
    ("file.docs_product_project_self_containment", "docs/product/PROJECT_SELF_CONTAINMENT_POLICY.md", "Project self-containment policy"),
    ("file.docs_product_project_drift_guard", "docs/product/PROJECT_DRIFT_GUARD.md", "Project drift guard"),
    ("file.docs_product_rag_001_notebooklm_source_intake", "docs/product/RAG_001_NOTEBOOKLM_SOURCE_INTAKE_BRIDGE.md", "RAG NotebookLM source intake bridge"),
    ("file.docs_product_rag_002_notebooklm_extraction_automation", "docs/product/RAG_002_NOTEBOOKLM_EXTRACTION_AUTOMATION_BRIDGE.md", "RAG NotebookLM extraction automation bridge"),
    ("file.docs_product_rag_003_report_import_readiness", "docs/product/RAG_003_REPORT_IMPORT_READINESS.md", "RAG NotebookLM report import readiness"),
    ("file.docs_product_rag_004_source_manifest_normalization", "docs/product/RAG_004_SOURCE_MANIFEST_NORMALIZATION.md", "RAG source manifest normalization"),
    ("file.docs_product_rag_005_chunk_normalization", "docs/product/RAG_005_CHUNK_NORMALIZATION.md", "RAG chunk normalization"),
    ("file.docs_product_rag_006_chunk_review_packet", "docs/product/RAG_006_CHUNK_REVIEW_PACKET.md", "RAG chunk review packet"),
    ("file.docs_product_rag_007_reviewed_first_slice", "docs/product/RAG_007_REVIEWED_FIRST_SLICE.md", "RAG reviewed first slice"),
    ("file.docs_product_rag_008_guarded_retrieval_policy", "docs/product/RAG_008_GUARDED_RETRIEVAL_POLICY.md", "RAG guarded retrieval policy"),
    ("file.docs_product_rag_009_all_source_review_coverage", "docs/product/RAG_009_ALL_SOURCE_REVIEW_COVERAGE.md", "RAG all-source review coverage"),
    ("file.docs_product_rag_010_reviewed_expansion_slice", "docs/product/RAG_010_REVIEWED_EXPANSION_SLICE.md", "RAG reviewed expansion slice"),
    ("file.docs_product_rag_011_blocker_cleanup_packet", "docs/product/RAG_011_BLOCKER_CLEANUP_PACKET.md", "RAG blocker cleanup packet"),
    ("file.docs_product_rag_012_accepted_cleanup", "docs/product/RAG_012_ACCEPTED_CLEANUP.md", "RAG accepted cleanup"),
    ("file.docs_product_rag_013_cleanup_strategy", "docs/product/RAG_013_CLEANUP_STRATEGY.md", "RAG cleanup strategy"),
    ("file.docs_product_rag_014_source_mapped_quote_followup", "docs/product/RAG_014_SOURCE_MAPPED_QUOTE_FOLLOWUP.md", "RAG source-mapped quote follow-up"),
    ("file.docs_product_rag_015_source_mapping_batches", "docs/product/RAG_015_SOURCE_MAPPING_BATCHES.md", "RAG source-mapping batches"),
    ("file.docs_product_rag_016_quote_clearance_batches", "docs/product/RAG_016_QUOTE_CLEARANCE_BATCHES.md", "RAG quote-clearance batches"),
    ("file.docs_product_rag_016a_quote_clearance_decision_slice", "docs/product/RAG_016A_QUOTE_CLEARANCE_DECISION_SLICE.md", "RAG quote-clearance decision slice"),
    ("file.docs_product_rag_016b_voice_delivery_decision_slice", "docs/product/RAG_016B_VOICE_DELIVERY_DECISION_SLICE.md", "RAG voice-delivery decision slice"),
    ("file.docs_product_rag_017_runtime_knowledge_registry", "docs/product/RAG_017_RUNTIME_KNOWLEDGE_REGISTRY.md", "RAG runtime knowledge registry"),
    ("file.docs_product_rag_018_guarded_runtime_retrieval", "docs/product/RAG_018_GUARDED_RUNTIME_RETRIEVAL.md", "RAG guarded runtime retrieval"),
    ("file.docs_product_rag_019_sales_communication_source_expansion", "docs/product/RAG_019_SALES_COMMUNICATION_SOURCE_EXPANSION.md", "RAG sales communication source expansion"),
    ("file.docs_product_voice_provider_run_boundary", "docs/product/VOICE_PROVIDER_RUN_BOUNDARY.md", "Voice provider run boundary"),
    ("file.docs_product_voice_generated_audio_asset_log", "docs/product/VOICE_GENERATED_AUDIO_ASSET_LOG.md", "Voice generated audio asset log"),
    ("file.docs_product_realtime_agent_architecture", "docs/product/REALTIME_AGENT_ARCHITECTURE.md", "Realtime architecture"),
    ("file.docs_product_realtime_turn_cli", "docs/product/REALTIME_TURN_CLI.md", "Realtime CLI docs"),
    ("file.docs_product_voice_007_provider_readiness", "docs/product/VOICE_007_PROVIDER_READINESS_GATE.md", "Voice provider readiness gate"),
    ("file.docs_product_voice_012_speech_naturalness", "docs/product/VOICE_012_SPEECH_NATURALNESS_LAYER.md", "Voice speech naturalness layer"),
    ("file.docs_product_voice_013_elevenlabs_tts", "docs/product/VOICE_013_ELEVENLABS_TTS_SMOKE_TEST.md", "ElevenLabs TTS smoke test"),
    ("file.docs_product_voice_014_provider_listening", "docs/product/VOICE_014_PROVIDER_LISTENING_COMPARISON.md", "Voice provider listening comparison"),
    ("file.docs_product_voice_015_prosody_naturalness", "docs/product/VOICE_015_PROSODY_NATURALNESS_LAYER.md", "Voice prosody naturalness layer"),
    ("file.docs_product_voice_016_provider_prosody", "docs/product/VOICE_016_PROVIDER_PROSODY_RENDERING.md", "Voice provider prosody rendering"),
    ("file.docs_product_voice_017_live_ab_audio", "docs/product/VOICE_017_LIVE_AB_AUDIO.md", "Voice live A/B audio harness"),
    ("file.docs_product_voice_018_sales_voice_tuning", "docs/product/VOICE_018_SALES_VOICE_TUNING.md", "Voice sales tuning"),
    ("file.docs_product_voice_019_sales_tuned_live_ab_audio", "docs/product/VOICE_019_SALES_TUNED_LIVE_AB_AUDIO.md", "Voice sales tuned live A/B audio"),
    ("file.docs_product_voice_020_elevenlabs_voice_design", "docs/product/VOICE_020_ELEVENLABS_VOICE_DESIGN.md", "ElevenLabs voice design"),
    ("file.docs_product_voice_021_custom_voice_comparison", "docs/product/VOICE_021_ELEVENLABS_CUSTOM_VOICE_COMPARISON.md", "ElevenLabs custom voice comparison"),
    ("file.docs_product_voice_022_spoken_text_normalization", "docs/product/VOICE_022_SPOKEN_TEXT_NORMALIZATION.md", "Voice spoken text normalization"),
    ("file.docs_product_voice_023_speech_realism", "docs/product/VOICE_023_SPEECH_REALISM_LAYER.md", "Voice speech realism layer"),
    ("file.docs_product_voice_024_speech_realism_live_ab", "docs/product/VOICE_024_SPEECH_REALISM_LIVE_AB.md", "Voice speech realism live A/B harness"),
    ("file.docs_product_voice_025_filler_placement", "docs/product/VOICE_025_FILLER_PLACEMENT.md", "Voice filler placement"),
    ("file.docs_product_voice_026_interaction_prosody", "docs/product/VOICE_026_INTERACTION_PROSODY.md", "Voice interaction prosody layer"),
    ("file.docs_product_voice_027_interaction_prosody_live_ab", "docs/product/VOICE_027_INTERACTION_PROSODY_LIVE_AB.md", "Voice interaction prosody live A/B harness"),
    ("file.docs_product_voice_028_controlled_imperfections", "docs/product/VOICE_028_CONTROLLED_IMPERFECTIONS.md", "Voice controlled delivery imperfections"),
    ("file.docs_product_voice_029_local_speech_profile", "docs/product/VOICE_029_LOCAL_SPEECH_PROFILE_LEARNING.md", "Voice local speech profile learning"),
    ("file.docs_product_voice_030a_raw_audio_reader", "docs/product/VOICE_030A_RAW_AUDIO_LOCAL_READER.md", "Voice raw audio local reader"),
    ("file.docs_product_voice_030b_local_speech_capture", "docs/product/VOICE_030B_LOCAL_SPEECH_CAPTURE.md", "Voice local speech capture"),
    ("file.docs_product_voice_030c_private_learning_queue", "docs/product/VOICE_030C_PRIVATE_LEARNING_QUEUE.md", "Voice private learning queue"),
    ("file.docs_product_voice_030d_private_feature_review", "docs/product/VOICE_030D_PRIVATE_FEATURE_REVIEW.md", "Voice private feature review"),
    ("file.docs_product_voice_031_feature_runtime_mapping", "docs/product/VOICE_031_FEATURE_RUNTIME_MAPPING.md", "Voice feature-to-runtime mapping gate"),
    ("file.docs_product_voice_032_local_audio_conversion", "docs/product/VOICE_032_LOCAL_AUDIO_CONVERSION.md", "Voice local audio conversion gate"),
    ("file.docs_product_voice_033_private_sample_readiness", "docs/product/VOICE_033_PRIVATE_SAMPLE_READINESS.md", "Voice private sample readiness report"),
    ("file.docs_product_voice_034_pacing_calibration", "docs/product/VOICE_034_PACING_CALIBRATION_V2.md", "Voice pacing calibration V2"),
    ("file.docs_product_voice_035_connected_speech", "docs/product/VOICE_035_CONNECTED_SPEECH_PHRASE_FLOW.md", "Voice connected speech phrase flow"),
    ("file.docs_product_voice_036_listening_calibration", "docs/product/VOICE_036_LISTENING_CALIBRATION.md", "Voice listening feedback calibration"),
    ("file.docs_product_voice_037_emotion_smoothing", "docs/product/VOICE_037_EMOTION_TRANSITION_SMOOTHING.md", "Voice emotion transition smoothing"),
    ("file.docs_product_voice_038_semantic_emphasis", "docs/product/VOICE_038_SEMANTIC_EMPHASIS_DIAGNOSIS.md", "Voice semantic emphasis diagnosis"),
    ("file.docs_product_voice_039_runtime_semantic_emphasis", "docs/product/VOICE_039_RUNTIME_SEMANTIC_EMPHASIS.md", "Voice runtime semantic emphasis"),
    ("file.docs_product_voice_040_low_pressure_focus", "docs/product/VOICE_040_LOW_PRESSURE_FOCUS.md", "Voice low-pressure focus"),
    ("file.docs_product_resp_002_runtime_voice_delivery", "docs/product/RESP_002_RUNTIME_VOICE_DELIVERY.md", "Runtime voice delivery"),
    ("file.docs_product_resp_003_runtime_live_tts", "docs/product/RESP_003_RUNTIME_LIVE_TTS.md", "Runtime live TTS delivery"),
    ("file.docs_data_data_usage_policy", "docs/data/DATA_USAGE_POLICY.md", "Data usage policy"),
    ("file.docs_data_private_call_center_policy", "docs/data/PRIVATE_CALL_CENTER_DATA_POLICY.md", "Private call-center data policy"),
    ("file.docs_data_private_call_learning_pipeline", "docs/data/PRIVATE_CALL_LEARNING_PIPELINE.md", "Private call learning pipeline"),
    ("file.data_private_gitignore", "data/private/.gitignore", "Private data local ignore rule"),
    ("file.config_local_gitignore", "config/local/.gitignore", "Local config ignore rule"),
    ("file.config_local_voice_ids_example", "config/local/voice_ids.example.json", "Local voice ID config example"),
    ("file.scripts_realtime_turn_cli", "scripts/realtime_turn_cli.py", "Realtime turn CLI"),
    ("file.scripts_start_guarded_local_server", "scripts/start_guarded_local_server.py", "Guarded local server launcher"),
    ("file.scripts_product_agent_output_contract", "scripts/product_agent_output_contract.py", "Product output contract"),
    ("file.scripts_validate_product_agent_output_contract", "scripts/validate_product_agent_output_contract.py", "Output contract validator"),
    ("file.scripts_validate_self_contained_project_policy", "scripts/validate_self_contained_project_policy.py", "Self-contained project policy validator"),
    ("file.scripts_check_project_drift", "scripts/check_project_drift.py", "Project drift guard"),
    ("file.scripts_validate_project_drift_guard", "scripts/validate_project_drift_guard.py", "Project drift guard validator"),
    ("file.scripts_check_thesis_reference_registry", "scripts/check_thesis_reference_registry.py", "Thesis reference registry guard"),
    ("file.scripts_validate_thesis_reference_registry", "scripts/validate_thesis_reference_registry.py", "Thesis reference registry guard validator"),
    ("file.scripts_check_thesis_update_gate", "scripts/check_thesis_update_gate.py", "Thesis update gate"),
    ("file.scripts_validate_thesis_update_gate", "scripts/validate_thesis_update_gate.py", "Thesis update gate validator"),
    ("file.scripts_validate_private_data_boundary", "scripts/validate_private_data_boundary.py", "Private data boundary validator"),
    ("file.scripts_check_private_call_learning_pipeline", "scripts/check_private_call_learning_pipeline.py", "Private call learning pipeline checker"),
    ("file.scripts_init_private_call_learning_workspace", "scripts/init_private_call_learning_workspace.py", "Private call learning local workspace initializer"),
    ("file.scripts_validate_private_call_learning_pipeline", "scripts/validate_private_call_learning_pipeline.py", "Private call learning pipeline validator"),
    ("file.scripts_rag_knowledge_base", "scripts/rag_knowledge_base.py", "RAG knowledge base intake module"),
    ("file.scripts_rag_notebooklm_automation", "scripts/rag_notebooklm_automation.py", "RAG NotebookLM automation module"),
    ("file.scripts_rag_report_import_readiness", "scripts/rag_report_import_readiness.py", "RAG NotebookLM report import readiness module"),
    ("file.scripts_rag_source_manifest_normalization", "scripts/rag_source_manifest_normalization.py", "RAG source manifest normalization module"),
    ("file.scripts_rag_chunk_normalization", "scripts/rag_chunk_normalization.py", "RAG chunk normalization module"),
    ("file.scripts_rag_chunk_review_packet", "scripts/rag_chunk_review_packet.py", "RAG chunk review packet module"),
    ("file.scripts_rag_reviewed_first_slice", "scripts/rag_reviewed_first_slice.py", "RAG reviewed first slice module"),
    ("file.scripts_rag_guarded_retrieval_policy", "scripts/rag_guarded_retrieval_policy.py", "RAG guarded retrieval policy module"),
    ("file.scripts_rag_all_source_review_coverage", "scripts/rag_all_source_review_coverage.py", "RAG all-source review coverage module"),
    ("file.scripts_rag_reviewed_expansion_slice", "scripts/rag_reviewed_expansion_slice.py", "RAG reviewed expansion slice module"),
    ("file.scripts_rag_blocker_cleanup_packet", "scripts/rag_blocker_cleanup_packet.py", "RAG blocker cleanup packet module"),
    ("file.scripts_rag_accepted_cleanup", "scripts/rag_accepted_cleanup.py", "RAG accepted cleanup module"),
    ("file.scripts_rag_cleanup_strategy", "scripts/rag_cleanup_strategy.py", "RAG cleanup strategy module"),
    ("file.scripts_rag_source_mapped_quote_followup", "scripts/rag_source_mapped_quote_followup.py", "RAG source-mapped quote follow-up module"),
    ("file.scripts_rag_source_mapping_batches", "scripts/rag_source_mapping_batches.py", "RAG source-mapping batches module"),
    ("file.scripts_rag_quote_clearance_batches", "scripts/rag_quote_clearance_batches.py", "RAG quote-clearance batches module"),
    ("file.scripts_rag_quote_clearance_decision_slice", "scripts/rag_quote_clearance_decision_slice.py", "RAG quote-clearance decision slice module"),
    ("file.scripts_rag_voice_delivery_quote_clearance_decision_slice", "scripts/rag_voice_delivery_quote_clearance_decision_slice.py", "RAG voice-delivery decision slice module"),
    ("file.scripts_rag_runtime_knowledge_registry", "scripts/rag_runtime_knowledge_registry.py", "RAG runtime knowledge registry module"),
    ("file.scripts_rag_sales_communication_source_expansion", "scripts/rag_sales_communication_source_expansion.py", "RAG sales communication source expansion module"),
    ("file.scripts_run_rag_001_notebooklm_source_intake", "scripts/run_rag_001_notebooklm_source_intake.py", "RAG NotebookLM source intake runner"),
    ("file.scripts_validate_rag_001_notebooklm_source_intake", "scripts/validate_rag_001_notebooklm_source_intake.py", "RAG NotebookLM source intake validator"),
    ("file.scripts_run_rag_002_notebooklm_extraction_automation", "scripts/run_rag_002_notebooklm_extraction_automation.py", "RAG NotebookLM extraction automation runner"),
    ("file.scripts_validate_rag_002_notebooklm_extraction_automation", "scripts/validate_rag_002_notebooklm_extraction_automation.py", "RAG NotebookLM extraction automation validator"),
    ("file.scripts_run_rag_003_report_import_readiness", "scripts/run_rag_003_report_import_readiness.py", "RAG NotebookLM report import readiness runner"),
    ("file.scripts_validate_rag_003_report_import_readiness", "scripts/validate_rag_003_report_import_readiness.py", "RAG NotebookLM report import readiness validator"),
    ("file.scripts_run_rag_004_source_manifest_normalization", "scripts/run_rag_004_source_manifest_normalization.py", "RAG source manifest normalization runner"),
    ("file.scripts_validate_rag_004_source_manifest_normalization", "scripts/validate_rag_004_source_manifest_normalization.py", "RAG source manifest normalization validator"),
    ("file.scripts_run_rag_005_chunk_normalization", "scripts/run_rag_005_chunk_normalization.py", "RAG chunk normalization runner"),
    ("file.scripts_validate_rag_005_chunk_normalization", "scripts/validate_rag_005_chunk_normalization.py", "RAG chunk normalization validator"),
    ("file.scripts_run_rag_006_chunk_review_packet", "scripts/run_rag_006_chunk_review_packet.py", "RAG chunk review packet runner"),
    ("file.scripts_validate_rag_006_chunk_review_packet", "scripts/validate_rag_006_chunk_review_packet.py", "RAG chunk review packet validator"),
    ("file.scripts_run_rag_007_reviewed_first_slice", "scripts/run_rag_007_reviewed_first_slice.py", "RAG reviewed first slice runner"),
    ("file.scripts_validate_rag_007_reviewed_first_slice", "scripts/validate_rag_007_reviewed_first_slice.py", "RAG reviewed first slice validator"),
    ("file.scripts_run_rag_008_guarded_retrieval_policy", "scripts/run_rag_008_guarded_retrieval_policy.py", "RAG guarded retrieval policy runner"),
    ("file.scripts_validate_rag_008_guarded_retrieval_policy", "scripts/validate_rag_008_guarded_retrieval_policy.py", "RAG guarded retrieval policy validator"),
    ("file.scripts_run_rag_009_all_source_review_coverage", "scripts/run_rag_009_all_source_review_coverage.py", "RAG all-source review coverage runner"),
    ("file.scripts_validate_rag_009_all_source_review_coverage", "scripts/validate_rag_009_all_source_review_coverage.py", "RAG all-source review coverage validator"),
    ("file.scripts_run_rag_010_reviewed_expansion_slice", "scripts/run_rag_010_reviewed_expansion_slice.py", "RAG reviewed expansion slice runner"),
    ("file.scripts_validate_rag_010_reviewed_expansion_slice", "scripts/validate_rag_010_reviewed_expansion_slice.py", "RAG reviewed expansion slice validator"),
    ("file.scripts_run_rag_011_blocker_cleanup_packet", "scripts/run_rag_011_blocker_cleanup_packet.py", "RAG blocker cleanup packet runner"),
    ("file.scripts_validate_rag_011_blocker_cleanup_packet", "scripts/validate_rag_011_blocker_cleanup_packet.py", "RAG blocker cleanup packet validator"),
    ("file.scripts_run_rag_012_accepted_cleanup", "scripts/run_rag_012_accepted_cleanup.py", "RAG accepted cleanup runner"),
    ("file.scripts_validate_rag_012_accepted_cleanup", "scripts/validate_rag_012_accepted_cleanup.py", "RAG accepted cleanup validator"),
    ("file.scripts_run_rag_013_cleanup_strategy", "scripts/run_rag_013_cleanup_strategy.py", "RAG cleanup strategy runner"),
    ("file.scripts_validate_rag_013_cleanup_strategy", "scripts/validate_rag_013_cleanup_strategy.py", "RAG cleanup strategy validator"),
    ("file.scripts_run_rag_014_source_mapped_quote_followup", "scripts/run_rag_014_source_mapped_quote_followup.py", "RAG source-mapped quote follow-up runner"),
    ("file.scripts_validate_rag_014_source_mapped_quote_followup", "scripts/validate_rag_014_source_mapped_quote_followup.py", "RAG source-mapped quote follow-up validator"),
    ("file.scripts_run_rag_015_source_mapping_batches", "scripts/run_rag_015_source_mapping_batches.py", "RAG source-mapping batches runner"),
    ("file.scripts_validate_rag_015_source_mapping_batches", "scripts/validate_rag_015_source_mapping_batches.py", "RAG source-mapping batches validator"),
    ("file.scripts_run_rag_016_quote_clearance_batches", "scripts/run_rag_016_quote_clearance_batches.py", "RAG quote-clearance batches runner"),
    ("file.scripts_validate_rag_016_quote_clearance_batches", "scripts/validate_rag_016_quote_clearance_batches.py", "RAG quote-clearance batches validator"),
    ("file.scripts_run_rag_016a_quote_clearance_decision_slice", "scripts/run_rag_016a_quote_clearance_decision_slice.py", "RAG quote-clearance decision slice runner"),
    ("file.scripts_validate_rag_016a_quote_clearance_decision_slice", "scripts/validate_rag_016a_quote_clearance_decision_slice.py", "RAG quote-clearance decision slice validator"),
    ("file.scripts_run_rag_016b_voice_delivery_decision_slice", "scripts/run_rag_016b_voice_delivery_decision_slice.py", "RAG voice-delivery decision slice runner"),
    ("file.scripts_validate_rag_016b_voice_delivery_decision_slice", "scripts/validate_rag_016b_voice_delivery_decision_slice.py", "RAG voice-delivery decision slice validator"),
    ("file.scripts_run_rag_017_runtime_knowledge_registry", "scripts/run_rag_017_runtime_knowledge_registry.py", "RAG runtime knowledge registry runner"),
    ("file.scripts_validate_rag_017_runtime_knowledge_registry", "scripts/validate_rag_017_runtime_knowledge_registry.py", "RAG runtime knowledge registry validator"),
    ("file.scripts_validate_rag_018_guarded_runtime_retrieval", "scripts/validate_rag_018_guarded_runtime_retrieval.py", "RAG guarded runtime retrieval validator"),
    ("file.scripts_run_rag_019_sales_communication_source_expansion", "scripts/run_rag_019_sales_communication_source_expansion.py", "RAG sales communication source expansion runner"),
    ("file.scripts_validate_rag_019_sales_communication_source_expansion", "scripts/validate_rag_019_sales_communication_source_expansion.py", "RAG sales communication source expansion validator"),
    ("file.scripts_local_voice_config", "scripts/local_voice_config.py", "Local voice ID config helper"),
    ("file.scripts_validate_local_voice_config", "scripts/validate_local_voice_config.py", "Local voice ID config validator"),
    ("file.scripts_evaluate_voice_provider_readiness", "scripts/evaluate_voice_provider_readiness.py", "Voice provider readiness evaluator"),
    ("file.scripts_speech_naturalness", "scripts/speech_naturalness.py", "Speech naturalness renderer"),
    ("file.scripts_validate_voice_012_speech_naturalness", "scripts/validate_voice_012_speech_naturalness.py", "Speech naturalness validator"),
    ("file.scripts_run_voice_013_elevenlabs_tts_smoke", "scripts/run_voice_013_elevenlabs_tts_smoke.py", "ElevenLabs TTS smoke runner"),
    ("file.scripts_validate_voice_013_elevenlabs_tts_smoke", "scripts/validate_voice_013_elevenlabs_tts_smoke.py", "ElevenLabs TTS smoke validator"),
    ("file.scripts_run_voice_014_provider_listening_comparison", "scripts/run_voice_014_provider_listening_comparison.py", "Provider listening comparison runner"),
    ("file.scripts_validate_voice_014_provider_listening_comparison", "scripts/validate_voice_014_provider_listening_comparison.py", "Provider listening comparison validator"),
    ("file.scripts_prosody_naturalness", "scripts/prosody_naturalness.py", "Prosody naturalness planner"),
    ("file.scripts_run_voice_015_prosody_naturalness", "scripts/run_voice_015_prosody_naturalness.py", "Prosody naturalness runner"),
    ("file.scripts_validate_voice_015_prosody_naturalness", "scripts/validate_voice_015_prosody_naturalness.py", "Prosody naturalness validator"),
    ("file.scripts_provider_prosody_rendering", "scripts/provider_prosody_rendering.py", "Provider prosody renderer"),
    ("file.scripts_run_voice_016_provider_prosody", "scripts/run_voice_016_provider_prosody_rendering.py", "Provider prosody rendering runner"),
    ("file.scripts_validate_voice_016_provider_prosody", "scripts/validate_voice_016_provider_prosody_rendering.py", "Provider prosody rendering validator"),
    ("file.scripts_run_voice_017_live_ab_audio", "scripts/run_voice_017_live_ab_audio.py", "Live A/B audio runner"),
    ("file.scripts_validate_voice_017_live_ab_audio", "scripts/validate_voice_017_live_ab_audio.py", "Live A/B audio validator"),
    ("file.scripts_sales_voice_tuning", "scripts/sales_voice_tuning.py", "Sales voice tuning module"),
    ("file.scripts_run_voice_018_sales_voice_tuning", "scripts/run_voice_018_sales_voice_tuning.py", "Sales voice tuning runner"),
    ("file.scripts_validate_voice_018_sales_voice_tuning", "scripts/validate_voice_018_sales_voice_tuning.py", "Sales voice tuning validator"),
    ("file.scripts_run_voice_019_sales_tuned_live_ab_audio", "scripts/run_voice_019_sales_tuned_live_ab_audio.py", "Sales tuned live A/B audio runner"),
    ("file.scripts_validate_voice_019_sales_tuned_live_ab_audio", "scripts/validate_voice_019_sales_tuned_live_ab_audio.py", "Sales tuned live A/B audio validator"),
    ("file.scripts_run_voice_020_elevenlabs_voice_design", "scripts/run_voice_020_elevenlabs_voice_design.py", "ElevenLabs voice design runner"),
    ("file.scripts_validate_voice_020_elevenlabs_voice_design", "scripts/validate_voice_020_elevenlabs_voice_design.py", "ElevenLabs voice design validator"),
    ("file.scripts_run_voice_021_custom_voice_comparison", "scripts/run_voice_021_custom_voice_comparison.py", "ElevenLabs custom voice comparison runner"),
    ("file.scripts_validate_voice_021_custom_voice_comparison", "scripts/validate_voice_021_custom_voice_comparison.py", "ElevenLabs custom voice comparison validator"),
    ("file.scripts_spoken_text_normalization", "scripts/spoken_text_normalization.py", "Spoken text normalization module"),
    ("file.scripts_run_voice_022_spoken_text_normalization", "scripts/run_voice_022_spoken_text_normalization.py", "Spoken text normalization runner"),
    ("file.scripts_validate_voice_022_spoken_text_normalization", "scripts/validate_voice_022_spoken_text_normalization.py", "Spoken text normalization validator"),
    ("file.scripts_speech_realism", "scripts/speech_realism.py", "Speech realism module"),
    ("file.scripts_run_voice_023_speech_realism", "scripts/run_voice_023_speech_realism.py", "Speech realism runner"),
    ("file.scripts_validate_voice_023_speech_realism", "scripts/validate_voice_023_speech_realism.py", "Speech realism validator"),
    ("file.scripts_run_voice_024_speech_realism_live_ab", "scripts/run_voice_024_speech_realism_live_ab.py", "Speech realism live A/B runner"),
    ("file.scripts_validate_voice_024_speech_realism_live_ab", "scripts/validate_voice_024_speech_realism_live_ab.py", "Speech realism live A/B validator"),
    ("file.scripts_run_voice_025_filler_placement", "scripts/run_voice_025_filler_placement.py", "Filler placement runner"),
    ("file.scripts_validate_voice_025_filler_placement", "scripts/validate_voice_025_filler_placement.py", "Filler placement validator"),
    ("file.scripts_speech_interaction", "scripts/speech_interaction.py", "Speech interaction prosody module"),
    ("file.scripts_run_voice_026_interaction_prosody", "scripts/run_voice_026_interaction_prosody.py", "Interaction prosody runner"),
    ("file.scripts_validate_voice_026_interaction_prosody", "scripts/validate_voice_026_interaction_prosody.py", "Interaction prosody validator"),
    ("file.scripts_run_voice_027_interaction_prosody_live_ab", "scripts/run_voice_027_interaction_prosody_live_ab.py", "Interaction prosody live A/B runner"),
    ("file.scripts_validate_voice_027_interaction_prosody_live_ab", "scripts/validate_voice_027_interaction_prosody_live_ab.py", "Interaction prosody live A/B validator"),
    ("file.scripts_speech_imperfections", "scripts/speech_imperfections.py", "Controlled delivery imperfections module"),
    ("file.scripts_run_voice_028_controlled_imperfections", "scripts/run_voice_028_controlled_imperfections.py", "Controlled imperfections runner"),
    ("file.scripts_validate_voice_028_controlled_imperfections", "scripts/validate_voice_028_controlled_imperfections.py", "Controlled imperfections validator"),
    ("file.scripts_personal_speech_profile", "scripts/personal_speech_profile.py", "Personal speech profile module"),
    ("file.scripts_run_voice_029_local_speech_profile", "scripts/run_voice_029_local_speech_profile.py", "Local speech profile runner"),
    ("file.scripts_validate_voice_029_local_speech_profile", "scripts/validate_voice_029_local_speech_profile.py", "Local speech profile validator"),
    ("file.scripts_init_personal_speech_learning_workspace", "scripts/init_personal_speech_learning_workspace.py", "Personal speech learning workspace initializer"),
    ("file.scripts_raw_audio_speech_features", "scripts/raw_audio_speech_features.py", "Raw audio speech feature module"),
    ("file.scripts_run_voice_030_raw_audio_reader", "scripts/run_voice_030_raw_audio_reader.py", "Raw audio reader runner"),
    ("file.scripts_validate_voice_030_raw_audio_reader", "scripts/validate_voice_030_raw_audio_reader.py", "Raw audio reader validator"),
    ("file.scripts_private_speech_learning_queue", "scripts/private_speech_learning_queue.py", "Private speech learning queue module"),
    ("file.scripts_run_voice_030b_local_speech_capture", "scripts/run_voice_030b_local_speech_capture.py", "Local speech capture runner"),
    ("file.scripts_validate_voice_030b_local_speech_capture", "scripts/validate_voice_030b_local_speech_capture.py", "Local speech capture validator"),
    ("file.scripts_validate_voice_030c_private_learning_queue", "scripts/validate_voice_030c_private_learning_queue.py", "Private learning queue validator"),
    ("file.scripts_run_voice_030d_private_feature_review", "scripts/run_voice_030d_private_feature_review.py", "Private feature review runner"),
    ("file.scripts_validate_voice_030d_private_feature_review", "scripts/validate_voice_030d_private_feature_review.py", "Private feature review validator"),
    ("file.scripts_voice_feature_runtime_mapping", "scripts/voice_feature_runtime_mapping.py", "Feature-to-runtime mapping module"),
    ("file.scripts_run_voice_031_feature_runtime_mapping", "scripts/run_voice_031_feature_runtime_mapping.py", "Feature-to-runtime mapping runner"),
    ("file.scripts_validate_voice_031_feature_runtime_mapping", "scripts/validate_voice_031_feature_runtime_mapping.py", "Feature-to-runtime mapping validator"),
    ("file.scripts_private_audio_conversion", "scripts/private_audio_conversion.py", "Private audio conversion module"),
    ("file.scripts_run_voice_032_local_audio_conversion", "scripts/run_voice_032_local_audio_conversion.py", "Local audio conversion runner"),
    ("file.scripts_validate_voice_032_local_audio_conversion", "scripts/validate_voice_032_local_audio_conversion.py", "Local audio conversion validator"),
    ("file.scripts_private_sample_readiness", "scripts/private_sample_readiness.py", "Private sample readiness module"),
    ("file.scripts_run_voice_033_private_sample_readiness", "scripts/run_voice_033_private_sample_readiness.py", "Private sample readiness runner"),
    ("file.scripts_validate_voice_033_private_sample_readiness", "scripts/validate_voice_033_private_sample_readiness.py", "Private sample readiness validator"),
    ("file.scripts_voice_pacing_calibration", "scripts/voice_pacing_calibration.py", "Voice pacing calibration module"),
    ("file.scripts_run_voice_034_pacing_calibration", "scripts/run_voice_034_pacing_calibration.py", "Voice pacing calibration runner"),
    ("file.scripts_validate_voice_034_pacing_calibration", "scripts/validate_voice_034_pacing_calibration.py", "Voice pacing calibration validator"),
    ("file.scripts_voice_connected_speech", "scripts/voice_connected_speech.py", "Voice connected speech module"),
    ("file.scripts_run_voice_035_connected_speech", "scripts/run_voice_035_connected_speech.py", "Voice connected speech runner"),
    ("file.scripts_validate_voice_035_connected_speech", "scripts/validate_voice_035_connected_speech.py", "Voice connected speech validator"),
    ("file.scripts_voice_listening_calibration", "scripts/voice_listening_calibration.py", "Voice listening feedback calibration module"),
    ("file.scripts_run_voice_036_listening_calibration", "scripts/run_voice_036_listening_calibration.py", "Voice listening feedback calibration runner"),
    ("file.scripts_validate_voice_036_listening_calibration", "scripts/validate_voice_036_listening_calibration.py", "Voice listening feedback calibration validator"),
    ("file.scripts_voice_emotion_smoothing", "scripts/voice_emotion_smoothing.py", "Voice emotion transition smoothing module"),
    ("file.scripts_run_voice_037_emotion_smoothing", "scripts/run_voice_037_emotion_smoothing.py", "Voice emotion transition smoothing runner"),
    ("file.scripts_validate_voice_037_emotion_smoothing", "scripts/validate_voice_037_emotion_smoothing.py", "Voice emotion transition smoothing validator"),
    ("file.scripts_run_voice_038_semantic_emphasis", "scripts/run_voice_038_semantic_emphasis_diagnosis.py", "Voice semantic emphasis diagnosis runner"),
    ("file.scripts_validate_voice_038_semantic_emphasis", "scripts/validate_voice_038_semantic_emphasis_diagnosis.py", "Voice semantic emphasis diagnosis validator"),
    ("file.scripts_voice_semantic_emphasis", "scripts/voice_semantic_emphasis.py", "Voice semantic emphasis module"),
    ("file.scripts_run_voice_039_runtime_semantic_emphasis", "scripts/run_voice_039_runtime_semantic_emphasis.py", "Voice runtime semantic emphasis runner"),
    ("file.scripts_validate_voice_039_runtime_semantic_emphasis", "scripts/validate_voice_039_runtime_semantic_emphasis.py", "Voice runtime semantic emphasis validator"),
    ("file.scripts_voice_low_pressure_focus", "scripts/voice_low_pressure_focus.py", "Voice low-pressure focus module"),
    ("file.scripts_run_voice_040_low_pressure_focus", "scripts/run_voice_040_low_pressure_focus.py", "Voice low-pressure focus runner"),
    ("file.scripts_validate_voice_040_low_pressure_focus", "scripts/validate_voice_040_low_pressure_focus.py", "Voice low-pressure focus validator"),
    ("file.scripts_runtime_voice_delivery", "scripts/runtime_voice_delivery.py", "Runtime voice delivery module"),
    ("file.scripts_generate_runtime_voice_delivery", "scripts/generate_runtime_voice_delivery.py", "Runtime voice delivery runner"),
    ("file.scripts_validate_resp_002_runtime_voice_delivery", "scripts/validate_resp_002_runtime_voice_delivery.py", "Runtime voice delivery validator"),
    ("file.scripts_tts_provider_clients", "scripts/tts_provider_clients.py", "Project-local TTS provider clients"),
    ("file.scripts_runtime_tts_delivery", "scripts/runtime_tts_delivery.py", "Runtime live TTS delivery module"),
    ("file.scripts_generate_runtime_tts_delivery", "scripts/generate_runtime_tts_delivery.py", "Runtime live TTS delivery runner"),
    ("file.scripts_validate_resp_003_runtime_live_tts", "scripts/validate_resp_003_runtime_live_tts.py", "Runtime live TTS delivery validator"),
    ("file.scripts_run_resp_003_bilingual_live_tts_ab", "scripts/run_resp_003_bilingual_live_tts_ab.py", "Runtime bilingual live TTS A/B runner"),
    ("file.scripts_validate_resp_003_bilingual_live_tts_ab", "scripts/validate_resp_003_bilingual_live_tts_ab.py", "Runtime bilingual live TTS A/B validator"),
    ("file.scripts_run_product_simulation", "scripts/run_product_simulation.py", "Product simulation runner"),
    ("file.scripts_run_rule_baseline", "scripts/run_rule_baseline.py", "Rule baseline runner"),
    ("file.scripts_read_relevant", "scripts/read_relevant.py", "Product-local relevant reader"),
    ("file.scripts_validate_read_relevant", "scripts/validate_read_relevant.py", "Relevant reader validator"),
    ("file.scripts_validate_context_reading_policy", "scripts/validate_context_reading_policy.py", "Context reading policy validator"),
    ("file.data_rag_readme", "data/rag/README.md", "RAG data workspace README"),
    ("file.research_private_call_learning_001", "research/experiments/PRIVATE-CALL-LEARNING-001.md", "Private call learning experiment note"),
    ("file.research_case_rag_001_notebooklm_source_intake", "research/experiments/cases/rag-001-notebooklm-source-intake-bridge.json", "RAG NotebookLM source intake case file"),
    ("file.research_case_rag_002_notebooklm_extraction_automation", "research/experiments/cases/rag-002-notebooklm-extraction-automation-bridge.json", "RAG NotebookLM extraction automation case file"),
    ("file.research_case_rag_003_report_import_readiness", "research/experiments/cases/rag-003-report-import-readiness.json", "RAG NotebookLM report import readiness case file"),
    ("file.research_case_rag_004_source_manifest_normalization", "research/experiments/cases/rag-004-source-manifest-normalization.json", "RAG source manifest normalization case file"),
    ("file.research_case_rag_005_chunk_normalization", "research/experiments/cases/rag-005-chunk-normalization.json", "RAG chunk normalization case file"),
    ("file.research_case_rag_006_chunk_review_packet", "research/experiments/cases/rag-006-chunk-review-packet.json", "RAG chunk review packet case file"),
    ("file.research_case_rag_007_reviewed_first_slice", "research/experiments/cases/rag-007-reviewed-first-slice.json", "RAG reviewed first slice case file"),
    ("file.research_case_rag_008_guarded_retrieval_policy", "research/experiments/cases/rag-008-guarded-retrieval-policy.json", "RAG guarded retrieval policy case file"),
    ("file.research_case_rag_009_all_source_review_coverage", "research/experiments/cases/rag-009-all-source-review-coverage.json", "RAG all-source review coverage case file"),
    ("file.research_case_rag_010_reviewed_expansion_slice", "research/experiments/cases/rag-010-reviewed-expansion-slice.json", "RAG reviewed expansion slice case file"),
    ("file.research_case_rag_011_blocker_cleanup_packet", "research/experiments/cases/rag-011-blocker-cleanup-packet.json", "RAG blocker cleanup packet case file"),
    ("file.research_case_rag_012_accepted_cleanup", "research/experiments/cases/rag-012-accepted-cleanup.json", "RAG accepted cleanup case file"),
    ("file.research_case_rag_013_cleanup_strategy", "research/experiments/cases/rag-013-cleanup-strategy.json", "RAG cleanup strategy case file"),
    ("file.research_case_rag_014_source_mapped_quote_followup", "research/experiments/cases/rag-014-source-mapped-quote-followup.json", "RAG source-mapped quote follow-up case file"),
    ("file.research_case_rag_015_source_mapping_batches", "research/experiments/cases/rag-015-source-mapping-batches.json", "RAG source-mapping batches case file"),
    ("file.research_case_rag_016_quote_clearance_batches", "research/experiments/cases/rag-016-quote-clearance-batches.json", "RAG quote-clearance batches case file"),
    ("file.research_case_rag_016a_quote_clearance_decision_slice", "research/experiments/cases/rag-016a-quote-clearance-decision-slice.json", "RAG quote-clearance decision slice case file"),
    ("file.research_case_rag_016b_voice_delivery_decision_slice", "research/experiments/cases/rag-016b-voice-delivery-decision-slice.json", "RAG voice-delivery decision slice case file"),
    ("file.research_case_rag_019_sales_communication_source_expansion", "research/experiments/cases/rag-019-sales-communication-source-expansion.json", "RAG sales communication source expansion case file"),
    ("file.research_case_private_call_learning_001", "research/experiments/cases/private-call-learning-001.json", "Private call learning pipeline case"),
    ("file.research_case_voice_023_speech_realism", "research/experiments/cases/voice-023-speech-realism.json", "VOICE-023 speech realism case file"),
    ("file.research_case_voice_024_speech_realism_live_ab", "research/experiments/cases/voice-024-speech-realism-live-ab.json", "VOICE-024 speech realism live A/B case file"),
    ("file.research_case_voice_025_filler_placement", "research/experiments/cases/voice-025-filler-placement.json", "VOICE-025 filler placement case file"),
    ("file.research_case_voice_026_interaction_prosody", "research/experiments/cases/voice-026-interaction-prosody.json", "VOICE-026 interaction prosody case file"),
    ("file.research_case_voice_027_interaction_prosody_live_ab", "research/experiments/cases/voice-027-interaction-prosody-live-ab.json", "VOICE-027 interaction prosody live A/B case file"),
    ("file.research_case_voice_028_controlled_imperfections", "research/experiments/cases/voice-028-controlled-imperfections.json", "VOICE-028 controlled imperfections case file"),
    ("file.research_case_voice_029_local_speech_profile", "research/experiments/cases/voice-029-local-speech-profile-learning.json", "VOICE-029 local speech profile case file"),
    ("file.research_case_voice_030_raw_audio_reader", "research/experiments/cases/voice-030-raw-audio-local-reader.json", "VOICE-030A raw audio reader case file"),
    ("file.research_case_voice_030b_local_speech_capture", "research/experiments/cases/voice-030b-local-speech-capture.json", "VOICE-030B local speech capture case file"),
    ("file.research_case_voice_030c_private_learning_queue", "research/experiments/cases/voice-030c-private-learning-queue.json", "VOICE-030C private learning queue case file"),
    ("file.research_case_voice_030d_private_feature_review", "research/experiments/cases/voice-030d-private-feature-review.json", "VOICE-030D private feature review case file"),
    ("file.research_case_voice_031_feature_runtime_mapping", "research/experiments/cases/voice-031-feature-runtime-mapping.json", "VOICE-031 feature-to-runtime mapping case file"),
    ("file.research_case_voice_032_local_audio_conversion", "research/experiments/cases/voice-032-local-audio-conversion.json", "VOICE-032 local audio conversion case file"),
    ("file.research_case_voice_033_private_sample_readiness", "research/experiments/cases/voice-033-private-sample-readiness.json", "VOICE-033 private sample readiness case file"),
    ("file.research_case_voice_034_pacing_calibration", "research/experiments/cases/voice-034-pacing-calibration-v2.json", "VOICE-034 pacing calibration case file"),
    ("file.research_case_voice_035_connected_speech", "research/experiments/cases/voice-035-connected-speech-phrase-flow.json", "VOICE-035 connected speech case file"),
    ("file.research_case_voice_036_listening_calibration", "research/experiments/cases/voice-036-listening-calibration.json", "VOICE-036 listening feedback calibration case file"),
    ("file.research_case_voice_037_emotion_smoothing", "research/experiments/cases/voice-037-emotion-smoothing.json", "VOICE-037 emotion transition smoothing case file"),
    ("file.research_case_voice_038_semantic_emphasis", "research/experiments/cases/voice-038-semantic-emphasis-diagnosis.json", "VOICE-038 semantic emphasis diagnosis case file"),
    ("file.research_case_voice_039_runtime_semantic_emphasis", "research/experiments/cases/voice-039-runtime-semantic-emphasis.json", "VOICE-039 runtime semantic emphasis case file"),
    ("file.research_case_voice_040_low_pressure_focus", "research/experiments/cases/voice-040-low-pressure-focus.json", "VOICE-040 low-pressure focus case file"),
]

OPTIONAL_ENV_VARS = [
    ("OPENAI_API_KEY", "Optional LLM product-agent runs"),
    ("CARTESIA_API_KEY", "Optional live Cartesia TTS smoke tests"),
    ("CARTESIA_VOICE_ID", "Optional live Cartesia TTS smoke tests"),
    ("CARTESIA_VOICE_ID_DE", "Optional live Cartesia German TTS smoke tests"),
    ("CARTESIA_VOICE_ID_EN", "Optional live Cartesia English TTS smoke tests"),
    ("ELEVENLABS_API_KEY", "Optional live ElevenLabs TTS smoke tests"),
    ("ELEVENLABS_VOICE_ID", "Optional live ElevenLabs TTS smoke tests"),
    ("ELEVENLABS_VOICE_ID_DE", "Optional live ElevenLabs German TTS smoke tests"),
    ("ELEVENLABS_VOICE_ID_EN", "Optional live ElevenLabs English TTS smoke tests"),
]


def build_check(check_id: str, status: str, severity: str, message: str, path: str | None = None) -> dict[str, Any]:
    check: dict[str, Any] = {
        "id": check_id,
        "status": status,
        "severity": severity,
        "message": message,
    }
    if path is not None:
        check["path"] = path
    return check


def check_python_version() -> dict[str, Any]:
    current = sys.version_info
    current_text = f"{current.major}.{current.minor}.{current.micro}"
    minimum_text = ".".join(str(part) for part in MIN_PYTHON)
    if (current.major, current.minor) >= MIN_PYTHON:
        return build_check(
            "python.version",
            "pass",
            "required",
            f"Python {current_text} meets minimum {minimum_text}.",
        )
    return build_check(
        "python.version",
        "fail",
        "required",
        f"Python {current_text} is below minimum {minimum_text}.",
    )


def check_directories(root: Path) -> list[dict[str, Any]]:
    checks = []
    for check_id, relative_path, label in REQUIRED_DIRS:
        path = root / relative_path
        if path.is_dir():
            checks.append(build_check(check_id, "pass", "required", f"{label} exists.", relative_path))
        else:
            checks.append(build_check(check_id, "fail", "required", f"{label} is missing.", relative_path))
    for check_id, relative_path, label in OPTIONAL_DIRS:
        path = root / relative_path
        if path.is_dir():
            checks.append(build_check(check_id, "pass", "optional", f"{label} exists.", relative_path))
        else:
            checks.append(
                build_check(
                    check_id,
                    "pass",
                    "optional",
                    f"{label} is absent. Default setup does not require restricted private data.",
                    relative_path,
                )
            )
    return checks


def check_files(root: Path) -> list[dict[str, Any]]:
    checks = []
    for check_id, relative_path, label in REQUIRED_FILES:
        path = root / relative_path
        if path.is_file():
            checks.append(build_check(check_id, "pass", "required", f"{label} exists.", relative_path))
        else:
            checks.append(build_check(check_id, "fail", "required", f"{label} is missing.", relative_path))
    return checks


def check_write_path(root: Path) -> dict[str, Any]:
    relative_path = "research/experiments/generated"
    write_dir = root / relative_path
    if not write_dir.is_dir():
        return build_check(
            "write.research_experiments_generated",
            "fail",
            "required",
            "Generated experiment artifact directory is missing.",
            relative_path,
        )
    if not os.access(write_dir, os.W_OK):
        return build_check(
            "write.research_experiments_generated",
            "fail",
            "required",
            "Generated experiment artifact directory does not appear writable.",
            relative_path,
        )

    return build_check(
        "write.research_experiments_generated",
        "pass",
        "required",
        "Generated experiment artifact directory is present and reports writable. No file was written.",
        relative_path,
    )


def build_environment_report() -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "present": bool(os.environ.get(name)),
            "required_for_default_setup": False,
            "value_logged": False,
            "used_for": description,
        }
        for name, description in OPTIONAL_ENV_VARS
    ]


def summarize_checks(checks: list[dict[str, Any]], strict: bool) -> tuple[str, dict[str, Any]]:
    failures = [check for check in checks if check["status"] == "fail"]
    warnings = [check for check in checks if check["status"] == "warning"]
    status = "fail" if failures or (strict and warnings) else "pass"
    return status, {
        "check_count": len(checks),
        "failures": len(failures),
        "warnings": len(warnings),
        "strict": strict,
        "network_calls_made": False,
        "secret_values_logged": False,
    }


def build_report(root: Path, strict: bool) -> dict[str, Any]:
    checks = [
        build_check(
            "root.exists",
            "pass" if root.is_dir() else "fail",
            "required",
            "Project root exists." if root.is_dir() else "Project root is missing.",
            ".",
        ),
        check_python_version(),
    ]
    checks.extend(check_directories(root))
    checks.extend(check_files(root))
    checks.append(check_write_path(root))

    status, summary = summarize_checks(checks, strict)
    return {
        "project": PROJECT_NAME,
        "root": str(root),
        "status": status,
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "python": platform.python_version(),
        },
        "summary": summary,
        "environment": build_environment_report(),
        "checks": checks,
    }


def print_text_report(report: dict[str, Any]) -> None:
    print(f"{report['project']} setup check")
    print(f"Root: {report['root']}")
    print(f"Status: {report['status']}")
    print(
        "Summary: "
        f"{report['summary']['failures']} failure(s), "
        f"{report['summary']['warnings']} warning(s), "
        f"{report['summary']['check_count']} check(s)"
    )
    print("Network calls made: false")
    print("Secret values logged: false")
    print()
    print("Environment gates:")
    for entry in report["environment"]:
        state = "present" if entry["present"] else "not set"
        print(f"- {entry['name']}: {state}; value logged: false; default required: false")
    print()
    print("Checks:")
    for check in report["checks"]:
        path = f" [{check['path']}]" if "path" in check else ""
        print(f"- {check['status'].upper()} {check['id']}{path}: {check['message']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check local setup for the Emotion Aware AI Sales Agent product repo.")
    parser.add_argument("--root", default=str(ROOT), help="Project root to check. Defaults to this repository root.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.root).resolve()
    report = build_report(root, args.strict)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_text_report(report)

    raise SystemExit(0 if report["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
