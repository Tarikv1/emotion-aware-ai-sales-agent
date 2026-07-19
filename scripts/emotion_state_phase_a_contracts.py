from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from pathlib import PurePosixPath, PureWindowsPath
from collections.abc import Mapping
from typing import Any

from runtime.contracts.emotion_pattern_contracts import pattern_contract_self_check
from runtime.contracts.emotion_state_brain_extension import brain_extension_self_check
from runtime.contracts.emotion_state_contracts import contract_self_check
from scripts.emotion_state_annotation_contracts import annotation_contract_self_check
from scripts.emotion_state_cohort_release_contracts import cohort_release_contract_self_check
from scripts.exp_002_frozen_response_baseline import frozen_baseline_self_check


EXPECTED_ARCHIVE_SHA256 = "E579B966E226F2AF6E4F8F8203C7189FEC94FB448EFC09B4B6640C10A398ECCC"
EXPECTED_IMPLEMENTATION_BASELINE_COMMIT = (
    "fb0513545fc0167bcf89dbc81283b7b2a2820b67"
)
EXPECTED_BASELINE_FINGERPRINTS = {
    "packages/prompts/baseline-non-adaptive.txt": "BB1FD1EAC0D4DE858BFDCE4A880BBF2C59C14A216489A1A85EF149F3E88D7FCA",
    "packages/prompts/baseline-adaptive.txt": "EBD4106841987CA4A322C2B8B95A33ECFFC4238BB476DEC611A640D5B000EB42",
    "research/experiments/cases/exp-002-dataset-derived.json": "882B94C0A31C41A94540941A254AC7E8119CADE9AAD9B071089E854917BDC7D6",
    "research/experiments/EXP-002-dataset-derived-baseline.md": "D930C845AC912D44610B3CE263B55EA03BFFD7CAB8706C2BC95CB17045FF1316",
    "research/experiments/generated/EXP-002/EXP-002-prompt-packet.md": "14017F985D54D2B46A338EA2EFA796B24202E3E5A3D3EB8223346CEA96E5CD09",
    "docs/thesis/EVALUATION_RUBRIC.md": "39D3CF33E38A0C13ADEE178F3DB4174D4D8E3A42B1DE4C274BF96FFA36FFB416",
}
SELECTED_PUBLIC_DATASET_IDS = (
    "crema-d-v1.0-audio-wav",
    "ami-manual-annotations-v1.6.2",
)
DATASET_EVIDENCE_DIRECTORY = (
    "research/sources/emotion_state/datasets"
)
MATERIAL_PENDING_CONTRACT_STATUSES = {
    "public_dataset_contract": "pass",
    "split_manifest_v2_contract": "pass",
    "cohort_release_contract": "pass",
}
MATERIAL_PENDING_COMPLETION_SCOPE = (
    "source_provenance_dataset_selection_and_offline_contracts_only_"
    "material_verification_pending"
)
COMPLETE_PHASE_A_COMPLETION_SCOPE = (
    "source_provenance_dataset_manifests_offline_contracts_and_"
    "cohort_release_gate_only"
)
MATERIAL_PENDING_BLOCKERS = [
    "dataset_download_not_authorized",
    "selected_dataset_manifests_not_verified",
]
EXPECTED_CONTRACT_CHECKS = {
    "exp_002_frozen_response_baseline": "pass",
    "emotion_state_annotation_contracts": "pass",
    "public_dataset_contract": "pass",
    "split_manifest_v2_contract": "pass",
    "cohort_release_contract": "pass",
    "emotion_state_contracts": "pass",
    "emotion_pattern_contracts": "pass",
    "emotion_state_brain_extension": "pass",
}
MATERIAL_PENDING_PAYLOAD_FIELDS = {
    "checkpoint_id",
    "schema_version",
    "mode",
    "status",
    "selected_public_datasets",
    "dataset_download_authorized",
    "dataset_evaluation_started",
    "dataset_manifest_evidence",
    "source_pin",
    "contract_checks",
    "blocking_reason_codes",
    "summary",
    "archive_sha256",
    "baseline_fingerprints",
    "readiness_boundary",
}
VERIFICATION_EVIDENCE_FIELDS = {
    "implementation_baseline_commit",
    "repository_head_commit",
    "committed_change_inventory",
    "uncommitted_change_inventory",
    "executable_dependency_closure_inventory",
    "executable_dependency_closure_edges",
    "dataset_manifest_digests",
    "dataset_hash_inventory_digests",
    "executed_command_ledger",
    "guard_policy_digest",
    "verification_input_path_inventory_digest",
    "executable_dependency_closure_digest",
    "executed_command_ledger_digest",
    "verification_input_tree_digest",
    "verification_run_id",
    "guarded_command_results",
    "repository_gate_statuses",
    "provider_environment_scrubbed",
    "private_path_guard_enabled",
    "network_guard_enabled",
}
COMPLETE_VERIFICATION_EVIDENCE_FIELDS = VERIFICATION_EVIDENCE_FIELDS | {
    "dataset_quality_inventory_digests",
    "prepublication_byte_lock_reread_status",
}
COMPLETE_PAYLOAD_FIELDS = MATERIAL_PENDING_PAYLOAD_FIELDS | (
    COMPLETE_VERIFICATION_EVIDENCE_FIELDS
    | {
        "dataset_material_validation_status",
        "source_provenance_status",
        "public_dataset_contract_status",
        "cohort_release_contract_status",
        "split_manifest_v2_contract_status",
        "publication_integrity_preconditions",
    }
)
COMPLETE_READINESS_BOUNDARY_FIELDS = {
    "phase_a_contract_artifacts_built",
    "phase_a_complete",
    "phase_a_completion_scope",
    "full_repository_gate_claimed_by_this_artifact",
    "live_aggregate_release_unblocked",
    "phase_b_unblocked",
    "public_dataset_evaluation_unblocked",
    "private_research_unblocked",
    "provider_feasibility_unblocked",
    "runtime_activation_unblocked",
}
VERIFICATION_OUTPUT_EXCLUSIONS = {
    "research/experiments/generated/EMOTION-STATE-001-phase-a-contracts/result.json",
    "research/experiments/generated/EMOTION-STATE-001-phase-a-contracts/report.md",
}
VERIFICATION_RECOVERY_PREFIX = ".tmp/emotion-state-001-phase-a-publication"
MATERIAL_PENDING_EXCLUDED_PATH_PREFIXES = (
    ("data", "private"),
    ("data", "private-restricted"),
    ("data", "public", "emotion-state"),
    ("research", "sources", "emotion_state", "datasets"),
)
TASKS_1_7_CHANGE_INVENTORY_PATHS = (
    ".superpowers/sdd/task-4-report.md",
    ".superpowers/sdd/task-4-review-findings.md",
    "docs/product/COMMANDS.md",
    "docs/product/EMOTION_STATE_001_PHASE_A_CONTRACTS.md",
    (
        "docs/superpowers/plans/"
        "2026-07-15-emotion-state-phase-a-open-dataset-gate-completion.md"
    ),
    "docs/thesis/DECISION_LOG.md",
    "docs/thesis/METHODOLOGY_LOG.md",
    "docs/thesis/ROADMAP.md",
    "docs/thesis/THESIS_REFERENCE_REGISTRY.md",
    "docs/third-party-inspirations.md",
    "research/experiments/EMOTION-STATE-001-phase-a.md",
    (
        "research/experiments/cases/"
        "emotion-state-001-cohort-release-fixtures.json"
    ),
    "research/experiments/cases/emotion-state-001-phase-a-contracts.json",
    "research/sources/creative_analysis_engine/source_manifest.json",
    "research/sources/creative_analysis_engine/source_notes.md",
    (
        "research/sources/emotion_state/"
        "cohort_release_evidence_v1.schema.json"
    ),
    "research/sources/emotion_state/dataset_manifest_contract.json",
    (
        "research/sources/emotion_state/"
        "phase_a_verification_guard_policy.json"
    ),
    "research/sources/emotion_state/split_manifest_v2.schema.json",
    "scripts/build_emotion_state_public_dataset_manifests.py",
    "scripts/check_project_drift.py",
    "scripts/check_setup.py",
    "scripts/check_thesis_reference_registry.py",
    "scripts/emotion_state_cohort_release_contracts.py",
    "scripts/emotion_state_phase_a_contracts.py",
    "scripts/emotion_state_phase_a_guard_site/sitecustomize.py",
    "scripts/emotion_state_phase_a_verification_evidence.py",
    "scripts/emotion_state_public_dataset_contracts.py",
    "scripts/emotion_state_split_manifest_v2_contracts.py",
    "scripts/run_brain_002_runtime_state_schema.py",
    "scripts/run_emotion_state_001_phase_a_contracts.py",
    "scripts/run_exp_002_frozen_response_baseline.py",
    "scripts/test_emotion_state_001_closeout_hardening.py",
    "scripts/test_emotion_state_001_open_dataset_gate.py",
    "scripts/validate_check_setup.py",
    "scripts/validate_emotion_state_001_phase_a_contracts.py",
    "scripts/validate_private_data_boundary.py",
    "scripts/validate_project_drift_guard.py",
)
TASKS_1_7_CLOSURE_PATHS = (
    "runtime/__init__.py",
    "runtime/contracts/__init__.py",
    "runtime/contracts/brain_runtime_state_schema.py",
    "runtime/contracts/emotion_pattern_contracts.py",
    "runtime/contracts/emotion_state_brain_extension.py",
    "runtime/contracts/emotion_state_contracts.py",
    "scripts/build_emotion_state_public_dataset_manifests.py",
    "scripts/check_project_drift.py",
    "scripts/check_setup.py",
    "scripts/check_thesis_reference_registry.py",
    "scripts/emotion_state_annotation_contracts.py",
    "scripts/emotion_state_cohort_release_contracts.py",
    "scripts/emotion_state_phase_a_contracts.py",
    "scripts/emotion_state_phase_a_guard_site/sitecustomize.py",
    "scripts/emotion_state_phase_a_verification_evidence.py",
    "scripts/emotion_state_public_dataset_contracts.py",
    "scripts/emotion_state_split_manifest_v2_contracts.py",
    "scripts/exp_002_frozen_response_baseline.py",
    "scripts/run_brain_002_runtime_state_schema.py",
    "scripts/run_emotion_state_001_phase_a_contracts.py",
    "scripts/run_exp_002_frozen_response_baseline.py",
    "scripts/run_prompt_baseline.py",
    "scripts/test_emotion_state_001_closeout_hardening.py",
    "scripts/test_emotion_state_001_open_dataset_gate.py",
    "scripts/validate_brain_002_runtime_state_schema.py",
    "scripts/validate_check_setup.py",
    "scripts/validate_emotion_state_001_phase_a_contracts.py",
    "scripts/validate_exp_002_frozen_response_baseline.py",
    "scripts/validate_private_data_boundary.py",
    "scripts/validate_project_drift_guard.py",
)
TASKS_1_7_CLOSURE_EDGES = (
    (
        "runtime/contracts/emotion_pattern_contracts.py",
        "runtime/__init__.py",
        "python_import",
    ),
    (
        "runtime/contracts/emotion_pattern_contracts.py",
        "runtime/contracts/__init__.py",
        "python_import",
    ),
    (
        "runtime/contracts/emotion_pattern_contracts.py",
        "runtime/contracts/emotion_state_contracts.py",
        "python_import",
    ),
    (
        "runtime/contracts/emotion_state_brain_extension.py",
        "runtime/__init__.py",
        "python_import",
    ),
    (
        "runtime/contracts/emotion_state_brain_extension.py",
        "runtime/contracts/__init__.py",
        "python_import",
    ),
    (
        "runtime/contracts/emotion_state_brain_extension.py",
        "runtime/contracts/emotion_state_contracts.py",
        "python_import",
    ),
    (
        "scripts/build_emotion_state_public_dataset_manifests.py",
        "scripts/emotion_state_public_dataset_contracts.py",
        "python_import",
    ),
    (
        "scripts/check_project_drift.py",
        "scripts/emotion_state_phase_a_verification_evidence.py",
        "python_import",
    ),
    (
        "scripts/check_setup.py",
        "scripts/emotion_state_phase_a_verification_evidence.py",
        "python_import",
    ),
    (
        "scripts/emotion_state_cohort_release_contracts.py",
        "runtime/__init__.py",
        "python_import",
    ),
    (
        "scripts/emotion_state_cohort_release_contracts.py",
        "runtime/contracts/__init__.py",
        "python_import",
    ),
    (
        "scripts/emotion_state_cohort_release_contracts.py",
        "runtime/contracts/emotion_pattern_contracts.py",
        "python_import",
    ),
    (
        "scripts/emotion_state_cohort_release_contracts.py",
        "runtime/contracts/emotion_state_contracts.py",
        "python_import",
    ),
    (
        "scripts/emotion_state_cohort_release_contracts.py",
        "scripts/emotion_state_public_dataset_contracts.py",
        "python_import",
    ),
    (
        "scripts/emotion_state_phase_a_contracts.py",
        "runtime/__init__.py",
        "python_import",
    ),
    (
        "scripts/emotion_state_phase_a_contracts.py",
        "runtime/contracts/__init__.py",
        "python_import",
    ),
    (
        "scripts/emotion_state_phase_a_contracts.py",
        "runtime/contracts/emotion_pattern_contracts.py",
        "python_import",
    ),
    (
        "scripts/emotion_state_phase_a_contracts.py",
        "runtime/contracts/emotion_state_brain_extension.py",
        "python_import",
    ),
    (
        "scripts/emotion_state_phase_a_contracts.py",
        "runtime/contracts/emotion_state_contracts.py",
        "python_import",
    ),
    (
        "scripts/emotion_state_phase_a_contracts.py",
        "scripts/emotion_state_annotation_contracts.py",
        "python_import",
    ),
    (
        "scripts/emotion_state_phase_a_contracts.py",
        "scripts/emotion_state_cohort_release_contracts.py",
        "python_import",
    ),
    (
        "scripts/emotion_state_phase_a_contracts.py",
        "scripts/emotion_state_phase_a_verification_evidence.py",
        "python_import",
    ),
    (
        "scripts/emotion_state_phase_a_contracts.py",
        "scripts/emotion_state_public_dataset_contracts.py",
        "python_import",
    ),
    (
        "scripts/emotion_state_phase_a_contracts.py",
        "scripts/emotion_state_split_manifest_v2_contracts.py",
        "python_import",
    ),
    (
        "scripts/emotion_state_phase_a_contracts.py",
        "scripts/exp_002_frozen_response_baseline.py",
        "python_import",
    ),
    (
        "scripts/emotion_state_split_manifest_v2_contracts.py",
        "scripts/emotion_state_public_dataset_contracts.py",
        "python_import",
    ),
    (
        "scripts/run_brain_002_runtime_state_schema.py",
        "runtime/__init__.py",
        "python_import",
    ),
    (
        "scripts/run_brain_002_runtime_state_schema.py",
        "runtime/contracts/__init__.py",
        "python_import",
    ),
    (
        "scripts/run_brain_002_runtime_state_schema.py",
        "runtime/contracts/brain_runtime_state_schema.py",
        "python_import",
    ),
    (
        "scripts/run_emotion_state_001_phase_a_contracts.py",
        "scripts/emotion_state_phase_a_contracts.py",
        "python_import",
    ),
    (
        "scripts/run_emotion_state_001_phase_a_contracts.py",
        "scripts/emotion_state_phase_a_verification_evidence.py",
        "python_import",
    ),
    (
        "scripts/run_exp_002_frozen_response_baseline.py",
        "scripts/exp_002_frozen_response_baseline.py",
        "python_import",
    ),
    (
        "scripts/test_emotion_state_001_closeout_hardening.py",
        "scripts/check_project_drift.py",
        "python_import",
    ),
    (
        "scripts/test_emotion_state_001_closeout_hardening.py",
        "scripts/emotion_state_phase_a_contracts.py",
        "python_import",
    ),
    (
        "scripts/test_emotion_state_001_closeout_hardening.py",
        "scripts/emotion_state_phase_a_verification_evidence.py",
        "python_import",
    ),
    (
        "scripts/test_emotion_state_001_closeout_hardening.py",
        "scripts/run_brain_002_runtime_state_schema.py",
        "python_import",
    ),
    (
        "scripts/test_emotion_state_001_closeout_hardening.py",
        "scripts/run_emotion_state_001_phase_a_contracts.py",
        "python_import",
    ),
    (
        "scripts/test_emotion_state_001_closeout_hardening.py",
        "scripts/run_exp_002_frozen_response_baseline.py",
        "python_import",
    ),
    (
        "scripts/test_emotion_state_001_closeout_hardening.py",
        "scripts/validate_emotion_state_001_phase_a_contracts.py",
        "python_import",
    ),
    (
        "scripts/test_emotion_state_001_closeout_hardening.py",
        "scripts/validate_exp_002_frozen_response_baseline.py",
        "python_import",
    ),
    (
        "scripts/test_emotion_state_001_open_dataset_gate.py",
        "runtime/__init__.py",
        "python_import",
    ),
    (
        "scripts/test_emotion_state_001_open_dataset_gate.py",
        "runtime/contracts/__init__.py",
        "python_import",
    ),
    (
        "scripts/test_emotion_state_001_open_dataset_gate.py",
        "runtime/contracts/emotion_pattern_contracts.py",
        "python_import",
    ),
    (
        "scripts/test_emotion_state_001_open_dataset_gate.py",
        "runtime/contracts/emotion_state_contracts.py",
        "python_import",
    ),
    (
        "scripts/test_emotion_state_001_open_dataset_gate.py",
        "scripts/build_emotion_state_public_dataset_manifests.py",
        "python_import",
    ),
    (
        "scripts/test_emotion_state_001_open_dataset_gate.py",
        "scripts/check_project_drift.py",
        "python_import",
    ),
    (
        "scripts/test_emotion_state_001_open_dataset_gate.py",
        "scripts/check_setup.py",
        "python_import",
    ),
    (
        "scripts/test_emotion_state_001_open_dataset_gate.py",
        "scripts/check_thesis_reference_registry.py",
        "python_import",
    ),
    (
        "scripts/test_emotion_state_001_open_dataset_gate.py",
        "scripts/emotion_state_cohort_release_contracts.py",
        "python_import",
    ),
    (
        "scripts/test_emotion_state_001_open_dataset_gate.py",
        "scripts/emotion_state_phase_a_contracts.py",
        "python_import",
    ),
    (
        "scripts/test_emotion_state_001_open_dataset_gate.py",
        "scripts/emotion_state_phase_a_verification_evidence.py",
        "python_import",
    ),
    (
        "scripts/test_emotion_state_001_open_dataset_gate.py",
        "scripts/emotion_state_public_dataset_contracts.py",
        "python_import",
    ),
    (
        "scripts/test_emotion_state_001_open_dataset_gate.py",
        "scripts/emotion_state_split_manifest_v2_contracts.py",
        "python_import",
    ),
    (
        "scripts/test_emotion_state_001_open_dataset_gate.py",
        "scripts/run_emotion_state_001_phase_a_contracts.py",
        "python_import",
    ),
    (
        "scripts/test_emotion_state_001_open_dataset_gate.py",
        "scripts/test_emotion_state_001_closeout_hardening.py",
        "python_import",
    ),
    (
        "scripts/test_emotion_state_001_open_dataset_gate.py",
        "scripts/validate_emotion_state_001_phase_a_contracts.py",
        "python_import",
    ),
    (
        "scripts/test_emotion_state_001_open_dataset_gate.py",
        "scripts/validate_private_data_boundary.py",
        "python_import",
    ),
    (
        "scripts/validate_check_setup.py",
        "scripts/check_setup.py",
        "python_import",
    ),
    (
        "scripts/validate_emotion_state_001_phase_a_contracts.py",
        "runtime/__init__.py",
        "python_import",
    ),
    (
        "scripts/validate_emotion_state_001_phase_a_contracts.py",
        "runtime/contracts/__init__.py",
        "python_import",
    ),
    (
        "scripts/validate_emotion_state_001_phase_a_contracts.py",
        "runtime/contracts/emotion_pattern_contracts.py",
        "python_import",
    ),
    (
        "scripts/validate_emotion_state_001_phase_a_contracts.py",
        "runtime/contracts/emotion_state_brain_extension.py",
        "python_import",
    ),
    (
        "scripts/validate_emotion_state_001_phase_a_contracts.py",
        "runtime/contracts/emotion_state_contracts.py",
        "python_import",
    ),
    (
        "scripts/validate_emotion_state_001_phase_a_contracts.py",
        "scripts/build_emotion_state_public_dataset_manifests.py",
        "python_import",
    ),
    (
        "scripts/validate_emotion_state_001_phase_a_contracts.py",
        "scripts/emotion_state_annotation_contracts.py",
        "python_import",
    ),
    (
        "scripts/validate_emotion_state_001_phase_a_contracts.py",
        "scripts/emotion_state_cohort_release_contracts.py",
        "python_import",
    ),
    (
        "scripts/validate_emotion_state_001_phase_a_contracts.py",
        "scripts/emotion_state_phase_a_contracts.py",
        "python_import",
    ),
    (
        "scripts/validate_emotion_state_001_phase_a_contracts.py",
        "scripts/emotion_state_public_dataset_contracts.py",
        "python_import",
    ),
    (
        "scripts/validate_emotion_state_001_phase_a_contracts.py",
        "scripts/emotion_state_split_manifest_v2_contracts.py",
        "python_import",
    ),
    (
        "scripts/validate_emotion_state_001_phase_a_contracts.py",
        "scripts/run_emotion_state_001_phase_a_contracts.py",
        "python_import",
    ),
    (
        "scripts/validate_emotion_state_001_phase_a_contracts.py",
        "scripts/validate_brain_002_runtime_state_schema.py",
        "python_subprocess_target",
    ),
    (
        "scripts/validate_emotion_state_001_phase_a_contracts.py",
        "scripts/validate_exp_002_frozen_response_baseline.py",
        "python_subprocess_target",
    ),
    (
        "scripts/validate_exp_002_frozen_response_baseline.py",
        "scripts/exp_002_frozen_response_baseline.py",
        "python_import",
    ),
    (
        "scripts/validate_exp_002_frozen_response_baseline.py",
        "scripts/run_exp_002_frozen_response_baseline.py",
        "python_subprocess_target",
    ),
    (
        "scripts/validate_exp_002_frozen_response_baseline.py",
        "scripts/run_prompt_baseline.py",
        "python_subprocess_target",
    ),
    (
        "scripts/validate_private_data_boundary.py",
        "scripts/emotion_state_phase_a_verification_evidence.py",
        "python_import",
    ),
    (
        "scripts/validate_project_drift_guard.py",
        "scripts/check_project_drift.py",
        "python_import",
    ),
)

