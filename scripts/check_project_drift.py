#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_NAME = "emotion-aware-ai-sales-agent"
ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "AGENTS.md",
    "README.md",
    "docs/third-party-inspirations.md",
    "docs/product-review-gates.md",
    "docs/PROJECT_NAVIGATION.md",
    "docs/brain/README.md",
    "docs/product/COMMANDS.md",
    "docs/product/CHECKPOINT_INDEX.md",
    "docs/product/CONTEXT_READING_POLICY.md",
    "docs/product/PROJECT_SELF_CONTAINMENT_POLICY.md",
    "docs/product/VOICE_PROVIDER_RUN_BOUNDARY.md",
    "docs/product/VOICE_GENERATED_AUDIO_ASSET_LOG.md",
    "docs/product/PROJECT_DRIFT_GUARD.md",
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
    "docs/product/PROD_036_INTERACTIVE_DEMO_READINESS_REVIEW.md",
    "docs/brain/PROD_011_DIALOGUE_POLICY_HARDENING.md",
    "docs/brain/BRAIN_001_PROJECT_BRAIN_ARCHITECTURE.md",
    "docs/brain/BRAIN_002_RUNTIME_STATE_SCHEMA.md",
    "docs/product/RAG_001_NOTEBOOKLM_SOURCE_INTAKE_BRIDGE.md",
    "docs/product/RAG_002_NOTEBOOKLM_EXTRACTION_AUTOMATION_BRIDGE.md",
    "docs/product/RAG_003_REPORT_IMPORT_READINESS.md",
    "docs/product/RAG_004_SOURCE_MANIFEST_NORMALIZATION.md",
    "docs/product/RAG_005_CHUNK_NORMALIZATION.md",
    "docs/product/RAG_006_CHUNK_REVIEW_PACKET.md",
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
    "scripts/prod_036_interactive_demo_readiness_review.py",
    "scripts/run_prod_036_interactive_demo_readiness_review.py",
    "scripts/validate_prod_036_interactive_demo_readiness_review.py",
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
    "data/rag/README.md",
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
    "scripts/validate_private_data_boundary.py",
    "scripts/check_private_call_learning_pipeline.py",
    "scripts/init_private_call_learning_workspace.py",
    "scripts/validate_private_call_learning_pipeline.py",
    "scripts/validate_context_reading_policy.py",
    "scripts/validate_project_drift_guard.py",
]

ALLOWED_EXTERNAL_REFERENCE_FILES = {
    "AGENTS.md",
    "docs/internal-development-tools.md",
    "docs/product-local-tooling-candidates.md",
    "docs/third-party-inspirations.md",
    "docs/product/COMMANDS.md",
    "docs/product/PROJECT_SELF_CONTAINMENT_POLICY.md",
    "docs/product/PROJECT_DRIFT_GUARD.md",
    "docs/product-review-gates.md",
    "docs/thesis/METHODOLOGY_LOG.md",
    "docs/thesis/ROADMAP.md",
}

TEXT_EXTENSIONS = {
    ".css",
    ".csv",
    ".html",
    ".js",
    ".json",
    ".md",
    ".mjs",
    ".py",
    ".sql",
    ".toml",
    ".ts",
    ".txt",
    ".yml",
    ".yaml",
}

BINARY_EXTENSIONS = {
    ".db",
    ".jpeg",
    ".jpg",
    ".mp3",
    ".pdf",
    ".png",
    ".pyc",
    ".sqlite",
    ".wav",
}

SKIP_DIRS = {
    ".git",
    ".tmp",
    "__pycache__",
}

SKIP_DIR_PREFIXES = {
    ("data", "public"),
    ("data", "private"),
    ("data", "private-restricted"),
    ("data", "processed"),
    ("data", "external"),
    ("config", "local"),
}

AUDIO_EXTENSIONS = {".mp3", ".wav"}
ALLOWED_GENERATED_ROOT_FILES = {"README.md"}

CURATED_GENERATED_AUDIO_FILES = {
    "research/experiments/generated/VOICE-002/VOICE-002-customer-placeholder.wav",
}

OLD_PRODUCT_DOCS = "docs/" + "product/"

