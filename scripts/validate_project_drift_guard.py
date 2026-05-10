#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "check_project_drift.py"
FIXTURE_ROOT = ROOT / ".tmp" / "project-drift-validation" / f"run-{uuid.uuid4().hex}"

REQUIRED_FIXTURE_FILES = [
    "AGENTS.md",
    "README.md",
    "docs/PROJECT_NAVIGATION.md",
    "docs/brain/README.md",
    "docs/product/CONTEXT_READING_POLICY.md",
    "docs/product/PROJECT_SELF_CONTAINMENT_POLICY.md",
    "docs/product/VOICE_PROVIDER_RUN_BOUNDARY.md",
    "docs/product/VOICE_GENERATED_AUDIO_ASSET_LOG.md",
    "docs/product/PROJECT_DRIFT_GUARD.md",
    "docs/product/CHECKPOINT_INDEX.md",
    "docs/product/FULL_SALE_MVP_STRATEGY.md",
    "docs/product/PROD_007_FULL_CALL_GAUNTLET.md",
    "docs/product/PROD_008_GENERATED_FULL_CALL_PACKETS.md",
    "docs/product/PROD_009_CROSS_DOMAIN_GENERATED_GAUNTLET.md",
    "docs/product/PROD_010_LONG_CALL_UNIVERSAL_OBJECTIONS.md",
    "docs/product/PROD_021_LIVE_SHAPED_DIALOGUE_POLICY_SIMULATION.md",
    "docs/product/PROD_022_PROD_021_REVIEW_GAP_PACKET.md",
    "docs/product/PROD_023_RUNTIME_POLICY_CALL_CONTROL_FIX.md",
    "docs/product/PROD_024_LIVE_SHAPED_POST_FIX_RERUN.md",
    "docs/product/PROD_025_BOUNDED_DEMO_READINESS_PACKET.md",
    "docs/product/PROD_026_LOCAL_DEMO_TRACE_HARNESS.md",
    "docs/product/PROD_027_FULL_SCENARIO_ROUTE_EVALUATION.md",
    "docs/product/PROD_028_SYNTHETIC_CAMPAIGN_KNOWLEDGE_GROUNDING.md",
    "docs/product/PROD_029_GROUNDED_FULL_SCENARIO_RERUN.md",
    "docs/product/PROD_030_GROUNDED_DEMO_REVIEW.md",
    "docs/product/PROD_031_INTERACTIVE_GROUNDED_CALL_SIMULATION.md",
    "docs/product/PROD_032_INTERACTIVE_SIMULATION_REVIEW.md",
    "docs/product/PROD_033_INTERACTIVE_SIMULATOR_TERMINATION_FIX.md",
    "docs/product/PROD_034_INTERACTIVE_POST_FIX_REVIEW.md",
    "docs/product/PROD_035_RUNTIME_DECISION_TRACE_ALIGNMENT.md",
    "docs/brain/PROD_011_DIALOGUE_POLICY_HARDENING.md",
    "docs/brain/BRAIN_001_PROJECT_BRAIN_ARCHITECTURE.md",
    "docs/brain/BRAIN_002_RUNTIME_STATE_SCHEMA.md",
    "docs/product/VOICE_024_SPEECH_REALISM_LIVE_AB.md",
    "docs/product/VOICE_025_FILLER_PLACEMENT.md",
    "docs/product/VOICE_026_INTERACTION_PROSODY.md",
    "docs/product/VOICE_027_INTERACTION_PROSODY_LIVE_AB.md",
    "docs/product/VOICE_028_CONTROLLED_IMPERFECTIONS.md",
    "docs/product/VOICE_029_LOCAL_SPEECH_PROFILE_LEARNING.md",
    "docs/product/VOICE_030A_RAW_AUDIO_LOCAL_READER.md",
    "docs/product/VOICE_030B_LOCAL_SPEECH_CAPTURE.md",
    "docs/product/VOICE_030C_PRIVATE_LEARNING_QUEUE.md",
    "docs/product/VOICE_030D_PRIVATE_FEATURE_REVIEW.md",
    "docs/product/VOICE_031_FEATURE_RUNTIME_MAPPING.md",
    "docs/product/VOICE_032_LOCAL_AUDIO_CONVERSION.md",
    "docs/product/VOICE_033_PRIVATE_SAMPLE_READINESS.md",
    "docs/product/VOICE_034_PACING_CALIBRATION_V2.md",
    "docs/product/VOICE_035_CONNECTED_SPEECH_PHRASE_FLOW.md",
    "docs/product/VOICE_036_LISTENING_CALIBRATION.md",
    "docs/product/VOICE_037_EMOTION_TRANSITION_SMOOTHING.md",
    "docs/product/VOICE_038_SEMANTIC_EMPHASIS_DIAGNOSIS.md",
    "docs/product/VOICE_039_RUNTIME_SEMANTIC_EMPHASIS.md",
    "docs/product/VOICE_040_LOW_PRESSURE_FOCUS.md",
    "docs/product/RESP_004_VOICE_044_LISTENING_CHECK.md",
    "docs/product/RAG_001_NOTEBOOKLM_SOURCE_INTAKE_BRIDGE.md",
    "docs/product/RAG_002_NOTEBOOKLM_EXTRACTION_AUTOMATION_BRIDGE.md",
    "docs/product/RAG_003_REPORT_IMPORT_READINESS.md",
    "docs/product/RAG_004_SOURCE_MANIFEST_NORMALIZATION.md",
    "docs/product/RAG_005_CHUNK_NORMALIZATION.md",
    "docs/product/RAG_006_CHUNK_REVIEW_PACKET.md",
    "docs/product/COMMANDS.md",
    "docs/product-review-gates.md",
    "docs/third-party-inspirations.md",
    "docs/data/PRIVATE_CALL_CENTER_DATA_POLICY.md",
    "docs/data/PRIVATE_CALL_LEARNING_PIPELINE.md",
    "docs/thesis/ROADMAP.md",
    "docs/thesis/METHODOLOGY_LOG.md",
    "docs/thesis/DECISION_LOG.md",
    "docs/thesis/THESIS_REFERENCE_REGISTRY.md",
    "docs/thesis/THESIS_WRITING_GUIDE.md",
    "data/private/.gitignore",
    "data/external/.gitignore",
    "scripts/check_project_drift.py",
    "scripts/check_thesis_reference_registry.py",
    "scripts/validate_thesis_reference_registry.py",
    "scripts/check_thesis_update_gate.py",
    "scripts/validate_thesis_update_gate.py",
    "scripts/brain_runtime_state_schema.py",
    "scripts/run_brain_002_runtime_state_schema.py",
    "scripts/validate_brain_002_runtime_state_schema.py",
    "scripts/full_call_gauntlet.py",
    "scripts/run_prod_007_full_call_gauntlet.py",
    "scripts/validate_prod_007_full_call_gauntlet.py",
    "scripts/generated_full_call_packets.py",
    "scripts/run_prod_008_generated_full_call_packets.py",
    "scripts/validate_prod_008_generated_full_call_packets.py",
    "scripts/run_prod_009_cross_domain_generated_gauntlet.py",
    "scripts/validate_prod_009_cross_domain_generated_gauntlet.py",
    "scripts/run_prod_010_long_call_universal_objections.py",
    "scripts/validate_prod_010_long_call_universal_objections.py",
    "scripts/dialogue_policy_hardening.py",
    "scripts/run_prod_011_dialogue_policy_hardening.py",
    "scripts/validate_prod_011_dialogue_policy_hardening.py",
    "scripts/prod_021_live_shaped_dialogue_policy_simulation.py",
    "scripts/run_prod_021_live_shaped_dialogue_policy_simulation.py",
    "scripts/validate_prod_021_live_shaped_dialogue_policy_simulation.py",
    "scripts/prod_022_prod_021_review_gap_packet.py",
    "scripts/run_prod_022_prod_021_review_gap_packet.py",
    "scripts/validate_prod_022_prod_021_review_gap_packet.py",
    "scripts/prod_023_runtime_policy_call_control_fix.py",
    "scripts/run_prod_023_runtime_policy_call_control_fix.py",
    "scripts/validate_prod_023_runtime_policy_call_control_fix.py",
    "scripts/prod_024_live_shaped_post_fix_rerun.py",
    "scripts/run_prod_024_live_shaped_post_fix_rerun.py",
    "scripts/validate_prod_024_live_shaped_post_fix_rerun.py",
    "scripts/prod_025_bounded_demo_readiness_packet.py",
    "scripts/run_prod_025_bounded_demo_readiness_packet.py",
    "scripts/validate_prod_025_bounded_demo_readiness_packet.py",
    "scripts/prod_026_local_demo_trace_harness.py",
    "scripts/run_prod_026_local_demo_trace_harness.py",
    "scripts/validate_prod_026_local_demo_trace_harness.py",
    "scripts/prod_027_full_scenario_route_evaluation.py",
    "scripts/run_prod_027_full_scenario_route_evaluation.py",
    "scripts/validate_prod_027_full_scenario_route_evaluation.py",
    "scripts/prod_028_synthetic_campaign_knowledge_grounding.py",
    "scripts/run_prod_028_synthetic_campaign_knowledge_grounding.py",
    "scripts/validate_prod_028_synthetic_campaign_knowledge_grounding.py",
    "scripts/prod_029_grounded_full_scenario_rerun.py",
    "scripts/run_prod_029_grounded_full_scenario_rerun.py",
    "scripts/validate_prod_029_grounded_full_scenario_rerun.py",
    "scripts/prod_030_grounded_demo_review.py",
    "scripts/run_prod_030_grounded_demo_review.py",
    "scripts/validate_prod_030_grounded_demo_review.py",
    "scripts/prod_031_interactive_grounded_call_simulation.py",
    "scripts/run_prod_031_interactive_grounded_call_simulation.py",
    "scripts/validate_prod_031_interactive_grounded_call_simulation.py",
    "scripts/prod_032_interactive_simulation_review.py",
    "scripts/run_prod_032_interactive_simulation_review.py",
    "scripts/validate_prod_032_interactive_simulation_review.py",
    "scripts/prod_033_interactive_simulator_termination_fix.py",
    "scripts/run_prod_033_interactive_simulator_termination_fix.py",
    "scripts/validate_prod_033_interactive_simulator_termination_fix.py",
    "scripts/prod_034_interactive_post_fix_review.py",
    "scripts/run_prod_034_interactive_post_fix_review.py",
    "scripts/validate_prod_034_interactive_post_fix_review.py",
    "scripts/prod_035_runtime_decision_trace_alignment.py",
    "scripts/run_prod_035_runtime_decision_trace_alignment.py",
    "scripts/validate_prod_035_runtime_decision_trace_alignment.py",
    "scripts/speech_realism.py",
    "scripts/run_voice_023_speech_realism.py",
    "scripts/validate_voice_023_speech_realism.py",
    "scripts/run_voice_024_speech_realism_live_ab.py",
    "scripts/validate_voice_024_speech_realism_live_ab.py",
    "scripts/run_voice_025_filler_placement.py",
    "scripts/validate_voice_025_filler_placement.py",
    "scripts/speech_interaction.py",
    "scripts/run_voice_026_interaction_prosody.py",
    "scripts/validate_voice_026_interaction_prosody.py",
    "scripts/run_voice_027_interaction_prosody_live_ab.py",
    "scripts/validate_voice_027_interaction_prosody_live_ab.py",
    "scripts/speech_imperfections.py",
    "scripts/run_voice_028_controlled_imperfections.py",
    "scripts/validate_voice_028_controlled_imperfections.py",
    "scripts/personal_speech_profile.py",
    "scripts/run_voice_029_local_speech_profile.py",
    "scripts/validate_voice_029_local_speech_profile.py",
    "scripts/init_personal_speech_learning_workspace.py",
    "scripts/raw_audio_speech_features.py",
    "scripts/run_voice_030_raw_audio_reader.py",
    "scripts/validate_voice_030_raw_audio_reader.py",
    "scripts/private_speech_learning_queue.py",
    "scripts/run_voice_030b_local_speech_capture.py",
    "scripts/validate_voice_030b_local_speech_capture.py",
    "scripts/validate_voice_030c_private_learning_queue.py",
    "scripts/run_voice_030d_private_feature_review.py",
    "scripts/validate_voice_030d_private_feature_review.py",
    "scripts/voice_feature_runtime_mapping.py",
    "scripts/run_voice_031_feature_runtime_mapping.py",
    "scripts/validate_voice_031_feature_runtime_mapping.py",
    "scripts/private_audio_conversion.py",
    "scripts/run_voice_032_local_audio_conversion.py",
    "scripts/validate_voice_032_local_audio_conversion.py",
    "scripts/private_sample_readiness.py",
    "scripts/run_voice_033_private_sample_readiness.py",
    "scripts/validate_voice_033_private_sample_readiness.py",
    "scripts/voice_pacing_calibration.py",
    "scripts/run_voice_034_pacing_calibration.py",
    "scripts/validate_voice_034_pacing_calibration.py",
    "scripts/voice_connected_speech.py",
    "scripts/run_voice_035_connected_speech.py",
    "scripts/validate_voice_035_connected_speech.py",
    "scripts/voice_listening_calibration.py",
    "scripts/run_voice_036_listening_calibration.py",
    "scripts/validate_voice_036_listening_calibration.py",
    "scripts/voice_emotion_smoothing.py",
    "scripts/run_voice_037_emotion_smoothing.py",
    "scripts/validate_voice_037_emotion_smoothing.py",
    "scripts/run_voice_038_semantic_emphasis_diagnosis.py",
    "scripts/validate_voice_038_semantic_emphasis_diagnosis.py",
    "scripts/voice_semantic_emphasis.py",
    "scripts/run_voice_039_runtime_semantic_emphasis.py",
    "scripts/validate_voice_039_runtime_semantic_emphasis.py",
    "scripts/voice_low_pressure_focus.py",
    "scripts/run_voice_040_low_pressure_focus.py",
    "scripts/validate_voice_040_low_pressure_focus.py",
    "scripts/run_resp_004_voice_044_listening_check.py",
    "scripts/validate_resp_004_voice_044_listening_check.py",
    "scripts/rag_knowledge_base.py",
    "scripts/rag_notebooklm_automation.py",
    "scripts/rag_report_import_readiness.py",
    "scripts/rag_source_manifest_normalization.py",
    "scripts/rag_chunk_normalization.py",
    "scripts/rag_chunk_review_packet.py",
    "scripts/run_rag_001_notebooklm_source_intake.py",
    "scripts/validate_rag_001_notebooklm_source_intake.py",
    "scripts/run_rag_002_notebooklm_extraction_automation.py",
    "scripts/validate_rag_002_notebooklm_extraction_automation.py",
    "scripts/run_rag_003_report_import_readiness.py",
    "scripts/validate_rag_003_report_import_readiness.py",
    "scripts/run_rag_004_source_manifest_normalization.py",
    "scripts/validate_rag_004_source_manifest_normalization.py",
    "scripts/run_rag_005_chunk_normalization.py",
    "scripts/validate_rag_005_chunk_normalization.py",
    "scripts/run_rag_006_chunk_review_packet.py",
    "scripts/validate_rag_006_chunk_review_packet.py",
    "research/experiments/cases/voice-024-speech-realism-live-ab.json",
    "research/experiments/cases/voice-025-filler-placement.json",
    "research/experiments/cases/voice-026-interaction-prosody.json",
    "research/experiments/cases/voice-027-interaction-prosody-live-ab.json",
    "research/experiments/cases/voice-028-controlled-imperfections.json",
    "research/experiments/cases/voice-029-local-speech-profile-learning.json",
    "research/experiments/cases/voice-030-raw-audio-local-reader.json",
    "research/experiments/cases/voice-030b-local-speech-capture.json",
    "research/experiments/cases/voice-030c-private-learning-queue.json",
    "research/experiments/cases/voice-030d-private-feature-review.json",
    "research/experiments/cases/voice-031-feature-runtime-mapping.json",
    "research/experiments/cases/voice-032-local-audio-conversion.json",
    "research/experiments/cases/voice-033-private-sample-readiness.json",
    "research/experiments/cases/voice-034-pacing-calibration-v2.json",
    "research/experiments/cases/voice-035-connected-speech-phrase-flow.json",
    "research/experiments/cases/voice-036-listening-calibration.json",
    "research/experiments/cases/voice-037-emotion-smoothing.json",
    "research/experiments/cases/voice-038-semantic-emphasis-diagnosis.json",
    "research/experiments/cases/voice-039-runtime-semantic-emphasis.json",
    "research/experiments/cases/voice-040-low-pressure-focus.json",
    "research/experiments/cases/rag-001-notebooklm-source-intake-bridge.json",
    "research/experiments/cases/rag-002-notebooklm-extraction-automation-bridge.json",
    "research/experiments/cases/rag-003-report-import-readiness.json",
    "research/experiments/cases/rag-004-source-manifest-normalization.json",
    "research/experiments/cases/rag-005-chunk-normalization.json",
    "research/experiments/cases/rag-006-chunk-review-packet.json",
    "research/experiments/cases/brain-002-runtime-state-schema.json",
    "research/experiments/cases/prod-007-full-call-gauntlet.json",
    "research/experiments/cases/prod-008-generated-full-call-packets.json",
    "research/experiments/cases/prod-009-cross-domain-generated-gauntlet.json",
    "research/experiments/cases/prod-010-long-call-universal-objections.json",
    "research/experiments/cases/prod-011-dialogue-policy-hardening.json",
    "research/experiments/cases/prod-021-live-shaped-dialogue-policy-simulation.json",
    "research/experiments/README.md",
    "scripts/README.md",
    "data/rag/README.md",
    "scripts/validate_private_data_boundary.py",
    "scripts/check_private_call_learning_pipeline.py",
    "scripts/init_private_call_learning_workspace.py",
    "scripts/validate_private_call_learning_pipeline.py",
    "scripts/validate_context_reading_policy.py",
    "scripts/validate_project_drift_guard.py",
]


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def create_base_fixture(root: Path) -> None:
    for relative_path in REQUIRED_FIXTURE_FILES:
        write_text(root / relative_path, f"# {Path(relative_path).name}\n\nFixture file.\n")
    (root / "research" / "experiments" / "generated").mkdir(parents=True, exist_ok=True)
    write_text(
        root / ".gitignore",
        "\n".join(
            [
                ".tmp/",
                "__pycache__/",
                "data/public/*",
                "data/private/*",
                "!data/private/.gitignore",
                "research/experiments/generated/*.mp3",
                "research/experiments/generated/*.wav",
                "research/experiments/generated/**/*.mp3",
                "research/experiments/generated/**/*.wav",
                "",
            ]
        ),
    )