EXPECTED_CASE = {
    "checkpoint_id": "EMOTION-STATE-001-phase-a-contracts",
    "schema_version": 2,
    "source_label": "public-only",
    "campaign_profile_id": "emotion-state-phase-a-fixture",
    "campaign_profile_version": "fixture-v2",
    "selected_public_datasets": list(SELECTED_PUBLIC_DATASET_IDS),
    "dataset_download_authorized": True,
    "dataset_evaluation_started": False,
    "private_data_access_allowed": False,
    "provider_operations_allowed": False,
    "runtime_behavior_change_allowed": False,
    "runtime_activation_allowed": False,
    "baseline_fingerprints": EXPECTED_BASELINE_FINGERPRINTS,
}

MATERIAL_FIELDS = (
    "copied_material",
    "translated_material",
    "adapted_material",
    "independently_reimplemented_material",
)
EXPECTED_REVIEWED_FILES = [
    {
        "path": "README.md",
        "git_blob_sha1": "f8a1afe3842b361432d8dcc061c5c5b6969cf363",
        "equivalence_status": "byte_identical_to_dev_blob",
        "reuse_status": "reference_only",
    },
    {
        "path": "docs/features/FEATURE_speech_call_readiness_analytics.md",
        "git_blob_sha1": "b5e63a3dd9ba72f5eefc46688129aa98bf20a509",
        "equivalence_status": "byte_identical_to_dev_blob",
        "reuse_status": "reference_only",
    },
    {
        "path": "docs/features/FEATURE_speech_prosody.md",
        "git_blob_sha1": "5d5cbd7e25dc7bce5fcf2c7fcb97448524c79f22",
        "equivalence_status": "byte_identical_to_dev_blob",
        "reuse_status": "reference_only",
    },
    {
        "path": "docs/features/FEATURE_speech_turn_dynamics.md",
        "git_blob_sha1": "03f737ce52262fcac733016ec57f344d783a69b4",
        "equivalence_status": "byte_identical_to_dev_blob",
        "reuse_status": "reference_only",
    },
    {
        "path": "src/aggregation/speech_call_readiness.py",
        "git_blob_sha1": "8387ae5d365d22c816e407e315701a066e745599",
        "equivalence_status": "byte_identical_to_dev_blob",
        "reuse_status": "excluded_from_emotion_labels",
    },
    {
        "path": "src/features/temporal/speech_prosody.py",
        "git_blob_sha1": "dbadd19160affcd3aec864a9f4b77d3ed5e5a4d6",
        "equivalence_status": "byte_identical_to_dev_blob",
        "reuse_status": "reference_only",
    },
    {
        "path": "src/features/temporal/speech_turn_dynamics.py",
        "git_blob_sha1": "4a46634ca9531e5181f72a554545083defcff59d",
        "equivalence_status": "byte_identical_to_dev_blob",
        "reuse_status": "reference_only",
    },
]


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"unable to read valid JSON: {path.name}") from exc