STALE_PROJECT_PATH_REPLACEMENTS = {
    OLD_PRODUCT_DOCS + "BRAIN_001_PROJECT_BRAIN_ARCHITECTURE.md": "docs/brain/BRAIN_001_PROJECT_BRAIN_ARCHITECTURE.md",
    OLD_PRODUCT_DOCS + "BRAIN_002_RUNTIME_STATE_SCHEMA.md": "docs/brain/BRAIN_002_RUNTIME_STATE_SCHEMA.md",
    OLD_PRODUCT_DOCS + "PROD_011_DIALOGUE_POLICY_HARDENING.md": "docs/brain/PROD_011_DIALOGUE_POLICY_HARDENING.md",
}

DIRECT_GENERATED_ARTIFACT_RE = re.compile(
    r"research[\\/]+experiments[\\/]+generated[\\/]+(?P<filename>[A-Za-z0-9_.-]+\.(?:html|json|md|mp3|sqlite|wav))"
)

REFERENCE_GUARD_SOURCE_FILES = {
    "scripts/check_project_drift.py",
    "scripts/validate_project_drift_guard.py",
}

SECRET_PATTERNS = [
    r"sk_car_[A-Za-z0-9_-]{20,}",
    r"sk-[A-Za-z0-9_-]{20,}",
    r"AIza[0-9A-Za-z_-]{20,}",
    r"xox[baprs]-[A-Za-z0-9-]{20,}",
    r"CARTESIA_API_KEY\s*=\s*[^\s]+",
    r"ELEVENLABS_API_KEY\s*=\s*[^\s]+",
    r"OPENAI_API_KEY\s*=\s*[^\s]+",
    r"Authorization:\s*Bearer\s+[A-Za-z0-9]",
    r"X-API-Key\s*[:=]\s*[A-Za-z0-9]",
    r"xi-api-key\s*[:=]\s*[A-Za-z0-9]",
]

SECRET_RE = re.compile("|".join(SECRET_PATTERNS))


@dataclass(frozen=True)
class Issue:
    code: str
    severity: str
    path: str
    message: str
    line: int | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code,
            "severity": self.severity,
            "path": self.path,
            "message": self.message,
        }
        if self.line is not None:
            payload["line"] = self.line
        return payload


def join_path(*parts: str, sep: str) -> str:
    return sep.join(parts)


def build_external_workspace_patterns() -> list[str]:
    active = "active"
    workspace = ("D:", "Codex")
    projects = [
        ("career-ops",),
        ("youtube-channel",),
        ("client-websites",),
        ("codex-workspace-dashboard",),
    ]
    patterns = [
        join_path(*workspace, "shared", sep="/"),
        join_path(*workspace, "shared", sep="\\"),
        join_path("..", "..", "shared", sep="/"),
        join_path("..", "..", "shared", sep="\\"),
    ]
    for project in projects:
        patterns.append(join_path(active, *project, sep="/"))
        patterns.append(join_path(active, *project, sep="\\"))
        patterns.append(join_path(*workspace, active, *project, sep="/"))
        patterns.append(join_path(*workspace, active, *project, sep="\\"))
    return patterns


EXTERNAL_WORKSPACE_PATTERNS = build_external_workspace_patterns()


def normalize_relative(path: Path) -> str:
    return path.as_posix()


def relative_to_root(root: Path, path: Path) -> str:
    return normalize_relative(path.relative_to(root))


def should_skip_path(relative_path: Path) -> bool:
    parts = relative_path.parts
    if any(part in SKIP_DIRS for part in parts):
        return True
    for prefix in SKIP_DIR_PREFIXES:
        if len(parts) >= len(prefix) and tuple(parts[: len(prefix)]) == prefix:
            return True
    return relative_path.suffix.lower() in BINARY_EXTENSIONS


def iter_scan_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative_path = path.relative_to(root)
        if should_skip_path(relative_path):
            continue
        suffix = path.suffix.lower()
        if suffix and suffix not in TEXT_EXTENSIONS:
            continue
        files.append(path)
    return sorted(files)


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def build_generated_artifact_lookup(root: Path) -> dict[str, list[str]]:
    generated_root = root / "research" / "experiments" / "generated"
    lookup: dict[str, list[str]] = {}
    if not generated_root.is_dir():
        return lookup
    for path in sorted(generated_root.rglob("*")):
        if not path.is_file() or path.parent == generated_root:
            continue
        lookup.setdefault(path.name, []).append(relative_to_root(root, path))
    return lookup