def create_dirty_fixture(root: Path) -> None:
    create_base_fixture(root)
    write_text(root / "README.md", "# Dirty fixture\n\n<<<<<<< HEAD\nlocal\n=======\nremote\n>>>>>>> branch\n")
    external_path = "/".join(["D:", "Codex", "shared", "templates", "voice-ai-consent-checklist.md"])
    write_text(
        root / "scripts" / "bad_external_dependency.py",
        "SOURCE = " + repr(external_path) + "\n",
    )
    fake_secret = "sk-" + "TESTVALUE" + ("X" * 24)
    write_text(root / "docs" / "bad-secret.md", f"Do not store keys like {fake_secret}.\n")
    write_text(root / ".gitignore", ".tmp/\n__pycache__/\n")
    write_text(root / "research" / "experiments" / "generated" / "flat-result.json", "{}\n")
    write_text(root / "research" / "experiments" / "generated" / "VOICE-999" / "stale-result.json", "{}\n")
    old_brain_path = "docs/" + "product/" + "BRAIN_001_PROJECT_BRAIN_ARCHITECTURE.md"
    old_generated_path = "research/experiments/generated/" + "stale-result.json"
    write_text(
        root / "docs" / "stale-paths.md",
        "\n".join(
            [
                f"Old brain path: `{old_brain_path}`.",
                f"Old generated path: `{old_generated_path}`.",
                "",
            ]
        ),
    )
    audio_path = root / "research" / "experiments" / "generated" / "leaky-audio.mp3"
    audio_path.write_bytes(b"fixture audio bytes")