def sha256_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest().upper()
    except OSError as exc:
        raise ValueError(f"unable to fingerprint frozen baseline artifact: {path.name}") from exc


def validate_phase_a_case(case: Any) -> None:
    if not isinstance(case, dict):
        raise ValueError("Phase A case must be a JSON object")
    if set(case) != set(EXPECTED_CASE):
        raise ValueError("invalid Phase A case fields")
    if type(case.get("schema_version")) is not int:
        raise ValueError("invalid Phase A case schema version")
    for field in (
        "dataset_download_authorized",
        "dataset_evaluation_started",
        "private_data_access_allowed",
        "provider_operations_allowed",
        "runtime_behavior_change_allowed",
        "runtime_activation_allowed",
    ):
        if type(case.get(field)) is not bool:
            raise ValueError(f"invalid Phase A case boolean: {field}")
    mismatched = {
        key: case.get(key)
        for key, value in EXPECTED_CASE.items()
        if case.get(key) != value
    }
    if mismatched:
        raise ValueError(f"invalid Phase A case boundary: {sorted(mismatched)}")


def validate_source_manifest(manifest: Any) -> None:
    if not isinstance(manifest, dict):
        raise ValueError("source manifest must be a JSON object")
    expected_values = {
        "archive_sha256": EXPECTED_ARCHIVE_SHA256,
        "source_repository_url": "https://github.com/WisdomBreathes/creative-analysis-engine",
        "source_repository_url_status": "verified_read_only",
        "source_branch": "dev",
        "source_revision": "7cb99ea2da3016cd82d0b5f805c015a808ce4e0d",
        "source_revision_status": "verified_read_only",
        "observed_license": None,
        "observed_license_status": "absent_in_reviewed_root",
    }
    expected_booleans = {
        "runtime_dependency_added": False,
        "project_local_only": True,
    }
    required_fields = (
        set(expected_values)
        | set(expected_booleans)
        | set(MATERIAL_FIELDS)
        | {"adaptation_allowed", "phase_b_approval", "reviewed_files"}
    )
    missing_fields = sorted(required_fields - set(manifest))
    if missing_fields:
        raise ValueError(f"missing source manifest fields: {missing_fields}")
    mismatched = {
        key: manifest.get(key)
        for key, value in expected_values.items()
        if manifest.get(key) != value
    }
    if mismatched:
        raise ValueError(f"invalid source manifest boundary: {sorted(mismatched)}")
    if manifest["reviewed_files"] != EXPECTED_REVIEWED_FILES:
        raise ValueError("invalid source manifest reviewed-file provenance")
    if manifest["adaptation_allowed"] is not False:
        raise ValueError("source adaptation must remain blocked by the current instruction")
    if manifest["phase_b_approval"]["approved"] is not False:
        raise ValueError("Phase B source reuse approval must remain false")
    for field, expected in expected_booleans.items():
        value = manifest.get(field)
        if type(value) is not bool or value is not expected:
            raise ValueError(f"invalid source manifest boolean: {field}")
    for field in MATERIAL_FIELDS:
        value = manifest.get(field)
        if not isinstance(value, list):
            raise ValueError(f"invalid source manifest material field: {field}")
        if value:
            raise ValueError("source adaptation must remain blocked")