def detect_missing_required_files(root: Path) -> list[Issue]:
    issues: list[Issue] = []
    for relative_path in REQUIRED_FILES:
        if not (root / relative_path).is_file():
            issues.append(
                Issue(
                    code="missing_required_file",
                    severity="fail",
                    path=relative_path,
                    message="Required project-local guard or documentation file is missing.",
                )
            )
    return issues


def detect_line_issues(root: Path, files: list[Path]) -> list[Issue]:
    issues: list[Issue] = []
    generated_lookup = build_generated_artifact_lookup(root)
    for path in files:
        text = read_text(path)
        if text is None:
            continue
        relative_path = relative_to_root(root, path)
        for line_number, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("<<<<<<< ") or stripped == "=======" or stripped.startswith(">>>>>>> "):
                issues.append(
                    Issue(
                        code="conflict_marker",
                        severity="fail",
                        path=relative_path,
                        line=line_number,
                        message="Git conflict marker found. Resolve the file before continuing.",
                    )
                )
            if SECRET_RE.search(line):
                issues.append(
                    Issue(
                        code="secret_like_value",
                        severity="fail",
                        path=relative_path,
                        line=line_number,
                        message="Secret-like value found. Move credentials to environment variables and rotate if exposed.",
                    )
                )
            if relative_path not in ALLOWED_EXTERNAL_REFERENCE_FILES:
                matched_external = any(pattern in line for pattern in EXTERNAL_WORKSPACE_PATTERNS)
                if matched_external:
                    issues.append(
                        Issue(
                            code="external_workspace_dependency",
                            severity="fail",
                            path=relative_path,
                            line=line_number,
                            message="Project file depends on material outside Emotion Aware. Adapt it locally or document it as inspiration only.",
                        )
                    )
            if relative_path in REFERENCE_GUARD_SOURCE_FILES:
                continue
            normalized_line = line.replace("\\", "/")
            for stale_path, current_path in STALE_PROJECT_PATH_REPLACEMENTS.items():
                if stale_path in normalized_line:
                    issues.append(
                        Issue(
                            code="stale_project_path_reference",
                            severity="fail",
                            path=relative_path,
                            line=line_number,
                            message=f"Reference points at old location {stale_path}; use {current_path}.",
                        )
                    )
            for match in DIRECT_GENERATED_ARTIFACT_RE.finditer(line):
                old_reference = match.group(0).replace("\\", "/")
                target = root / old_reference
                if target.exists():
                    continue
                filename = match.group("filename")
                candidates = generated_lookup.get(filename, [])
                if candidates:
                    replacement_hint = candidates[0] if len(candidates) == 1 else "the matching milestone/run subfolder"
                    issues.append(
                        Issue(
                            code="stale_generated_artifact_reference",
                            severity="fail",
                            path=relative_path,
                            line=line_number,
                            message=(
                                "Reference points at old generated-root artifact path; "
                                f"use {replacement_hint}."
                            ),
                        )
                    )
    return issues


def load_gitignore_patterns(root: Path) -> list[str]:
    gitignore_path = root / ".gitignore"
    if not gitignore_path.is_file():
        return []
    patterns: list[str] = []
    for raw_line in gitignore_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        patterns.append(line.replace("\\", "/"))
    return patterns


def ignore_pattern_matches(relative_path: str, pattern: str) -> bool:
    negated = pattern.startswith("!")
    if negated:
        pattern = pattern[1:]
    pattern = pattern.lstrip("/")
    if not pattern:
        return False
    if pattern.endswith("/"):
        return relative_path.startswith(pattern)
    if "/" not in pattern:
        path_parts = relative_path.split("/")
        return any(fnmatch.fnmatch(part, pattern) for part in path_parts)
    return fnmatch.fnmatch(relative_path, pattern)


def is_ignored_by_gitignore(relative_path: str, patterns: list[str]) -> bool:
    ignored = False
    for pattern in patterns:
        if ignore_pattern_matches(relative_path, pattern):
            ignored = not pattern.startswith("!")
    return ignored