def run_guard(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--root", str(root), "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )


def parse_json_output(completed: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Guard did not return valid JSON. stdout={completed.stdout!r} stderr={completed.stderr!r}") from exc


def validate_dirty_fixture() -> None:
    dirty_root = FIXTURE_ROOT / "dirty"
    create_dirty_fixture(dirty_root)

    completed = run_guard(dirty_root)
    assert_condition(completed.returncode != 0, "Dirty fixture should fail project drift guard.")
    payload = parse_json_output(completed)
    assert_condition(payload["status"] == "fail", "Dirty fixture payload should be fail.")

    issue_codes = {issue["code"] for issue in payload["issues"]}
    for expected_code in [
        "conflict_marker",
        "external_workspace_dependency",
        "secret_like_value",
        "flat_generated_artifact",
        "generated_audio_not_ignored",
        "stale_project_path_reference",
        "stale_generated_artifact_reference",
    ]:
        assert_condition(expected_code in issue_codes, f"Dirty fixture did not report {expected_code}.")

    assert_condition(payload["summary"]["auto_fixes_applied"] is False, "Guard must not auto-fix dirty fixture.")


def validate_clean_fixture() -> None:
    clean_root = FIXTURE_ROOT / "clean"
    create_base_fixture(clean_root)
    audio_path = clean_root / "research" / "experiments" / "generated" / "VOICE-999" / "audio" / "ignored-audio.mp3"
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    audio_path.write_bytes(b"fixture audio bytes")

    completed = run_guard(clean_root)
    assert_condition(completed.returncode == 0, f"Clean fixture should pass. stderr={completed.stderr!r}")
    payload = parse_json_output(completed)
    assert_condition(payload["status"] == "pass", "Clean fixture payload should be pass.")
    assert_condition(payload["summary"]["failure_count"] == 0, "Clean fixture should not have failures.")
    assert_condition(payload["summary"]["auto_fixes_applied"] is False, "Guard must not auto-fix clean fixture.")


def validate_current_repo() -> None:
    completed = run_guard(ROOT)
    assert_condition(completed.returncode == 0, f"Current repo should pass project drift guard. stdout={completed.stdout!r}")
    payload = parse_json_output(completed)
    assert_condition(payload["project"] == "emotion-aware-ai-sales-agent", "Unexpected project name.")
    assert_condition(payload["status"] == "pass", "Current repo drift guard status should be pass.")
    assert_condition(payload["summary"]["auto_fixes_applied"] is False, "Guard must not auto-fix current repo.")


def main() -> None:
    assert_condition(SCRIPT_PATH.exists(), "Project drift guard runner is missing.")
    FIXTURE_ROOT.mkdir(parents=True, exist_ok=True)

    try:
        validate_dirty_fixture()
        validate_clean_fixture()
        validate_current_repo()
    finally:
        shutil.rmtree(FIXTURE_ROOT, ignore_errors=True)

    print("Project drift guard validation passed.")


if __name__ == "__main__":
    main()