def determine_phase_a_completion(evidence: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(evidence, Mapping):
        raise ValueError("Phase A completion evidence must be an object")
    derived_fields = {
        "phase_a_complete",
        "repository_gate_statuses",
        "guarded_command_results",
    }
    supplied_derived_fields = derived_fields.intersection(evidence)
    if supplied_derived_fields:
        raise ValueError(
            "Phase A completion evidence fields are derived-only: "
            + ", ".join(sorted(supplied_derived_fields))
        )
    common_fields = {
        "mode",
        "selected_dataset_ids",
        "dataset_download_authorized",
        "dataset_evidence",
        "contract_statuses",
    }
    if not common_fields.issubset(evidence):
        raise ValueError("invalid Phase A completion evidence fields")
    mode = evidence.get("mode")
    if not isinstance(mode, str) or mode not in {"material_pending", "complete"}:
        raise ValueError("invalid Phase A completion mode")
    complete_fields = common_fields | {
        "verification_evidence",
        "executed_command_ledger",
        "publication_integrity_preconditions",
        "authorization_boundaries",
    }
    expected_fields = common_fields if mode == "material_pending" else complete_fields
    if set(evidence) != expected_fields:
        raise ValueError("invalid Phase A completion evidence fields")
    if evidence["selected_dataset_ids"] != list(SELECTED_PUBLIC_DATASET_IDS):
        raise ValueError("selected public dataset IDs or order changed")
    download_authorized = evidence["dataset_download_authorized"]
    if type(download_authorized) is not bool:
        raise ValueError("dataset_download_authorized must be boolean")
    dataset_evidence = evidence["dataset_evidence"]
    if not isinstance(dataset_evidence, list):
        raise ValueError("dataset_evidence must be a list")
    contract_statuses = evidence["contract_statuses"]
    if not isinstance(contract_statuses, Mapping):
        raise ValueError("contract_statuses must be an object")
    if mode == "material_pending":
        if dict(contract_statuses) != MATERIAL_PENDING_CONTRACT_STATUSES:
            raise ValueError("offline material-pending contract checks must all pass")
        if download_authorized is not False:
            raise ValueError("material-pending mode requires download authorization false")
        if dataset_evidence:
            raise ValueError("material-pending mode requires zero dataset-evidence entries")
        blockers = list(MATERIAL_PENDING_BLOCKERS)
        completion_scope = MATERIAL_PENDING_COMPLETION_SCOPE
        phase_a_complete = False
        repository_gate_complete = False
    else:
        blockers = []
        if not download_authorized:
            blockers.append("dataset_download_not_authorized")

        expected_dataset_fields = {
            "dataset_id",
            "completion_status",
            "manifest_sha256",
            "hash_inventory_sha256",
            "quality_inventory_sha256",
            "source_provenance_status",
            "material_validation_status",
        }
        dataset_evidence_valid = (
            len(dataset_evidence) == len(SELECTED_PUBLIC_DATASET_IDS)
        )
        if dataset_evidence_valid:
            for expected_dataset_id, dataset_entry in zip(
                SELECTED_PUBLIC_DATASET_IDS,
                dataset_evidence,
                strict=True,
            ):
                if (
                    not isinstance(dataset_entry, Mapping)
                    or set(dataset_entry) != expected_dataset_fields
                    or dataset_entry.get("dataset_id") != expected_dataset_id
                    or dataset_entry.get("completion_status") != "verified"
                    or dataset_entry.get("source_provenance_status") != "pass"
                    or dataset_entry.get("material_validation_status") != "pass"
                ):
                    dataset_evidence_valid = False
                    break
                for digest_field in (
                    "manifest_sha256",
                    "hash_inventory_sha256",
                    "quality_inventory_sha256",
                ):
                    digest = dataset_entry.get(digest_field)
                    if (
                        not isinstance(digest, str)
                        or re.fullmatch(r"[0-9A-F]{64}", digest) is None
                    ):
                        dataset_evidence_valid = False
                        break
                if not dataset_evidence_valid:
                    break
        if not dataset_evidence_valid:
            blockers.append("selected_dataset_manifests_not_verified")

        if (
            set(contract_statuses) != set(MATERIAL_PENDING_CONTRACT_STATUSES)
            or any(
                contract_statuses.get(field) != "pass"
                for field in MATERIAL_PENDING_CONTRACT_STATUSES
            )
        ):
            blockers.append("offline_contract_checks_not_verified")

        verification_evidence = evidence["verification_evidence"]
        verification_mapping = (
            verification_evidence
            if isinstance(verification_evidence, Mapping)
            else {}
        )
        expected_verification_fields = {
            "implementation_baseline_commit",
            "repository_head_commit",
            "verification_run_id",
            "verification_input_path_inventory_digest",
            "executable_dependency_closure_digest",
            "executed_command_ledger_digest",
            "guard_policy_digest",
            "verification_input_tree_digest",
            "provider_environment_scrubbed",
            "private_path_guard_enabled",
            "network_guard_enabled",
            "prepublication_byte_lock_reread_status",
        }
        verification_valid = (
            isinstance(verification_evidence, Mapping)
            and set(verification_evidence) == expected_verification_fields
        )
        if verification_valid:
            for commit_field in (
                "implementation_baseline_commit",
                "repository_head_commit",
            ):
                commit = verification_evidence.get(commit_field)
                if (
                    not isinstance(commit, str)
                    or re.fullmatch(r"[0-9a-f]{40}", commit) is None
                ):
                    verification_valid = False
            for digest_field in (
                "verification_run_id",
                "verification_input_path_inventory_digest",
                "executable_dependency_closure_digest",
                "executed_command_ledger_digest",
                "guard_policy_digest",
                "verification_input_tree_digest",
            ):
                digest = verification_evidence.get(digest_field)
                if (
                    not isinstance(digest, str)
                    or re.fullmatch(r"[0-9A-F]{64}", digest) is None
                ):
                    verification_valid = False
            for guard_field in (
                "provider_environment_scrubbed",
                "private_path_guard_enabled",
                "network_guard_enabled",
            ):
                if verification_evidence.get(guard_field) is not True:
                    verification_valid = False
            if (
                verification_evidence.get(
                    "prepublication_byte_lock_reread_status"
                )
                != "pass"
            ):
                verification_valid = False
        if not verification_valid:
            blockers.append("verification_evidence_not_verified")

        repository_gate_complete = False
        try:
            from scripts.emotion_state_phase_a_verification_evidence import (
                REPOSITORY_GATE_COMMAND_IDS,
                derive_repository_gate_statuses,
            )

            repository_gate_statuses = derive_repository_gate_statuses(
                evidence["executed_command_ledger"],
                "complete",
                baseline_commit=verification_mapping.get(
                    "implementation_baseline_commit"
                ),
                head_commit=verification_mapping.get("repository_head_commit"),
            )
            repository_gate_complete = (
                tuple(repository_gate_statuses)
                == tuple(REPOSITORY_GATE_COMMAND_IDS)
                and all(
                    status == "pass"
                    for status in repository_gate_statuses.values()
                )
            )
        except (TypeError, ValueError):
            repository_gate_complete = False
        if not repository_gate_complete:
            blockers.append("repository_gates_not_verified")

        publication_preconditions = evidence["publication_integrity_preconditions"]
        if (
            not isinstance(publication_preconditions, Mapping)
            or set(publication_preconditions)
            != {
                "crash_safe_pair_protocol_status",
                "explicit_acceptance_transaction_status",
                "last_valid_pair_preservation_status",
                "output_self_reference_absent",
            }
            or publication_preconditions.get("crash_safe_pair_protocol_status")
            != "pass"
            or publication_preconditions.get(
                "explicit_acceptance_transaction_status"
            )
            != "pass"
            or publication_preconditions.get(
                "last_valid_pair_preservation_status"
            )
            != "pass"
            or publication_preconditions.get("output_self_reference_absent")
            is not True
        ):
            blockers.append("publication_integrity_preconditions_not_verified")

        authorization_boundaries = evidence["authorization_boundaries"]
        expected_authorization_fields = {
            "live_aggregate_release_unblocked",
            "public_dataset_evaluation_unblocked",
            "phase_b_unblocked",
            "private_research_unblocked",
            "provider_feasibility_unblocked",
            "runtime_activation_unblocked",
        }
        if (
            not isinstance(authorization_boundaries, Mapping)
            or set(authorization_boundaries) != expected_authorization_fields
            or any(
                authorization_boundaries.get(field) is not False
                for field in expected_authorization_fields
            )
        ):
            blockers.append("authorization_boundaries_not_closed")

        completion_scope = COMPLETE_PHASE_A_COMPLETION_SCOPE
        phase_a_complete = not blockers

    return {
        "phase_a_contract_artifacts_built": True,
        "phase_a_complete": phase_a_complete,
        "phase_a_completion_scope": completion_scope,
        "full_repository_gate_claimed_by_this_artifact": (
            repository_gate_complete
        ),
        "live_aggregate_release_unblocked": False,
        "phase_b_unblocked": False,
        "public_dataset_evaluation_unblocked": False,
        "private_research_unblocked": False,
        "provider_feasibility_unblocked": False,
        "runtime_activation_unblocked": False,
        "blocking_reason_codes": blockers,
    }


def _normalized_verification_evidence(
    verification_evidence: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if verification_evidence is None:
        return {}
    if not isinstance(verification_evidence, Mapping):
        raise ValueError("verification evidence must be an object")
    try:
        encoded = json.dumps(
            dict(verification_evidence),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        normalized = json.loads(encoded)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("verification evidence must be canonical JSON") from exc
    if not isinstance(normalized, dict):
        raise ValueError("verification evidence must normalize to an object")
    return normalized


def _load_complete_dataset_evidence(
    root: Path,
) -> tuple[
    list[dict[str, Any]],
    dict[str, str],
    dict[str, str],
]:
    """Read and byte-bind the exact ordered tracked public-dataset evidence."""

    from scripts.emotion_state_public_dataset_contracts import (
        validate_dataset_manifest,
    )

    dataset_evidence: list[dict[str, Any]] = []
    hash_inventory_digests: dict[str, str] = {}
    quality_inventory_digests: dict[str, str] = {}
    evidence_root = root / DATASET_EVIDENCE_DIRECTORY
    for dataset_id in SELECTED_PUBLIC_DATASET_IDS:
        manifest_path = evidence_root / f"{dataset_id}.manifest.json"
        hash_inventory_path = evidence_root / f"{dataset_id}.hashes.json"
        quality_inventory_path = evidence_root / f"{dataset_id}.quality.json"
        manifest = read_json(manifest_path)
        hash_inventory = read_json(hash_inventory_path)
        quality_inventory = read_json(quality_inventory_path)
        validate_dataset_manifest(manifest)
        if (
            hash_inventory.get("dataset_id") != dataset_id
            or quality_inventory.get("dataset_id") != dataset_id
        ):
            raise ValueError("dataset evidence identity mismatch")
        manifest_sha256 = sha256_file(manifest_path)
        hash_inventory_sha256 = sha256_file(hash_inventory_path)
        quality_inventory_sha256 = sha256_file(quality_inventory_path)
        if (
            manifest.get("completion_status") != "verified"
            or manifest.get("hash_inventory", {}).get("inventory_sha256")
            != hash_inventory_sha256
            or manifest.get("exclusion_inventory", {}).get(
                "quality_inventory_sha256"
            )
            != quality_inventory_sha256
            or manifest.get("hash_inventory", {}).get("selected_file_count")
            != hash_inventory.get("selected_file_count")
            or manifest.get("hash_inventory", {}).get("selected_byte_count")
            != hash_inventory.get("selected_byte_count")
            or manifest.get("exclusion_inventory", {}).get(
                "included_file_count"
            )
            != quality_inventory.get("included_file_count")
            or manifest.get("exclusion_inventory", {}).get(
                "excluded_file_count"
            )
            != quality_inventory.get("excluded_file_count")
        ):
            raise ValueError("dataset evidence bytes do not match manifest references")
        dataset_evidence.append({
            "dataset_id": dataset_id,
            "completion_status": "verified",
            "manifest_sha256": manifest_sha256,
            "hash_inventory_sha256": hash_inventory_sha256,
            "quality_inventory_sha256": quality_inventory_sha256,
            "source_provenance_status": "pass",
            "material_validation_status": "pass",
        })
        hash_inventory_digests[dataset_id] = hash_inventory_sha256
        quality_inventory_digests[dataset_id] = quality_inventory_sha256
    return (
        dataset_evidence,
        hash_inventory_digests,
        quality_inventory_digests,
    )


def _assert_exact_json_value(
    actual: Any,
    expected: Any,
    *,
    location: str,
) -> None:
    if type(actual) is not type(expected):
        raise ValueError(f"{location} has the wrong type")
    if isinstance(expected, dict):
        if set(actual) != set(expected):
            raise ValueError(f"{location} has the wrong fields")
        for key, expected_value in expected.items():
            _assert_exact_json_value(
                actual[key],
                expected_value,
                location=f"{location}.{key}",
            )
        return
    if isinstance(expected, list):
        if len(actual) != len(expected):
            raise ValueError(f"{location} has the wrong item count")
        for index, (actual_value, expected_value) in enumerate(
            zip(actual, expected, strict=True)
        ):
            _assert_exact_json_value(
                actual_value,
                expected_value,
                location=f"{location}[{index}]",
            )
        return
    if actual != expected:
        raise ValueError(f"{location} has the wrong value")


def _validate_upper_sha256(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9A-F]{64}", value) is None:
        raise ValueError(f"{field} must be uppercase SHA-256 hexadecimal")
    return value


def _validate_lower_commit(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{40}", value) is None:
        raise ValueError(f"{field} must be lowercase 40-hex")
    return value


def _validate_evidence_path(value: Any, *, field: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or "\x00" in value
        or "\\" in value
        or PureWindowsPath(value).drive
        or PureWindowsPath(value).root
    ):
        raise ValueError(f"{field} must be a relative repository path")
    normalized = PurePosixPath(value.replace("\\", "/"))
    if normalized.is_absolute() or ".." in normalized.parts or normalized.as_posix() == ".":
        raise ValueError(f"{field} must be a relative repository path")
    normalized_text = normalized.as_posix()
    if value != normalized_text:
        raise ValueError(f"{field} must be a canonical POSIX repository path")
    folded_parts = tuple(part.casefold() for part in normalized.parts)
    folded_text = normalized_text.casefold()
    if (
        any(
            folded_parts[: len(prefix)] == prefix
            for prefix in MATERIAL_PENDING_EXCLUDED_PATH_PREFIXES
        )
        or folded_text in {
            path.casefold()
            for path in VERIFICATION_OUTPUT_EXCLUSIONS
        }
        or folded_text == VERIFICATION_RECOVERY_PREFIX.casefold()
        or folded_text.startswith(VERIFICATION_RECOVERY_PREFIX.casefold() + "/")
    ):
        raise ValueError(f"{field} targets an excluded verification path")
    return normalized_text


def _validate_exact_inventory_scope(
    actual_paths: set[str],
    *,
    expected_paths: tuple[str, ...],
    field: str,
) -> None:
    expected_set = set(expected_paths)
    expected_casefolded = {path.casefold() for path in expected_paths}
    if (
        tuple(sorted(expected_paths)) != expected_paths
        or len(expected_set) != len(expected_paths)
        or len(expected_casefolded) != len(expected_paths)
    ):
        raise ValueError(f"{field} expected scope is not canonical")
    if actual_paths != expected_set:
        raise ValueError(
            f"{field} must match the exact authorized Tasks 1-7 scope"
        )


def _validate_byte_inventory(
    value: Any,
    *,
    field: str,
    include_git_state: bool,
) -> set[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    expected_fields = {"path", "git_mode", "sha256"}
    if include_git_state:
        expected_fields.add("git_state")
    normalized_order: list[tuple[str, ...]] = []
    for index, entry in enumerate(value):
        if not isinstance(entry, dict) or set(entry) != expected_fields:
            raise ValueError(f"{field}[{index}] has the wrong fields")
        path = _validate_evidence_path(
            entry["path"],
            field=f"{field}[{index}].path",
        )
        if (
            not isinstance(entry["git_mode"], str)
            or re.fullmatch(r"[0-7]{6}", entry["git_mode"]) is None
        ):
            raise ValueError(f"{field}[{index}].git_mode is invalid")
        _validate_upper_sha256(
            entry["sha256"],
            field=f"{field}[{index}].sha256",
        )
        if include_git_state:
            if (
                not isinstance(entry["git_state"], str)
                or entry["git_state"] not in {"staged", "unstaged", "untracked"}
            ):
                raise ValueError(f"{field}[{index}].git_state is invalid")
            normalized_order.append((path, entry["git_state"]))
        else:
            normalized_order.append((path,))
    if normalized_order != sorted(set(normalized_order)):
        raise ValueError(f"{field} must be unique and sorted")
    return {entry[0] for entry in normalized_order}


def _validate_closure_edges(value: Any) -> list[tuple[str, str, str]]:
    if not isinstance(value, list):
        raise ValueError("executable_dependency_closure_edges must be a list")
    normalized_order: list[tuple[str, str, str]] = []
    for index, edge in enumerate(value):
        if not isinstance(edge, dict) or set(edge) != {
            "consumer",
            "dependency",
            "edge_type",
        }:
            raise ValueError(f"closure edge {index} has the wrong fields")
        consumer = _validate_evidence_path(
            edge["consumer"],
            field=f"closure edge {index} consumer",
        )
        dependency = _validate_evidence_path(
            edge["dependency"],
            field=f"closure edge {index} dependency",
        )
        edge_type = edge["edge_type"]
        if (
            not isinstance(edge_type, str)
            or edge_type not in {"python_import", "python_subprocess_target"}
        ):
            raise ValueError(f"closure edge {index} has an invalid edge type")
        normalized_order.append((consumer, dependency, edge_type))
    if normalized_order != sorted(set(normalized_order)):
        raise ValueError("executable dependency closure edges must be unique and sorted")
    return normalized_order


def _validate_exact_closure_edge_scope(
    actual_edges: list[tuple[str, str, str]],
) -> None:
    expected_edges = TASKS_1_7_CLOSURE_EDGES
    closure_paths = set(TASKS_1_7_CLOSURE_PATHS)
    if (
        tuple(sorted(expected_edges)) != expected_edges
        or len(set(expected_edges)) != len(expected_edges)
        or any(
            consumer not in closure_paths
            or dependency not in closure_paths
            or edge_type not in {
                "python_import",
                "python_subprocess_target",
            }
            for consumer, dependency, edge_type in expected_edges
        )
    ):
        raise ValueError(
            "executable dependency closure expected edge scope is not canonical"
        )
    if tuple(actual_edges) != expected_edges:
        raise ValueError(
            "executable dependency closure edges must match the exact "
            "authorized Tasks 1-7 closure"
        )


def validate_material_pending_payload(payload: Any) -> dict[str, Any]:
    """Purely validate the exact accepted material-pending checkpoint contract."""

    if not isinstance(payload, dict):
        raise ValueError("material-pending payload must be an object")
    expected_fields = MATERIAL_PENDING_PAYLOAD_FIELDS | VERIFICATION_EVIDENCE_FIELDS
    if set(payload) != expected_fields or len(payload) != 35:
        raise ValueError("material-pending payload must contain exactly 35 owned fields")

    _assert_exact_json_value(
        {
            "checkpoint_id": payload["checkpoint_id"],
            "schema_version": payload["schema_version"],
            "mode": payload["mode"],
            "status": payload["status"],
            "selected_public_datasets": payload["selected_public_datasets"],
            "dataset_download_authorized": payload["dataset_download_authorized"],
            "dataset_evaluation_started": payload["dataset_evaluation_started"],
            "dataset_manifest_evidence": payload["dataset_manifest_evidence"],
            "source_pin": payload["source_pin"],
            "contract_checks": payload["contract_checks"],
            "blocking_reason_codes": payload["blocking_reason_codes"],
            "summary": payload["summary"],
            "archive_sha256": payload["archive_sha256"],
            "baseline_fingerprints": payload["baseline_fingerprints"],
            "readiness_boundary": payload["readiness_boundary"],
        },
        {
            "checkpoint_id": "EMOTION-STATE-001-phase-a-contracts",
            "schema_version": 2,
            "mode": "material_pending",
            "status": "material_pending",
            "selected_public_datasets": list(SELECTED_PUBLIC_DATASET_IDS),
            "dataset_download_authorized": False,
            "dataset_evaluation_started": False,
            "dataset_manifest_evidence": [],
            "source_pin": {
                "source_repository_url": (
                    "https://github.com/WisdomBreathes/creative-analysis-engine"
                ),
                "source_branch": "dev",
                "source_revision": "7cb99ea2da3016cd82d0b5f805c015a808ce4e0d",
                "archive_sha256": EXPECTED_ARCHIVE_SHA256,
                "source_adaptation_allowed": False,
                "code_adaptation_started": False,
            },
            "contract_checks": EXPECTED_CONTRACT_CHECKS,
            "blocking_reason_codes": list(MATERIAL_PENDING_BLOCKERS),
            "summary": {
                "contract_check_count": len(EXPECTED_CONTRACT_CHECKS),
                "contract_checks": EXPECTED_CONTRACT_CHECKS,
                "baseline_fingerprint_count": len(EXPECTED_BASELINE_FINGERPRINTS),
                "selected_public_dataset_count": len(SELECTED_PUBLIC_DATASET_IDS),
                "dataset_download_authorized": False,
                "dataset_evaluation_started": False,
                "material_verification_status": "pending",
                "source_repository_url_status": "verified_read_only",
                "source_adaptation_allowed": False,
                "code_adaptation_started": False,
                "frozen_exp_002_evaluator_provenance_status": "not_recorded",
                "provider_operations_performed_by_runner": False,
                "private_data_read_by_runner": False,
                "runtime_behavior_changed_by_runner": False,
                "runtime_activation_allowed": False,
            },
            "archive_sha256": EXPECTED_ARCHIVE_SHA256,
            "baseline_fingerprints": EXPECTED_BASELINE_FINGERPRINTS,
            "readiness_boundary": {
                "phase_a_contract_artifacts_built": True,
                "phase_a_complete": False,
                "phase_a_completion_scope": MATERIAL_PENDING_COMPLETION_SCOPE,
                "full_repository_gate_claimed_by_this_artifact": False,
                "live_aggregate_release_unblocked": False,
                "phase_b_unblocked": False,
                "public_dataset_evaluation_unblocked": False,
                "private_research_unblocked": False,
                "provider_feasibility_unblocked": False,
                "runtime_activation_unblocked": False,
            },
        },
        location="material_pending_payload",
    )

    _validate_lower_commit(
        payload["repository_head_commit"],
        field="repository_head_commit",
    )
    if payload["implementation_baseline_commit"] != EXPECTED_IMPLEMENTATION_BASELINE_COMMIT:
        raise ValueError("implementation_baseline_commit is not the fixed Task 7 baseline")
    committed_paths = _validate_byte_inventory(
        payload["committed_change_inventory"],
        field="committed_change_inventory",
        include_git_state=False,
    )
    uncommitted_paths = _validate_byte_inventory(
        payload["uncommitted_change_inventory"],
        field="uncommitted_change_inventory",
        include_git_state=True,
    )
    closure_paths = _validate_byte_inventory(
        payload["executable_dependency_closure_inventory"],
        field="executable_dependency_closure_inventory",
        include_git_state=False,
    )
    _validate_exact_inventory_scope(
        committed_paths,
        expected_paths=TASKS_1_7_CHANGE_INVENTORY_PATHS,
        field="committed_change_inventory",
    )
    _validate_exact_inventory_scope(
        uncommitted_paths,
        expected_paths=(),
        field="uncommitted_change_inventory",
    )
    _validate_exact_inventory_scope(
        closure_paths,
        expected_paths=TASKS_1_7_CLOSURE_PATHS,
        field="executable_dependency_closure_inventory",
    )
    closure_edges = _validate_closure_edges(
        payload["executable_dependency_closure_edges"]
    )
    _validate_exact_closure_edge_scope(closure_edges)
    for consumer, dependency, _edge_type in closure_edges:
        if consumer not in closure_paths or dependency not in closure_paths:
            raise ValueError(
                "executable dependency closure edge endpoint is absent from inventory"
            )
    _assert_exact_json_value(
        payload["dataset_manifest_digests"],
        {},
        location="dataset_manifest_digests",
    )
    _assert_exact_json_value(
        payload["dataset_hash_inventory_digests"],
        {},
        location="dataset_hash_inventory_digests",
    )

    from scripts.emotion_state_phase_a_verification_evidence import (
        FROZEN_GUARD_POLICY_DIGEST,
        canonical_json_sha256,
        derive_repository_gate_statuses,
    )

    ledger = payload["executed_command_ledger"]
    if not isinstance(ledger, list):
        raise ValueError("executed_command_ledger must be a list")
    try:
        expected_gate_statuses = derive_repository_gate_statuses(
            ledger,
            "material-pending",
            baseline_commit=payload["implementation_baseline_commit"],
            head_commit=payload["repository_head_commit"],
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(f"executed_command_ledger is invalid: {exc}") from exc
    expected_commit_range = (
        payload["implementation_baseline_commit"]
        + ".."
        + payload["repository_head_commit"]
    )
    diff_entry = next(
        entry
        for entry in ledger
        if entry["command_id"] == "git-diff-check"
    )
    if diff_entry["argv"][-1] != expected_commit_range:
        raise ValueError(
            "executed command ledger commit range does not match payload commits"
        )
    expected_guarded_results = {
        entry["command_id"]: 0
        for entry in ledger
    }
    _assert_exact_json_value(
        payload["guarded_command_results"],
        expected_guarded_results,
        location="guarded_command_results",
    )
    _assert_exact_json_value(
        payload["repository_gate_statuses"],
        expected_gate_statuses,
        location="repository_gate_statuses",
    )
    _assert_exact_json_value(
        payload["provider_environment_scrubbed"],
        True,
        location="provider_environment_scrubbed",
    )
    _assert_exact_json_value(
        payload["private_path_guard_enabled"],
        True,
        location="private_path_guard_enabled",
    )
    _assert_exact_json_value(
        payload["network_guard_enabled"],
        True,
        location="network_guard_enabled",
    )
    if payload["guard_policy_digest"] != FROZEN_GUARD_POLICY_DIGEST:
        raise ValueError("guard_policy_digest does not match the frozen policy")

    expected_input_digest = canonical_json_sha256({
        "committed_change_inventory": payload["committed_change_inventory"],
        "uncommitted_change_inventory": payload["uncommitted_change_inventory"],
    })
    expected_closure_digest = canonical_json_sha256({
        "edges": payload["executable_dependency_closure_edges"],
        "inventory": payload["executable_dependency_closure_inventory"],
    })
    expected_ledger_digest = canonical_json_sha256(ledger)
    tree_payload = {
        "implementation_baseline_commit": payload["implementation_baseline_commit"],
        "repository_head_commit": payload["repository_head_commit"],
        "committed_change_inventory": payload["committed_change_inventory"],
        "uncommitted_change_inventory": payload["uncommitted_change_inventory"],
        "executable_dependency_closure_inventory": (
            payload["executable_dependency_closure_inventory"]
        ),
        "executable_dependency_closure_edges": (
            payload["executable_dependency_closure_edges"]
        ),
        "dataset_manifest_digests": payload["dataset_manifest_digests"],
        "dataset_hash_inventory_digests": payload["dataset_hash_inventory_digests"],
        "executed_command_ledger": ledger,
        "guard_policy_digest": payload["guard_policy_digest"],
    }
    expected_tree_digest = canonical_json_sha256(tree_payload)
    expected_run_id = hashlib.sha256(
        (
            "emotion-state-phase-a-validator-v1:"
            + expected_tree_digest
        ).encode("utf-8")
    ).hexdigest().upper()
    expected_digests = {
        "verification_input_path_inventory_digest": expected_input_digest,
        "executable_dependency_closure_digest": expected_closure_digest,
        "executed_command_ledger_digest": expected_ledger_digest,
        "verification_input_tree_digest": expected_tree_digest,
        "verification_run_id": expected_run_id,
    }
    for field, expected_digest in expected_digests.items():
        _validate_upper_sha256(payload[field], field=field)
        if payload[field] != expected_digest:
            raise ValueError(f"{field} does not match its canonical inputs")
    return payload


def validate_complete_payload(
    payload: Any,
    *,
    root: Path,
) -> dict[str, Any]:
    """Validate a complete candidate without treating it as accepted."""

    if not isinstance(payload, dict):
        raise ValueError("complete payload must be an object")
    if set(payload) != COMPLETE_PAYLOAD_FIELDS or len(payload) != 43:
        raise ValueError("complete payload must contain exactly 43 owned fields")
    if (
        payload["checkpoint_id"] != "EMOTION-STATE-001-phase-a-contracts"
        or payload["schema_version"] != 2
        or payload["mode"] != "complete"
        or payload["status"] != "complete"
        or payload["selected_public_datasets"]
        != list(SELECTED_PUBLIC_DATASET_IDS)
        or payload["dataset_download_authorized"] is not True
        or payload["dataset_evaluation_started"] is not False
    ):
        raise ValueError("complete payload identity or boundary mismatch")
    readiness_boundary = payload["readiness_boundary"]
    if (
        not isinstance(readiness_boundary, Mapping)
        or set(readiness_boundary) != COMPLETE_READINESS_BOUNDARY_FIELDS
    ):
        raise ValueError(
            "readiness_boundary must contain exactly the owned fields"
        )

    (
        expected_dataset_evidence,
        expected_hash_digests,
        expected_quality_digests,
    ) = _load_complete_dataset_evidence(Path(root))
    expected_manifest_digests = {
        entry["dataset_id"]: entry["manifest_sha256"]
        for entry in expected_dataset_evidence
    }
    _assert_exact_json_value(
        payload["dataset_manifest_evidence"],
        expected_dataset_evidence,
        location="dataset_manifest_evidence",
    )
    _assert_exact_json_value(
        payload["dataset_manifest_digests"],
        expected_manifest_digests,
        location="dataset_manifest_digests",
    )
    _assert_exact_json_value(
        payload["dataset_hash_inventory_digests"],
        expected_hash_digests,
        location="dataset_hash_inventory_digests",
    )
    _assert_exact_json_value(
        payload["dataset_quality_inventory_digests"],
        expected_quality_digests,
        location="dataset_quality_inventory_digests",
    )
    expected_statuses = {
        dataset_id: "pass"
        for dataset_id in SELECTED_PUBLIC_DATASET_IDS
    }
    _assert_exact_json_value(
        payload["dataset_material_validation_status"],
        expected_statuses,
        location="dataset_material_validation_status",
    )
    _assert_exact_json_value(
        payload["source_provenance_status"],
        expected_statuses,
        location="source_provenance_status",
    )
    contract_statuses = {
        "public_dataset_contract": payload["public_dataset_contract_status"],
        "split_manifest_v2_contract": payload[
            "split_manifest_v2_contract_status"
        ],
        "cohort_release_contract": payload["cohort_release_contract_status"],
    }
    verification_fields = {
        field: payload[field]
        for field in (
            "implementation_baseline_commit",
            "repository_head_commit",
            "verification_run_id",
            "verification_input_path_inventory_digest",
            "executable_dependency_closure_digest",
            "executed_command_ledger_digest",
            "guard_policy_digest",
            "verification_input_tree_digest",
            "provider_environment_scrubbed",
            "private_path_guard_enabled",
            "network_guard_enabled",
            "prepublication_byte_lock_reread_status",
        )
    }
    completion = determine_phase_a_completion({
        "mode": "complete",
        "selected_dataset_ids": list(payload["selected_public_datasets"]),
        "dataset_download_authorized": payload["dataset_download_authorized"],
        "dataset_evidence": payload["dataset_manifest_evidence"],
        "contract_statuses": contract_statuses,
        "verification_evidence": verification_fields,
        "executed_command_ledger": payload["executed_command_ledger"],
        "publication_integrity_preconditions": payload[
            "publication_integrity_preconditions"
        ],
        "authorization_boundaries": {
            field: readiness_boundary[field]
            for field in (
                "live_aggregate_release_unblocked",
                "public_dataset_evaluation_unblocked",
                "phase_b_unblocked",
                "private_research_unblocked",
                "provider_feasibility_unblocked",
                "runtime_activation_unblocked",
            )
        },
    })
    blockers = completion.pop("blocking_reason_codes")
    if blockers or not completion["phase_a_complete"]:
        raise ValueError("complete payload gate evidence is incomplete")
    _assert_exact_json_value(
        payload["blocking_reason_codes"],
        [],
        location="blocking_reason_codes",
    )
    _assert_exact_json_value(
        readiness_boundary,
        completion,
        location="readiness_boundary",
    )

    from scripts.emotion_state_phase_a_verification_evidence import (
        FROZEN_GUARD_POLICY_DIGEST,
        canonical_json_sha256,
        derive_repository_gate_statuses,
    )

    ledger = payload["executed_command_ledger"]
    derived_gate_statuses = derive_repository_gate_statuses(
        ledger,
        "complete",
        baseline_commit=payload["implementation_baseline_commit"],
        head_commit=payload["repository_head_commit"],
    )
    _assert_exact_json_value(
        payload["repository_gate_statuses"],
        derived_gate_statuses,
        location="repository_gate_statuses",
    )
    _assert_exact_json_value(
        payload["guarded_command_results"],
        {entry["command_id"]: 0 for entry in ledger},
        location="guarded_command_results",
    )
    if payload["implementation_baseline_commit"] != EXPECTED_IMPLEMENTATION_BASELINE_COMMIT:
        raise ValueError("implementation_baseline_commit is not fixed")
    _validate_lower_commit(
        payload["repository_head_commit"],
        field="repository_head_commit",
    )
    if payload["guard_policy_digest"] != FROZEN_GUARD_POLICY_DIGEST:
        raise ValueError("guard_policy_digest does not match the frozen policy")

    expected_input_digest = canonical_json_sha256({
        "committed_change_inventory": payload["committed_change_inventory"],
        "uncommitted_change_inventory": payload["uncommitted_change_inventory"],
    })
    expected_closure_digest = canonical_json_sha256({
        "edges": payload["executable_dependency_closure_edges"],
        "inventory": payload["executable_dependency_closure_inventory"],
    })
    expected_ledger_digest = canonical_json_sha256(ledger)
    tree_payload = {
        "implementation_baseline_commit": payload["implementation_baseline_commit"],
        "repository_head_commit": payload["repository_head_commit"],
        "committed_change_inventory": payload["committed_change_inventory"],
        "uncommitted_change_inventory": payload["uncommitted_change_inventory"],
        "executable_dependency_closure_inventory": payload[
            "executable_dependency_closure_inventory"
        ],
        "executable_dependency_closure_edges": payload[
            "executable_dependency_closure_edges"
        ],
        "dataset_manifest_digests": payload["dataset_manifest_digests"],
        "dataset_hash_inventory_digests": payload[
            "dataset_hash_inventory_digests"
        ],
        "dataset_quality_inventory_digests": payload[
            "dataset_quality_inventory_digests"
        ],
        "executed_command_ledger": ledger,
        "guard_policy_digest": payload["guard_policy_digest"],
    }
    expected_tree_digest = canonical_json_sha256(tree_payload)
    expected_run_id = hashlib.sha256(
        (
            "emotion-state-phase-a-validator-v1:"
            + expected_tree_digest
        ).encode("utf-8")
    ).hexdigest().upper()
    for field, expected in {
        "verification_input_path_inventory_digest": expected_input_digest,
        "executable_dependency_closure_digest": expected_closure_digest,
        "executed_command_ledger_digest": expected_ledger_digest,
        "verification_input_tree_digest": expected_tree_digest,
        "verification_run_id": expected_run_id,
    }.items():
        if payload[field] != expected:
            raise ValueError(f"{field} does not match its canonical inputs")
    return payload


def build_phase_a_payload(
    case_path: Path,
    *,
    root: Path,
    verification_evidence: Mapping[str, Any] | None = None,
    mode: str | None = None,
) -> dict[str, Any]:
    try:
        case_path = Path(case_path)
        root = Path(root)
    except TypeError as exc:
        raise ValueError("case path and root must be path-like") from exc
    case = read_json(case_path)
    validate_phase_a_case(case)
    manifest_path = (
        root
        / "research"
        / "sources"
        / "creative_analysis_engine"
        / "source_manifest.json"
    )
    manifest = read_json(manifest_path)
    validate_source_manifest(manifest)
    normalized_verification = _normalized_verification_evidence(
        verification_evidence
    )
    if mode is None:
        mode = (
            "complete"
            if case["dataset_download_authorized"]
            else "material_pending"
        )
    if mode not in {"material_pending", "complete"}:
        raise ValueError("invalid Phase A payload mode")
    reserved_fields = {
        "checkpoint_id",
        "schema_version",
        "mode",
        "status",
        "selected_public_datasets",
        "dataset_download_authorized",
        "dataset_evaluation_started",
        "dataset_manifest_evidence",
        "source_pin",
        "contract_checks",
        "blocking_reason_codes",
        "summary",
        "archive_sha256",
        "baseline_fingerprints",
        "readiness_boundary",
        "dataset_material_validation_status",
        "source_provenance_status",
        "public_dataset_contract_status",
        "cohort_release_contract_status",
        "split_manifest_v2_contract_status",
        "publication_integrity_preconditions",
    }
    if reserved_fields.intersection(normalized_verification):
        raise ValueError("verification evidence collides with checkpoint fields")
    allowed_verification_fields = (
        COMPLETE_VERIFICATION_EVIDENCE_FIELDS
        if mode == "complete"
        else VERIFICATION_EVIDENCE_FIELDS
    )
    if not set(normalized_verification).issubset(allowed_verification_fields):
        raise ValueError("verification evidence fields mismatch")
    code_adaptation_started = any(manifest[field] for field in MATERIAL_FIELDS)
    baseline = {
        relative_path: sha256_file(root / relative_path)
        for relative_path in EXPECTED_BASELINE_FINGERPRINTS
    }
    if baseline != case["baseline_fingerprints"]:
        raise ValueError("frozen baseline fingerprint drift")
    from scripts.emotion_state_public_dataset_contracts import (
        public_dataset_contract_self_check,
    )
    from scripts.emotion_state_split_manifest_v2_contracts import (
        split_manifest_v2_self_check,
    )

    checks = {
        "exp_002_frozen_response_baseline": frozen_baseline_self_check(root),
        "emotion_state_annotation_contracts": annotation_contract_self_check(),
        "public_dataset_contract": public_dataset_contract_self_check(),
        "split_manifest_v2_contract": split_manifest_v2_self_check(),
        "cohort_release_contract": cohort_release_contract_self_check(),
        "emotion_state_contracts": contract_self_check(),
        "emotion_pattern_contracts": pattern_contract_self_check(),
        "emotion_state_brain_extension": brain_extension_self_check(),
    }
    if set(checks.values()) != {"pass"}:
        raise ValueError("one or more Phase A contract self-checks failed")
    contract_statuses = {
        key: checks[key]
        for key in MATERIAL_PENDING_CONTRACT_STATUSES
    }
    dataset_evidence: list[dict[str, Any]] = []
    dataset_hash_inventory_digests: dict[str, str] = {}
    dataset_quality_inventory_digests: dict[str, str] = {}
    publication_integrity_preconditions = {
        "crash_safe_pair_protocol_status": "pass",
        "explicit_acceptance_transaction_status": "pass",
        "last_valid_pair_preservation_status": "pass",
        "output_self_reference_absent": True,
    }
    if mode == "complete":
        (
            dataset_evidence,
            dataset_hash_inventory_digests,
            dataset_quality_inventory_digests,
        ) = _load_complete_dataset_evidence(root)
        expected_dataset_digests = {
            "dataset_manifest_digests": {
                entry["dataset_id"]: entry["manifest_sha256"]
                for entry in dataset_evidence
            },
            "dataset_hash_inventory_digests": dataset_hash_inventory_digests,
            "dataset_quality_inventory_digests": (
                dataset_quality_inventory_digests
            ),
        }
        for field, expected in expected_dataset_digests.items():
            if (
                field in normalized_verification
                and normalized_verification[field] != expected
            ):
                raise ValueError(
                    f"verification evidence {field} does not match tracked evidence"
                )

    if mode == "material_pending":
        completion_request: dict[str, Any] = {
            "mode": "material_pending",
            "selected_dataset_ids": list(case["selected_public_datasets"]),
            "dataset_download_authorized": False,
            "dataset_evidence": [],
            "contract_statuses": contract_statuses,
        }
    elif normalized_verification:
        verification_fields = {
            field: normalized_verification.get(field)
            for field in (
                "implementation_baseline_commit",
                "repository_head_commit",
                "verification_run_id",
                "verification_input_path_inventory_digest",
                "executable_dependency_closure_digest",
                "executed_command_ledger_digest",
                "guard_policy_digest",
                "verification_input_tree_digest",
                "provider_environment_scrubbed",
                "private_path_guard_enabled",
                "network_guard_enabled",
                "prepublication_byte_lock_reread_status",
            )
        }
        ledger = normalized_verification.get("executed_command_ledger", [])
        from scripts.emotion_state_phase_a_verification_evidence import (
            derive_repository_gate_statuses,
        )

        try:
            derived_repository_gates = derive_repository_gate_statuses(
                ledger,
                "complete",
                baseline_commit=verification_fields[
                    "implementation_baseline_commit"
                ],
                head_commit=verification_fields["repository_head_commit"],
            )
        except (TypeError, ValueError):
            derived_repository_gates = {}
        derived_guarded_results = {
            entry.get("command_id"): entry.get("exit_status")
            for entry in ledger
            if isinstance(entry, Mapping)
        }
        if (
            "repository_gate_statuses" in normalized_verification
            and normalized_verification["repository_gate_statuses"]
            != derived_repository_gates
        ):
            raise ValueError("repository_gate_statuses do not match derived ledger")
        if (
            "guarded_command_results" in normalized_verification
            and normalized_verification["guarded_command_results"]
            != derived_guarded_results
        ):
            raise ValueError("guarded_command_results do not match derived ledger")
        normalized_verification["repository_gate_statuses"] = (
            derived_repository_gates
        )
        normalized_verification["guarded_command_results"] = (
            derived_guarded_results
        )
        completion_request = {
            "mode": "complete",
            "selected_dataset_ids": list(case["selected_public_datasets"]),
            "dataset_download_authorized": case["dataset_download_authorized"],
            "dataset_evidence": dataset_evidence,
            "contract_statuses": contract_statuses,
            "verification_evidence": verification_fields,
            "executed_command_ledger": ledger,
            "publication_integrity_preconditions": (
                publication_integrity_preconditions
            ),
            "authorization_boundaries": {
                "live_aggregate_release_unblocked": False,
                "public_dataset_evaluation_unblocked": False,
                "phase_b_unblocked": False,
                "private_research_unblocked": False,
                "provider_feasibility_unblocked": False,
                "runtime_activation_unblocked": False,
            },
        }
    else:
        completion_request = {
            "mode": "complete",
            "selected_dataset_ids": list(case["selected_public_datasets"]),
            "dataset_download_authorized": case["dataset_download_authorized"],
            "dataset_evidence": dataset_evidence,
            "contract_statuses": contract_statuses,
            "verification_evidence": {},
            "executed_command_ledger": [],
            "publication_integrity_preconditions": (
                publication_integrity_preconditions
            ),
            "authorization_boundaries": {
                "live_aggregate_release_unblocked": False,
                "public_dataset_evaluation_unblocked": False,
                "phase_b_unblocked": False,
                "private_research_unblocked": False,
                "provider_feasibility_unblocked": False,
                "runtime_activation_unblocked": False,
            },
        }
    completion = determine_phase_a_completion(completion_request)
    blockers = completion.pop("blocking_reason_codes")
    payload_download_authorized = (
        case["dataset_download_authorized"]
        if mode == "complete"
        else False
    )
    payload = {
        "checkpoint_id": "EMOTION-STATE-001-phase-a-contracts",
        "schema_version": 2,
        "mode": mode,
        "status": mode,
        "selected_public_datasets": list(case["selected_public_datasets"]),
        "dataset_download_authorized": payload_download_authorized,
        "dataset_evaluation_started": case["dataset_evaluation_started"],
        "dataset_manifest_evidence": dataset_evidence,
        "source_pin": {
            "source_repository_url": manifest["source_repository_url"],
            "source_branch": manifest["source_branch"],
            "source_revision": manifest["source_revision"],
            "archive_sha256": manifest["archive_sha256"],
            "source_adaptation_allowed": manifest["adaptation_allowed"],
            "code_adaptation_started": code_adaptation_started,
        },
        "contract_checks": checks,
        "blocking_reason_codes": blockers,
        "summary": {
            "contract_check_count": len(checks),
            "contract_checks": checks,
            "baseline_fingerprint_count": len(baseline),
            "selected_public_dataset_count": len(case["selected_public_datasets"]),
            "dataset_download_authorized": payload_download_authorized,
            "dataset_evaluation_started": case["dataset_evaluation_started"],
            "material_verification_status": (
                "verified" if mode == "complete" else "pending"
            ),
            "source_repository_url_status": manifest["source_repository_url_status"],
            "source_adaptation_allowed": manifest["adaptation_allowed"],
            "code_adaptation_started": code_adaptation_started,
            "frozen_exp_002_evaluator_provenance_status": "not_recorded",
            "provider_operations_performed_by_runner": False,
            "private_data_read_by_runner": False,
            "runtime_behavior_changed_by_runner": False,
            "runtime_activation_allowed": False,
        },
        "archive_sha256": manifest["archive_sha256"],
        "baseline_fingerprints": baseline,
        "readiness_boundary": completion,
    }
    if mode == "complete":
        payload.update({
            "dataset_hash_inventory_digests": (
                dataset_hash_inventory_digests
            ),
            "dataset_quality_inventory_digests": (
                dataset_quality_inventory_digests
            ),
            "dataset_material_validation_status": {
                dataset_id: "pass"
                for dataset_id in SELECTED_PUBLIC_DATASET_IDS
            },
            "source_provenance_status": {
                dataset_id: "pass"
                for dataset_id in SELECTED_PUBLIC_DATASET_IDS
            },
            "public_dataset_contract_status": (
                contract_statuses["public_dataset_contract"]
            ),
            "cohort_release_contract_status": (
                contract_statuses["cohort_release_contract"]
            ),
            "split_manifest_v2_contract_status": (
                contract_statuses["split_manifest_v2_contract"]
            ),
            "publication_integrity_preconditions": (
                publication_integrity_preconditions
            ),
        })
    payload.update(normalized_verification)
    if mode == "complete":
        payload["dataset_manifest_digests"] = {
            entry["dataset_id"]: entry["manifest_sha256"]
            for entry in dataset_evidence
        }
        payload["dataset_hash_inventory_digests"] = (
            dataset_hash_inventory_digests
        )
        payload["dataset_quality_inventory_digests"] = (
            dataset_quality_inventory_digests
        )
    return payload


def render_phase_a_report(
    payload: dict[str, Any],
    *,
    result_sha256: str,
) -> str:
    if (
        not isinstance(result_sha256, str)
        or len(result_sha256) != 64
        or any(character not in "0123456789ABCDEF" for character in result_sha256)
    ):
        raise ValueError("result_sha256 must be exactly 64 uppercase SHA-256 hexadecimal characters")
    summary = payload["summary"]
    return "\n".join([
        "# EMOTION-STATE-001 Phase A Contract Report",
        "",
        "This material-pending artifact validates source provenance, selected public-dataset IDs, and offline contract artifacts only; Phase A remains incomplete until separately authorized local materials are verified.",
        "",
        f"- Contract checks: `{summary['contract_check_count']}`",
        f"- Baseline fingerprints: `{summary['baseline_fingerprint_count']}`",
        f"- Publication commit marker: `result.json sha256:{result_sha256}`",
        f"- Selected public datasets: `{summary['selected_public_dataset_count']}`",
        f"- Dataset download authorized: `{summary.get('dataset_download_authorized', False)}`",
        f"- Dataset evaluation started: `{summary.get('dataset_evaluation_started', False)}`",
        f"- Material verification status: `{summary.get('material_verification_status', 'pending')}`",
        f"- Phase A complete: `{payload['readiness_boundary']['phase_a_complete']}`",
        f"- Source URL status: `{summary['source_repository_url_status']}`",
        f"- Code adaptation started: `{summary['code_adaptation_started']}`",
        f"- Frozen EXP-002 evaluator provenance status: `{summary['frozen_exp_002_evaluator_provenance_status']}`",
        f"- Provider operations performed by this runner: `{summary['provider_operations_performed_by_runner']}`",
        f"- Private data read by this runner: `{summary['private_data_read_by_runner']}`",
        f"- Runtime behavior changed by this runner: `{summary['runtime_behavior_changed_by_runner']}`",
        "",
        "Source adaptation remains blocked by the source URL, revision or authoritative archive date, Phase B reuse scope, Phase B attribution wording, and separate Phase B approval.",
        "Per-public-dataset manifests remain open and unverified. Acted and non-sales corpora can support offline thesis comparison only. Runtime activation remains blocked.",
        "Live aggregate release remains blocked until a separately approved privacy-preserving unique-speaker cohort-release and dedup gate exists.",
        "",
        "This is not production readiness, real-customer validation, PSTN/ASR/latency validation, provider-feasibility evidence, runtime activation, or proof of internal customer emotion.",
        "",
    ])