def detect_unignored_generated_audio(root: Path) -> list[Issue]:
    generated_root = root / "research" / "experiments" / "generated"
    if not generated_root.is_dir():
        return []
    patterns = load_gitignore_patterns(root)
    issues: list[Issue] = []
    for path in sorted(generated_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in AUDIO_EXTENSIONS:
            continue
        relative_path = relative_to_root(root, path)
        if relative_path in CURATED_GENERATED_AUDIO_FILES:
            continue
        if not is_ignored_by_gitignore(relative_path, patterns):
            issues.append(
                Issue(
                    code="generated_audio_not_ignored",
                    severity="fail",
                    path=relative_path,
                    message="Generated audio artifact is not covered by .gitignore. Keep provider outputs local unless explicitly curated.",
                )
            )
    return issues


def detect_flat_generated_artifacts(root: Path) -> list[Issue]:
    generated_root = root / "research" / "experiments" / "generated"
    if not generated_root.is_dir():
        return []
    issues: list[Issue] = []
    for path in sorted(generated_root.iterdir()):
        if not path.is_file() or path.name in ALLOWED_GENERATED_ROOT_FILES:
            continue
        issues.append(
            Issue(
                code="flat_generated_artifact",
                severity="fail",
                path=relative_to_root(root, path),
                message="Generated artifacts should live in milestone/run subfolders; keep only README.md at the generated root.",
            )
        )
    return issues


def summarize(issues: list[Issue], files_scanned: int) -> tuple[str, dict[str, Any]]:
    failure_count = sum(1 for issue in issues if issue.severity == "fail")
    warning_count = sum(1 for issue in issues if issue.severity == "warning")
    status = "fail" if failure_count else "pass"
    return status, {
        "issue_count": len(issues),
        "failure_count": failure_count,
        "warning_count": warning_count,
        "files_scanned": files_scanned,
        "auto_fixes_applied": False,
    }


def build_report(root: Path) -> dict[str, Any]:
    files = iter_scan_files(root) if root.is_dir() else []
    issues: list[Issue] = []
    if not root.is_dir():
        issues.append(Issue("missing_project_root", "fail", ".", "Project root is missing."))
    else:
        issues.extend(detect_missing_required_files(root))
        issues.extend(detect_line_issues(root, files))
        issues.extend(detect_flat_generated_artifacts(root))
        issues.extend(detect_unignored_generated_audio(root))

    issue_payload = [issue.to_dict() for issue in sorted(issues, key=lambda item: (item.severity, item.path, item.line or 0, item.code))]
    status, summary = summarize(issues, len(files))
    return {
        "project": PROJECT_NAME,
        "root": str(root),
        "status": status,
        "summary": summary,
        "issues": issue_payload,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Project Drift Guard Report",
        "",
        f"- Project: {report['project']}",
        f"- Root: `{report['root']}`",
        f"- Status: `{report['status']}`",
        f"- Issues: {report['summary']['issue_count']}",
        f"- Failures: {report['summary']['failure_count']}",
        f"- Warnings: {report['summary']['warning_count']}",
        f"- Files scanned: {report['summary']['files_scanned']}",
        f"- Auto fixes applied: {str(report['summary']['auto_fixes_applied']).lower()}",
        "",
        "## Issues",
        "",
    ]
    if not report["issues"]:
        lines.append("No project drift issues found.")
    else:
        for issue in report["issues"]:
            location = issue["path"]
            if "line" in issue:
                location = f"{location}:{issue['line']}"
            lines.append(f"- `{issue['severity']}` `{issue['code']}` `{location}`: {issue['message']}")
    lines.append("")
    return "\n".join(lines)


def print_text_report(report: dict[str, Any]) -> None:
    print(f"{report['project']} project drift guard")
    print(f"Root: {report['root']}")
    print(f"Status: {report['status']}")
    print(
        "Summary: "
        f"{report['summary']['failure_count']} failure(s), "
        f"{report['summary']['warning_count']} warning(s), "
        f"{report['summary']['files_scanned']} file(s) scanned"
    )
    print("Auto fixes applied: false")
    if report["issues"]:
        print()
        print("Issues:")
        for issue in report["issues"]:
            location = issue["path"]
            if "line" in issue:
                location = f"{location}:{issue['line']}"
            print(f"- {issue['severity'].upper()} {issue['code']} [{location}]: {issue['message']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect self-containment and safety drift in the Emotion Aware project.")
    parser.add_argument("--root", default=str(ROOT), help="Project root to scan. Defaults to this repository root.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--report-out", help="Optional Markdown report output path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.root).resolve()
    report = build_report(root)

    if args.report_out:
        report_path = Path(args.report_out)
        if not report_path.is_absolute():
            report_path = root / report_path
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(render_markdown(report), encoding="utf-8")

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_text_report(report)

    raise SystemExit(0 if report["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
