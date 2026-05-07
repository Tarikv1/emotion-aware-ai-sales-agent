#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "check_setup.py"

SECRET_VALUES = {
    "OPENAI_API_KEY": "TEST_OPENAI_VALUE_MUST_NOT_APPEAR",
    "CARTESIA_API_KEY": "TEST_CARTESIA_VALUE_MUST_NOT_APPEAR",
    "CARTESIA_VOICE_ID": "voice-id-secret-that-must-not-appear",
}

SECRET_PATTERN = re.compile(
    "|".join(re.escape(value) for value in SECRET_VALUES.values())
)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_setup_check() -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(SECRET_VALUES)
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--json"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )


def main() -> None:
    assert_condition(SCRIPT_PATH.exists(), "Product setup verifier is missing.")

    completed = run_setup_check()
    combined_output = completed.stdout + completed.stderr
    assert_condition(SECRET_PATTERN.search(combined_output) is None, "Setup verifier leaked an environment value.")

    payload = json.loads(completed.stdout)
    assert_condition(payload["project"] == "emotion-aware-ai-sales-agent", "Unexpected project name.")
    assert_condition(payload["status"] == "pass", "Current repo setup should pass required checks.")
    assert_condition(payload["summary"]["network_calls_made"] is False, "Setup verifier must not make network calls.")
    assert_condition(payload["summary"]["secret_values_logged"] is False, "Setup verifier must not log secret values.")

    checks_by_id = {check["id"]: check for check in payload["checks"]}
    for required_check in [
        "python.version",
        "dir.scripts",
        "dir.docs_product",
        "dir.research_experiments_generated",
        "dir.data_private",
        "dir.config_local",
        "file.agents",
        "file.docs_third_party_inspirations",
        "file.docs_thesis_speech_realism_references",
        "file.docs_thesis_reference_registry",
        "file.docs_thesis_writing_guide",
        "file.docs_product_review_gates",
        "file.docs_product_product_brief",
        "file.docs_product_context_reading_policy",
        "file.docs_product_project_drift_guard",
        "file.docs_product_voice_018_sales_voice_tuning",
        "file.docs_product_voice_019_sales_tuned_live_ab_audio",
        "file.docs_product_voice_020_elevenlabs_voice_design",
        "file.docs_product_voice_021_custom_voice_comparison",
        "file.docs_product_voice_022_spoken_text_normalization",
        "file.docs_product_voice_023_speech_realism",
        "file.docs_product_voice_024_speech_realism_live_ab",
        "file.docs_product_voice_025_filler_placement",
        "file.docs_product_voice_026_interaction_prosody",
        "file.docs_product_voice_027_interaction_prosody_live_ab",
        "file.docs_product_voice_028_controlled_imperfections",
        "file.docs_product_voice_029_local_speech_profile",
        "file.docs_product_voice_030a_raw_audio_reader",
        "file.docs_product_voice_030b_local_speech_capture",
        "file.docs_product_voice_030c_private_learning_queue",
        "file.docs_product_voice_030d_private_feature_review",
        "file.docs_product_voice_031_feature_runtime_mapping",
        "file.docs_product_voice_032_local_audio_conversion",
        "file.docs_product_voice_033_private_sample_readiness",
        "file.docs_product_voice_034_pacing_calibration",
        "file.docs_product_voice_035_connected_speech",
        "file.docs_product_voice_036_listening_calibration",
        "file.docs_product_voice_037_emotion_smoothing",
        "file.docs_product_voice_038_semantic_emphasis",
        "file.docs_product_rag_001_notebooklm_source_intake",
        "file.docs_product_rag_002_notebooklm_extraction_automation",
        "file.docs_product_rag_003_report_import_readiness",
        "file.docs_product_rag_004_source_manifest_normalization",
        "file.docs_product_rag_005_chunk_normalization",
        "file.docs_product_rag_006_chunk_review_packet",
        "file.docs_product_rag_007_reviewed_first_slice",
        "file.docs_product_rag_008_guarded_retrieval_policy",
        "file.docs_product_rag_009_all_source_review_coverage",
        "file.docs_product_rag_010_reviewed_expansion_slice",
        "file.docs_product_rag_011_blocker_cleanup_packet",
        "file.docs_product_rag_012_accepted_cleanup",
        "file.docs_data_private_call_center_policy",
        "file.docs_data_private_call_learning_pipeline",
        "file.data_private_gitignore",
        "file.config_local_gitignore",
        "file.config_local_voice_ids_example",
        "file.scripts_check_project_drift",
        "file.scripts_validate_project_drift_guard",
        "file.scripts_check_thesis_reference_registry",
        "file.scripts_validate_thesis_reference_registry",
        "file.scripts_check_thesis_update_gate",
        "file.scripts_validate_thesis_update_gate",
        "file.scripts_validate_private_data_boundary",
        "file.scripts_check_private_call_learning_pipeline",
        "file.scripts_init_private_call_learning_workspace",
        "file.scripts_validate_private_call_learning_pipeline",
        "file.scripts_rag_knowledge_base",
        "file.scripts_rag_notebooklm_automation",
        "file.scripts_rag_report_import_readiness",
        "file.scripts_rag_source_manifest_normalization",
        "file.scripts_rag_chunk_normalization",
        "file.scripts_rag_chunk_review_packet",
        "file.scripts_rag_reviewed_first_slice",
        "file.scripts_rag_guarded_retrieval_policy",
        "file.scripts_rag_all_source_review_coverage",
        "file.scripts_rag_reviewed_expansion_slice",
        "file.scripts_rag_blocker_cleanup_packet",
        "file.scripts_rag_accepted_cleanup",
        "file.scripts_run_rag_001_notebooklm_source_intake",
        "file.scripts_validate_rag_001_notebooklm_source_intake",
        "file.scripts_run_rag_002_notebooklm_extraction_automation",
        "file.scripts_validate_rag_002_notebooklm_extraction_automation",
        "file.scripts_run_rag_003_report_import_readiness",
        "file.scripts_validate_rag_003_report_import_readiness",
        "file.scripts_run_rag_004_source_manifest_normalization",
        "file.scripts_validate_rag_004_source_manifest_normalization",
        "file.scripts_run_rag_005_chunk_normalization",
        "file.scripts_validate_rag_005_chunk_normalization",
        "file.scripts_run_rag_006_chunk_review_packet",
        "file.scripts_validate_rag_006_chunk_review_packet",
        "file.scripts_run_rag_007_reviewed_first_slice",
        "file.scripts_validate_rag_007_reviewed_first_slice",
        "file.scripts_run_rag_008_guarded_retrieval_policy",
        "file.scripts_validate_rag_008_guarded_retrieval_policy",
        "file.scripts_run_rag_009_all_source_review_coverage",
        "file.scripts_validate_rag_009_all_source_review_coverage",
        "file.scripts_run_rag_010_reviewed_expansion_slice",
        "file.scripts_validate_rag_010_reviewed_expansion_slice",
        "file.scripts_run_rag_011_blocker_cleanup_packet",
        "file.scripts_validate_rag_011_blocker_cleanup_packet",
        "file.scripts_run_rag_012_accepted_cleanup",
        "file.scripts_validate_rag_012_accepted_cleanup",
        "file.scripts_local_voice_config",
        "file.scripts_validate_local_voice_config",
        "file.scripts_read_relevant",
        "file.scripts_validate_read_relevant",
        "file.scripts_validate_context_reading_policy",
        "file.scripts_sales_voice_tuning",
        "file.scripts_run_voice_018_sales_voice_tuning",
        "file.scripts_validate_voice_018_sales_voice_tuning",
        "file.scripts_run_voice_019_sales_tuned_live_ab_audio",
        "file.scripts_validate_voice_019_sales_tuned_live_ab_audio",
        "file.scripts_run_voice_020_elevenlabs_voice_design",
        "file.scripts_validate_voice_020_elevenlabs_voice_design",
        "file.scripts_run_voice_021_custom_voice_comparison",
        "file.scripts_validate_voice_021_custom_voice_comparison",
        "file.scripts_spoken_text_normalization",
        "file.scripts_run_voice_022_spoken_text_normalization",
        "file.scripts_validate_voice_022_spoken_text_normalization",
        "file.scripts_speech_realism",
        "file.scripts_run_voice_023_speech_realism",
        "file.scripts_validate_voice_023_speech_realism",
        "file.scripts_run_voice_024_speech_realism_live_ab",
        "file.scripts_validate_voice_024_speech_realism_live_ab",
        "file.scripts_run_voice_025_filler_placement",
        "file.scripts_validate_voice_025_filler_placement",
        "file.scripts_speech_interaction",
        "file.scripts_run_voice_026_interaction_prosody",
        "file.scripts_validate_voice_026_interaction_prosody",
        "file.scripts_run_voice_027_interaction_prosody_live_ab",
        "file.scripts_validate_voice_027_interaction_prosody_live_ab",
        "file.scripts_speech_imperfections",
        "file.scripts_run_voice_028_controlled_imperfections",
        "file.scripts_validate_voice_028_controlled_imperfections",
        "file.scripts_personal_speech_profile",
        "file.scripts_run_voice_029_local_speech_profile",
        "file.scripts_validate_voice_029_local_speech_profile",
        "file.scripts_init_personal_speech_learning_workspace",
        "file.scripts_raw_audio_speech_features",
        "file.scripts_run_voice_030_raw_audio_reader",
        "file.scripts_validate_voice_030_raw_audio_reader",
        "file.scripts_private_speech_learning_queue",
        "file.scripts_run_voice_030b_local_speech_capture",
        "file.scripts_validate_voice_030b_local_speech_capture",
        "file.scripts_validate_voice_030c_private_learning_queue",
        "file.scripts_run_voice_030d_private_feature_review",
        "file.scripts_validate_voice_030d_private_feature_review",
        "file.scripts_voice_feature_runtime_mapping",
        "file.scripts_run_voice_031_feature_runtime_mapping",
        "file.scripts_validate_voice_031_feature_runtime_mapping",
        "file.scripts_private_audio_conversion",
        "file.scripts_run_voice_032_local_audio_conversion",
        "file.scripts_validate_voice_032_local_audio_conversion",
        "file.scripts_private_sample_readiness",
        "file.scripts_run_voice_033_private_sample_readiness",
        "file.scripts_validate_voice_033_private_sample_readiness",
        "file.scripts_voice_pacing_calibration",
        "file.scripts_run_voice_034_pacing_calibration",
        "file.scripts_validate_voice_034_pacing_calibration",
        "file.scripts_voice_connected_speech",
        "file.scripts_run_voice_035_connected_speech",
        "file.scripts_validate_voice_035_connected_speech",
        "file.scripts_voice_listening_calibration",
        "file.scripts_run_voice_036_listening_calibration",
        "file.scripts_validate_voice_036_listening_calibration",
        "file.scripts_voice_emotion_smoothing",
        "file.scripts_run_voice_037_emotion_smoothing",
        "file.scripts_validate_voice_037_emotion_smoothing",
        "file.scripts_run_voice_038_semantic_emphasis",
        "file.scripts_validate_voice_038_semantic_emphasis",
        "file.scripts_realtime_turn_cli",
        "file.scripts_start_guarded_local_server",
        "file.research_private_call_learning_001",
        "file.research_case_private_call_learning_001",
        "file.research_case_voice_023_speech_realism",
        "file.research_case_voice_024_speech_realism_live_ab",
        "file.research_case_voice_025_filler_placement",
        "file.research_case_voice_026_interaction_prosody",
        "file.research_case_voice_027_interaction_prosody_live_ab",
        "file.research_case_voice_028_controlled_imperfections",
        "file.research_case_voice_029_local_speech_profile",
        "file.research_case_voice_030_raw_audio_reader",
        "file.research_case_voice_030b_local_speech_capture",
        "file.research_case_voice_030c_private_learning_queue",
        "file.research_case_voice_030d_private_feature_review",
        "file.research_case_voice_031_feature_runtime_mapping",
        "file.research_case_voice_032_local_audio_conversion",
        "file.research_case_voice_033_private_sample_readiness",
        "file.research_case_voice_034_pacing_calibration",
        "file.research_case_voice_035_connected_speech",
        "file.research_case_voice_036_listening_calibration",
        "file.research_case_voice_037_emotion_smoothing",
        "file.research_case_voice_038_semantic_emphasis",
        "file.research_case_rag_001_notebooklm_source_intake",
        "file.research_case_rag_002_notebooklm_extraction_automation",
        "file.research_case_rag_003_report_import_readiness",
        "file.research_case_rag_004_source_manifest_normalization",
        "file.research_case_rag_005_chunk_normalization",
        "file.research_case_rag_006_chunk_review_packet",
        "file.research_case_rag_007_reviewed_first_slice",
        "file.research_case_rag_008_guarded_retrieval_policy",
        "file.research_case_rag_009_all_source_review_coverage",
        "file.research_case_rag_010_reviewed_expansion_slice",
        "file.research_case_rag_011_blocker_cleanup_packet",
        "file.research_case_rag_012_accepted_cleanup",
        "write.research_experiments_generated",
    ]:
        assert_condition(required_check in checks_by_id, f"Missing setup check: {required_check}")
        assert_condition(checks_by_id[required_check]["status"] == "pass", f"Setup check failed: {required_check}")

    env_by_name = {entry["name"]: entry for entry in payload["environment"]}
    for name in SECRET_VALUES:
        assert_condition(name in env_by_name, f"Missing environment gate: {name}")
        assert_condition(env_by_name[name]["present"] is True, f"Expected test env var to be detected: {name}")
        assert_condition(env_by_name[name]["value_logged"] is False, f"Environment value should not be logged: {name}")
        assert_condition(env_by_name[name]["required_for_default_setup"] is False, f"{name} should not be required by default.")

    print("Product setup verifier validation passed.")


if __name__ == "__main__":
    main()
