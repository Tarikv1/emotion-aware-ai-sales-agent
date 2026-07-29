#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SOURCE_MANIFEST = ROOT / "research" / "sources" / "creative_analysis_engine" / "source_manifest.json"
SOURCE_NOTES = SOURCE_MANIFEST.with_name("source_notes.md")
DATASET_CONTRACT = ROOT / "research" / "sources" / "emotion_state" / "dataset_manifest_contract.json"
ANNOTATION_SCHEMA = DATASET_CONTRACT.with_name("annotation_record_v1.schema.json")
SPLIT_SCHEMA = DATASET_CONTRACT.with_name("split_manifest_v1.schema.json")
SPLIT_SCHEMA_V2 = DATASET_CONTRACT.with_name("split_manifest_v2.schema.json")
COHORT_RELEASE_SCHEMA = DATASET_CONTRACT.with_name("cohort_release_evidence_v1.schema.json")
COHORT_RELEASE_FIXTURES = (
    ROOT
    / "research"
    / "experiments"
    / "cases"
    / "emotion-state-001-cohort-release-fixtures.json"
)
CODEBOOK = ROOT / "docs" / "data" / "EMOTION_STATE_001_ANNOTATION_CODEBOOK.md"
THESIS_REFERENCE_REGISTRY = ROOT / "docs" / "thesis" / "THESIS_REFERENCE_REGISTRY.md"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "emotion-state-001-phase-a-contracts.json"
RUNNER = ROOT / "scripts" / "run_emotion_state_001_phase_a_contracts.py"
RESULT = ROOT / "research" / "experiments" / "generated" / "EMOTION-STATE-001-phase-a-contracts" / "result.json"
REPORT = RESULT.with_name("report.md")
RECOVERY_DIR = ROOT / ".tmp" / "emotion-state-001-phase-a-publication"
EXPECTED_ARCHIVE_SHA256 = "E579B966E226F2AF6E4F8F8203C7189FEC94FB448EFC09B4B6640C10A398ECCC"
EXPECTED_BASELINE_FINGERPRINTS = {
    "packages/prompts/baseline-non-adaptive.txt": "BB1FD1EAC0D4DE858BFDCE4A880BBF2C59C14A216489A1A85EF149F3E88D7FCA",
    "packages/prompts/baseline-adaptive.txt": "EBD4106841987CA4A322C2B8B95A33ECFFC4238BB476DEC611A640D5B000EB42",
    "research/experiments/cases/exp-002-dataset-derived.json": "882B94C0A31C41A94540941A254AC7E8119CADE9AAD9B071089E854917BDC7D6",
    "research/experiments/EXP-002-dataset-derived-baseline.md": "D930C845AC912D44610B3CE263B55EA03BFFD7CAB8706C2BC95CB17045FF1316",
    "research/experiments/generated/EXP-002/EXP-002-prompt-packet.md": "14017F985D54D2B46A338EA2EFA796B24202E3E5A3D3EB8223346CEA96E5CD09",
    "docs/thesis/EVALUATION_RUBRIC.md": "39D3CF33E38A0C13ADEE178F3DB4174D4D8E3A42B1DE4C274BF96FFA36FFB416",
}
EXPECTED_NORMALIZED_PROMPT_PACKET_SHA256 = "83DF6E5F7B3566754F7D09C78F5BBD3B013ABED328C01EF90BA68BCFF2C395FA"


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> Any:
    assert_condition(path.exists(), f"missing required file: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def require_text(path: Path, markers: list[str]) -> str:
    assert_condition(path.exists(), f"missing required file: {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        assert_condition(marker in text, f"{path.relative_to(ROOT)} missing marker: {marker}")
    return text


def normalized_prompt_packet_digest(path: Path) -> str:
    text = path.read_bytes().decode("utf-8")
    normalized, replacement_count = re.subn(
        r"(?m)^- Source case file: `[^`\r\n]+`(?=\r?$)",
        "- Source case file: `<normalized>`",
        text,
    )
    assert_condition(replacement_count == 1, f"expected one source-case line in {path.relative_to(ROOT)}")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest().upper()


def validate_source() -> None:
    manifest = read_json(SOURCE_MANIFEST)
    assert_condition(manifest["manifest_id"] == "creative-analysis-engine-emotion-state-source-v1", manifest)
    assert_condition(manifest["archive_sha256"] == EXPECTED_ARCHIVE_SHA256, manifest)
    assert_condition(manifest["author"] == "Shehzeb Iftakhar", manifest)
    assert_condition(manifest["permission_attestation"]["status"] == "confirmed_by_project_owner", manifest)
    assert_condition(manifest["permission_attestation"]["date"] == "2026-07-14", manifest)
    assert_condition(
        manifest["permission_attestation"]["basis"]
        == "project-owner attestation of author and supervisor approval",
        manifest,
    )
    assert_condition(manifest["permission_attestation"]["credit_required"] is True, manifest)
    assert_condition(
        manifest["source_repository_url"]
        == "https://github.com/WisdomBreathes/creative-analysis-engine",
        manifest,
    )
    assert_condition(manifest["source_repository_url_status"] == "verified_read_only", manifest)
    assert_condition(manifest["source_branch"] == "dev", manifest)
    assert_condition(
        manifest["source_revision"] == "7cb99ea2da3016cd82d0b5f805c015a808ce4e0d",
        manifest,
    )
    assert_condition(manifest["source_revision_status"] == "verified_read_only", manifest)
    assert_condition(manifest["source_archive_date"] is None, manifest)
    assert_condition(manifest["source_archive_date_status"] == "unverified", manifest)
    assert_condition(manifest["observed_license"] is None, manifest)
    assert_condition(manifest["observed_license_status"] == "absent_in_reviewed_root", manifest)
    assert_condition(manifest["copied_material"] == [], manifest)
    assert_condition(manifest["translated_material"] == [], manifest)
    assert_condition(manifest["adapted_material"] == [], manifest)
    assert_condition(manifest["independently_reimplemented_material"] == [], manifest)
    assert_condition(manifest["project_local_only"] is True, manifest)
    assert_condition(manifest["runtime_dependency_added"] is False, manifest)
    assert_condition(manifest["attribution"]["credit_name"] == "Shehzeb Iftakhar", manifest)
    assert_condition(manifest["attribution"]["phase_a_status"] == "recorded", manifest)
    assert_condition(manifest["attribution"]["phase_b_reuse_scope_status"] == "not_defined", manifest)
    assert_condition(manifest["attribution"]["phase_b_reuse_scope"] == [], manifest)
    assert_condition(manifest["attribution"]["phase_b_attribution_wording_status"] == "pending", manifest)
    assert_condition(manifest["attribution"]["phase_b_wording"] is None, manifest)
    assert_condition(manifest["phase_b_approval"]["status"] == "not_requested", manifest)
    assert_condition(manifest["phase_b_approval"]["approved"] is False, manifest)
    assert_condition(manifest["phase_b_approval"]["approval_reference"] is None, manifest)
    assert_condition(manifest["adaptation_allowed"] is False, manifest)
    assert_condition(manifest["adaptation_blockers"] == [
        "current_instruction_prohibits_source_adaptation",
        "observed_repository_license_absent",
        "phase_b_reuse_scope_not_defined",
        "phase_b_attribution_wording_pending",
        "phase_b_approval_not_granted",
    ], manifest)
    expected_reviewed_files = [
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
    assert_condition(manifest["reviewed_files"] == expected_reviewed_files, manifest)
    dataset_contract = read_json(DATASET_CONTRACT)
    from scripts.emotion_state_public_dataset_contracts import (
        REQUIRED_V1_FIELDS,
        REQUIRED_V2_FIELDS,
        SELECTED_PUBLIC_DATASETS,
        public_dataset_contract_self_check,
    )

    assert_condition(dataset_contract["schema_id"] == "emotion-state-dataset-manifest-v2", dataset_contract)
    assert_condition(
        type(dataset_contract["schema_version"]) is int
        and dataset_contract["schema_version"] == 2,
        dataset_contract,
    )
    assert_condition(
        set(dataset_contract["required_v1_fields"]) == REQUIRED_V1_FIELDS,
        dataset_contract,
    )
    assert_condition(set(dataset_contract["required_fields"]) == REQUIRED_V2_FIELDS, dataset_contract)
    assert_condition(set(dataset_contract["allowed_source_labels"]) == {
        "public-only", "private-restricted", "mixed-source", "synthetic-only",
    }, dataset_contract)
    assert_condition(
        dataset_contract["selected_public_datasets"] == list(SELECTED_PUBLIC_DATASETS),
        dataset_contract,
    )
    assert_condition(dataset_contract["dataset_download_authorized"] is True, dataset_contract)
    assert_condition(dataset_contract["dataset_evaluation_started"] is False, dataset_contract)
    assert_condition(dataset_contract["runtime_influence_allowed"] is False, dataset_contract)
    assert_condition(dataset_contract["domain_boundary"] == "acted_and_non_sales_corpora_support_offline_thesis_comparison_only", dataset_contract)
    assert_condition(
        public_dataset_contract_self_check() == "pass",
        "public dataset contract self-check failed",
    )
    annotation_schema = read_json(ANNOTATION_SCHEMA)
    from scripts.emotion_state_annotation_contracts import (
        ANNOTATION_FIELDS,
        DEPENDENCY_GROUP_FIELDS,
        NOT_INFERABLE_REASONS,
        OPERATIONAL_SIGNALS,
        SPLIT_MANIFEST_FIELDS,
        annotation_contract_self_check,
    )

    assert_condition(annotation_schema["schema_id"] == "emotion-state-annotation-record-v1", annotation_schema)
    assert_condition(set(annotation_schema["required_fields"]) == ANNOTATION_FIELDS, annotation_schema)
    assert_condition(set(annotation_schema["dependency_group_fields"]) == DEPENDENCY_GROUP_FIELDS, annotation_schema)
    assert_condition(set(annotation_schema["allowed_operational_signals"]) == OPERATIONAL_SIGNALS, annotation_schema)
    assert_condition(set(annotation_schema["allowed_evidence_classes"]) == {
        "direct_explicit", "observer_inference", "not_inferable",
    }, annotation_schema)
    assert_condition(set(annotation_schema["allowed_reviewer_confidence"]) == {
        "low", "medium", "high",
    }, annotation_schema)
    assert_condition(set(annotation_schema["allowed_not_inferable_reason_codes"]) == NOT_INFERABLE_REASONS, annotation_schema)
    assert_condition(annotation_schema["reviewers_per_turn"] == 3, annotation_schema)
    assert_condition(annotation_schema["valence_scale"] == [-2, -1, 0, 1, 2], annotation_schema)
    assert_condition(annotation_schema["activation_scale"] == [1, 2, 3, 4, 5], annotation_schema)
    assert_condition(annotation_schema["engagement_scale"] == [1, 2, 3, 4, 5], annotation_schema)
    assert_condition(annotation_schema["not_inferable_excludes_other_labels"] is True, annotation_schema)
    assert_condition(annotation_schema["unrestricted_transcript_quotes_allowed"] is False, annotation_schema)
    assert_condition(
        annotation_schema["explicit_statement_reference_format"]
        == "evidence:uuid:<canonical-lowercase-uuid-v4>",
        annotation_schema,
    )
    assert_condition(annotation_schema["runtime_influence_allowed"] is False, annotation_schema)
    split_schema = read_json(SPLIT_SCHEMA)
    assert_condition(split_schema["schema_id"] == "emotion-state-split-manifest-v1", split_schema)
    assert_condition(set(split_schema["required_fields"]) == SPLIT_MANIFEST_FIELDS, split_schema)
    assert_condition(set(split_schema["dependency_keys"]) == DEPENDENCY_GROUP_FIELDS, split_schema)
    assert_condition(split_schema["runtime_influence_allowed"] is False, split_schema)
    assert_condition(split_schema["training_discovery"]["case_ids"] == [], split_schema)
    assert_condition(split_schema["calibration"]["case_ids"] == [], split_schema)
    assert_condition(split_schema["balanced_diagnostic"]["case_ids"] == [], split_schema)
    assert_condition(split_schema["final_lockbox"]["open_count"] == 0, split_schema)
    assert_condition(split_schema["final_lockbox"]["case_ids"] == [], split_schema)
    for partition_name in ("training_discovery", "calibration", "balanced_diagnostic", "final_lockbox"):
        groups = split_schema[partition_name]["dependency_groups"]
        assert_condition(set(groups) == DEPENDENCY_GROUP_FIELDS, groups)
        assert_condition(all(identifiers == [] for identifiers in groups.values()), groups)
    split_schema_v2 = read_json(SPLIT_SCHEMA_V2)
    from scripts.emotion_state_split_manifest_v2_contracts import (
        DEPENDENCY_KEYS_V2,
        DEPENDENCY_PROFILES_V2,
        DEPENDENCY_REQUIREMENTS,
        DEPENDENCY_STATUSES,
        PARTITION_FIELDS_V2,
        PARTITIONS,
        QUARANTINE_FIELDS_V2,
        SPLIT_MANIFEST_V2_FIELDS,
        dependency_profiles_v2_contract,
        split_manifest_v2_self_check,
    )

    assert_condition(
        split_schema_v2["schema_id"] == "emotion-state-split-manifest-v2",
        split_schema_v2,
    )
    assert_condition(
        type(split_schema_v2["schema_version"]) is int
        and split_schema_v2["schema_version"] == 2,
        split_schema_v2,
    )
    assert_condition(
        len(split_schema_v2["required_fields"]) == len(SPLIT_MANIFEST_V2_FIELDS)
        and set(split_schema_v2["required_fields"]) == SPLIT_MANIFEST_V2_FIELDS,
        split_schema_v2,
    )
    assert_condition(
        split_schema_v2["dependency_keys"] == list(DEPENDENCY_KEYS_V2),
        split_schema_v2,
    )
    assert_condition(
        set(split_schema_v2["allowed_dependency_requirements"]) == DEPENDENCY_REQUIREMENTS,
        split_schema_v2,
    )
    assert_condition(
        set(split_schema_v2["allowed_dependency_statuses"]) == DEPENDENCY_STATUSES,
        split_schema_v2,
    )
    assert_condition(
        split_schema_v2["allowed_dependency_profile_ids"] == list(DEPENDENCY_PROFILES_V2),
        split_schema_v2,
    )
    assert_condition(
        split_schema_v2["dependency_profiles"] == dependency_profiles_v2_contract(),
        split_schema_v2,
    )
    for partition_name in PARTITIONS:
        partition = split_schema_v2[partition_name]
        assert_condition(set(partition) == PARTITION_FIELDS_V2[partition_name], partition)
        assert_condition(partition["case_ids"] == [], partition)
        groups = partition["dependency_groups"]
        assert_condition(tuple(groups) == DEPENDENCY_KEYS_V2, groups)
        assert_condition(all(identifiers == [] for identifiers in groups.values()), groups)
    quarantine = split_schema_v2["dependency_unknown_quarantine"]
    assert_condition(set(quarantine) == QUARANTINE_FIELDS_V2, quarantine)
    assert_condition(quarantine["case_ids"] == [], quarantine)
    assert_condition(quarantine["reason_codes"] == [], quarantine)
    assert_condition(quarantine["claims_allowed"] is False, quarantine)
    assert_condition(split_schema_v2["metric_denominator_case_ids"] == [], split_schema_v2)
    assert_condition(split_schema_v2["claim_denominator_case_ids"] == [], split_schema_v2)
    assert_condition(split_schema_v2["frozen_candidate_family_digest"] is None, split_schema_v2)
    assert_condition(split_schema_v2["confirmatory_claims_allowed"] is False, split_schema_v2)
    assert_condition(split_schema_v2["runtime_influence_allowed"] is False, split_schema_v2)
    assert_condition(
        split_manifest_v2_self_check() == "pass",
        "split manifest v2 contract self-check failed",
    )
    require_text(SOURCE_NOTES, [
        "The seven reviewed files were verified byte-identical",
        "The full ZIP was not proven equivalent",
        "No code was copied, translated, adapted, or independently reimplemented",
    ])
    require_text(CODEBOOK, [
        "not_inferable", "ambiguous", "Krippendorff", "three independent reviewers",
        "practice set", "`none` means", "abstention-policy error", "redacted, nonreversible",
        "evidence:uuid:", "Retain reviewer-level disagreement", "Derive every split dependency summary",
    ])
    require_text(ROOT / "docs" / "third-party-inspirations.md", [
        "Creative Analysis Engine",
        "research/sources/creative_analysis_engine/source_manifest.json",
        "The seven reviewed files were verified byte-identical",
        "The full ZIP was not proven equivalent",
        "No code was copied, translated, adapted, or independently reimplemented",
    ])
    require_text(THESIS_REFERENCE_REGISTRY, [
        "https://sail.usc.edu/iemocap/",
        "https://ecs.utdallas.edu/research/researchlabs/msp-lab/MSP-Podcast.html",
        "https://onlinelibrary.wiley.com/doi/10.1111/j.1468-2958.2004.tb00738.x",
        "https://airc.nist.gov/airmf-resources/airmf/5-sec-core/",
    ])
    assert_condition(annotation_contract_self_check() == "pass", "annotation contract self-check failed")


def validate_contracts() -> None:
    case = read_json(CASE_PATH)
    assert_condition(case["checkpoint_id"] == "EMOTION-STATE-001-phase-a-contracts", case)
    assert_condition(case["schema_version"] == 2, case)
    assert_condition(case["source_label"] == "public-only", case)
    assert_condition(case["campaign_profile_version"] == "fixture-v2", case)
    assert_condition(case["selected_public_datasets"] == [
        "crema-d-v1.0-audio-wav",
        "ami-manual-annotations-v1.6.2",
    ], case)
    assert_condition(case["dataset_download_authorized"] is True, case)
    assert_condition(case["dataset_evaluation_started"] is False, case)
    assert_condition(case["private_data_access_allowed"] is False, case)
    assert_condition(case["provider_operations_allowed"] is False, case)
    assert_condition(case["runtime_behavior_change_allowed"] is False, case)
    assert_condition(case["runtime_activation_allowed"] is False, case)
    assert_condition(case["baseline_fingerprints"] == EXPECTED_BASELINE_FINGERPRINTS, case)
    from runtime.contracts.emotion_state_contracts import contract_self_check
    from scripts.emotion_state_cohort_release_contracts import (
        ALLOWED_SPEAKER_BASES,
        BOOLEAN_BOUNDARY_FIELDS,
        COHORT_RELEASE_FIELDS,
        MAX_AUTHORITATIVE_HISTORY_CANONICAL_BYTES,
        MAX_AUTHORITATIVE_HISTORY_ENTRIES,
        MAX_RELEASE_CONTRIBUTIONS_PER_SPEAKER,
        METRIC_ALLOWLIST_V1,
        METRIC_ALLOWLIST_VERSION_V1,
        MIN_RELEASE_SPEAKERS,
        RELEASE_SCOPE,
        RESERVED_DISABLED_SPEAKER_BASE,
        cohort_release_contract_self_check,
        cohort_release_fixture_descriptor,
        cohort_release_schema_descriptor,
    )

    assert_condition(contract_self_check() == "pass", "emotion-state contract self-check failed")
    cohort_schema = read_json(COHORT_RELEASE_SCHEMA)
    assert_condition(
        json.dumps(
            cohort_schema,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        == json.dumps(
            cohort_release_schema_descriptor(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ),
        cohort_schema,
    )
    assert_condition(
        cohort_schema["schema_id"] == "emotion-state-cohort-release-evidence-v1",
        cohort_schema,
    )
    assert_condition(
        type(cohort_schema["schema_version"]) is int
        and cohort_schema["schema_version"] == 1,
        cohort_schema,
    )
    assert_condition(
        len(cohort_schema["required_fields"]) == len(COHORT_RELEASE_FIELDS)
        and set(cohort_schema["required_fields"]) == COHORT_RELEASE_FIELDS,
        cohort_schema,
    )
    assert_condition(
        cohort_schema["description"] == RELEASE_SCOPE,
        cohort_schema,
    )
    assert_condition(
        cohort_schema["allowed_speaker_bases"] == sorted(ALLOWED_SPEAKER_BASES),
        cohort_schema,
    )
    assert_condition(
        cohort_schema["reserved_disabled_speaker_basis"]
        == RESERVED_DISABLED_SPEAKER_BASE,
        cohort_schema,
    )
    assert_condition(
        cohort_schema["max_contribution_per_speaker"]
        == MAX_RELEASE_CONTRIBUTIONS_PER_SPEAKER,
        cohort_schema,
    )
    assert_condition(
        cohort_schema["minimum_unique_speakers"] == MIN_RELEASE_SPEAKERS,
        cohort_schema,
    )
    assert_condition(
        cohort_schema["minimum_unique_speakers_per_output_cell"]
        == MIN_RELEASE_SPEAKERS,
        cohort_schema,
    )
    assert_condition(
        cohort_schema["metric_allowlist_version"] == METRIC_ALLOWLIST_VERSION_V1,
        cohort_schema,
    )
    assert_condition(
        cohort_schema["metric_allowlist"] == list(METRIC_ALLOWLIST_V1),
        cohort_schema,
    )
    assert_condition(
        cohort_schema["false_constants"]
        == {field: False for field in BOOLEAN_BOUNDARY_FIELDS},
        cohort_schema,
    )
    assert_condition(
        cohort_schema["cross_corpus_identity_evidence_digest"] is None,
        cohort_schema,
    )
    assert_condition(
        cohort_schema["authoritative_history_boundary"][
            "max_authoritative_history_entries"
        ]
        == MAX_AUTHORITATIVE_HISTORY_ENTRIES,
        cohort_schema,
    )
    assert_condition(
        cohort_schema["authoritative_history_boundary"][
            "max_authoritative_history_canonical_bytes"
        ]
        == MAX_AUTHORITATIVE_HISTORY_CANONICAL_BYTES,
        cohort_schema,
    )
    cohort_fixtures = read_json(COHORT_RELEASE_FIXTURES)
    assert_condition(
        json.dumps(
            cohort_fixtures,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        == json.dumps(
            cohort_release_fixture_descriptor(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ),
        cohort_fixtures,
    )
    expected_scenarios = {
        "twelve_calls_four_speakers",
        "ten_calls_ten_speakers",
        "twenty_turns_five_speakers",
        "duplicate_public_actor_ids",
        "cross_corpus_same_bare_id",
        "missing_speaker_basis",
        "call_id_as_speaker",
        "forbidden_identity_basis",
        "over_contribution",
        "sparse_output_cell",
        "overlapping_release",
        "valid_replacement",
    }
    assert_condition(
        set(cohort_fixtures["scenarios"]) == expected_scenarios,
        cohort_fixtures,
    )
    assert_condition(
        cohort_fixtures["max_authoritative_history_entries"]
        == MAX_AUTHORITATIVE_HISTORY_ENTRIES
        and cohort_fixtures["max_authoritative_history_canonical_bytes"]
        == MAX_AUTHORITATIVE_HISTORY_CANONICAL_BYTES,
        cohort_fixtures,
    )
    assert_condition(
        all(
            isinstance(parameters, dict)
            and "records" not in parameters
            and "speaker_ids" not in parameters
            for parameters in cohort_fixtures["scenarios"].values()
        ),
        cohort_fixtures,
    )
    assert_condition(
        cohort_fixtures["private_data_access_allowed"] is False
        and cohort_fixtures["provider_operations_allowed"] is False
        and cohort_fixtures["runtime_influence_allowed"] is False,
        cohort_fixtures,
    )
    assert_condition(
        cohort_release_contract_self_check() == "pass",
        "cohort release contract self-check failed",
    )


def validate_patterns() -> None:
    from runtime.contracts.emotion_pattern_contracts import pattern_contract_self_check

    assert_condition(pattern_contract_self_check() == "pass", "pattern contract self-check failed")


def validate_brain_extension() -> None:
    from runtime.contracts.emotion_state_brain_extension import brain_extension_self_check

    assert_condition(brain_extension_self_check() == "pass", "BRAIN extension self-check failed")
    if _active_phase_a_guard_context():
        return
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_brain_002_runtime_state_schema.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert_condition(completed.returncode == 0, completed.stdout + completed.stderr)


def validate_split_v2() -> None:
    from scripts.emotion_state_split_manifest_v2_contracts import (
        split_manifest_v2_self_check,
    )

    assert_condition(
        split_manifest_v2_self_check() == "pass",
        "split manifest v2 contract self-check failed",
    )


def validate_cohort() -> None:
    from scripts.emotion_state_cohort_release_contracts import (
        cohort_release_contract_self_check,
    )

    assert_condition(
        cohort_release_contract_self_check() == "pass",
        "cohort release contract self-check failed",
    )


def validate_materials() -> None:
    from scripts.build_emotion_state_public_dataset_manifests import (
        validate_existing_dataset_evidence,
    )

    validate_existing_dataset_evidence(project_root=ROOT)


def _active_phase_a_guard_context() -> bool:
    guard_module = sys.modules.get("sitecustomize")
    policy_anchor = os.environ.get("EMOTION_STATE_PHASE_A_GUARD_POLICY")
    project_anchor = os.environ.get("EMOTION_STATE_PHASE_A_PROJECT_ROOT")
    guard_site = getattr(guard_module, "__file__", None)
    if not all(
        isinstance(value, str)
        for value in (policy_anchor, project_anchor, guard_site)
    ):
        return False
    try:
        project_root = ROOT.resolve(strict=True)
        return (
            subprocess.Popen
            is getattr(guard_module, "_GuardedPopen", None)
            and Path(project_anchor).resolve(strict=True) == project_root
            and Path(policy_anchor).resolve(strict=True)
            == project_root
            / "research/sources/emotion_state/"
            "phase_a_verification_guard_policy.json"
            and Path(guard_site).resolve(strict=True)
            == project_root
            / "scripts/emotion_state_phase_a_guard_site/sitecustomize.py"
        )
    except (OSError, RuntimeError, ValueError):
        return False


def validate_prepublication_inputs(mode: str) -> None:
    assert_condition(
        isinstance(mode, str) and mode in {"material-pending", "complete"},
        "prepublication mode must be material-pending or complete",
    )
    assert_condition(RUNNER.exists(), f"missing runner: {RUNNER.relative_to(ROOT)}")
    validate_source()
    validate_contracts()
    validate_split_v2()
    validate_cohort()
    validate_patterns()
    validate_brain_extension()
    guarded = _active_phase_a_guard_context()
    if not guarded:
        baseline_gate = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "validate_exp_002_frozen_response_baseline.py"),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=60,
            check=False,
        )
        assert_condition(
            baseline_gate.returncode == 0,
            baseline_gate.stdout + baseline_gate.stderr,
        )
    if mode == "complete" and not guarded:
        validate_materials()


def _readback_pair(
    result_path: Path,
    report_path: Path,
) -> dict[str, Any]:
    from scripts.emotion_state_phase_a_contracts import (
        render_phase_a_report,
        validate_complete_payload,
        validate_material_pending_payload,
    )
    from scripts.run_emotion_state_001_phase_a_contracts import (
        _validate_canonical_pair_metadata,
        verify_evidence_pair_bytes,
    )

    assert_condition(result_path.parent == report_path.parent, "canonical directory mismatch")
    _validate_canonical_pair_metadata(result_path, report_path)
    assert_condition(
        {path.name for path in result_path.parent.iterdir()}
        == {result_path.name, report_path.name},
        "canonical checkpoint directory must contain exactly result.json and report.md",
    )
    result_bytes = result_path.read_bytes()
    report_bytes = report_path.read_bytes()
    verify_evidence_pair_bytes(result_bytes, report_bytes)
    result = json.loads(result_bytes.decode("utf-8"))
    assert_condition(isinstance(result, dict), "checkpoint result must be an object")
    mode_status = (result.get("mode"), result.get("status"))
    if mode_status == ("material_pending", "material_pending"):
        validate_material_pending_payload(result)
        expected_complete = False
    elif mode_status == ("complete", "complete"):
        validate_complete_payload(result, root=ROOT)
        expected_complete = True
    else:
        raise ValueError("checkpoint mode/status pair is invalid")
    result_sha256 = hashlib.sha256(result_bytes).hexdigest().upper()
    expected_report = render_phase_a_report(result, result_sha256=result_sha256)
    assert_condition(
        report_bytes.decode("utf-8")
        == expected_report.replace("\n", os.linesep),
        "result/report publication pair is not deterministic",
    )
    _validate_report_semantics(result, report_bytes.decode("utf-8"))
    assert_condition(
        result.get("checkpoint_id") == "EMOTION-STATE-001-phase-a-contracts",
        result,
    )
    assert_condition(
        result.get("readiness_boundary", {}).get("phase_a_complete")
        is expected_complete,
        result,
    )
    return result


def _validate_report_semantics(
    payload: dict[str, Any],
    report_text: str,
) -> None:
    mismatch = "report semantic mode mismatch"
    summary = payload.get("summary")
    readiness_boundary = payload.get("readiness_boundary")
    assert_condition(isinstance(summary, dict), mismatch)
    assert_condition(isinstance(readiness_boundary, dict), mismatch)
    state = (
        payload.get("mode"),
        payload.get("status"),
        readiness_boundary.get("phase_a_complete"),
        summary.get("material_verification_status"),
    )
    pending_claims = (
        (
            "This material-pending artifact validates source provenance, selected "
            "public-dataset IDs, and offline contract artifacts only; Phase A "
            "remains incomplete until separately authorized local materials are "
            "verified."
        ),
        "Phase A remains incomplete",
        "Per-public-dataset manifests remain open and unverified",
        "- Material verification status: `pending`",
        "- Phase A complete: `False`",
    )
    complete_claims = (
        (
            "This complete offline Phase A artifact validates source provenance, "
            "the two selected public-dataset manifests and local material "
            "hash/quality inventories, offline contracts, and the privacy-preserving "
            "cohort-release gate; Phase A completion is limited to "
            "source_provenance_dataset_manifests_offline_contracts_and_cohort_release_gate_only."
        ),
        (
            "Source adaptation remains blocked by the current instruction, absent "
            "observed license metadata, undefined Phase B reuse scope, pending "
            "Phase B attribution wording, and separate Phase B approval."
        ),
        (
            "The two selected public-dataset manifests and local material "
            "hash/quality inventories are verified for this bounded offline "
            "checkpoint. Public-dataset model evaluation remains not started and "
            "unauthorized. Runtime activation remains blocked."
        ),
        (
            "Live aggregate release remains blocked; the offline synthetic "
            "cohort-release contract is not authorization for live data, customer "
            "use, or aggregate release."
        ),
        "- Material verification status: `verified`",
        "- Phase A complete: `True`",
    )
    if state == ("material_pending", "material_pending", False, "pending"):
        assert_condition(
            all(claim in report_text for claim in pending_claims)
            and not any(claim in report_text for claim in complete_claims),
            mismatch,
        )
    elif state == ("complete", "complete", True, "verified"):
        assert_condition(
            all(claim in report_text for claim in complete_claims)
            and not any(claim in report_text for claim in pending_claims),
            mismatch,
        )
    else:
        raise AssertionError(mismatch)


def validate_candidate_readback(receipt_path: str | Path) -> None:
    from scripts.run_emotion_state_001_phase_a_contracts import (
        validate_candidate_evidence_pair,
    )

    payload = validate_candidate_evidence_pair(
        receipt_path,
        result_path=RESULT,
        report_path=REPORT,
        recovery_dir=RECOVERY_DIR,
    )
    _validate_report_semantics(payload, REPORT.read_text(encoding="utf-8"))


def validate_checkpoint_readback() -> None:
    from scripts.run_emotion_state_001_phase_a_contracts import (
        JOURNAL_NAME,
        LOCK_NAME,
    )

    assert_condition(
        not (RECOVERY_DIR / JOURNAL_NAME).exists(),
        "accepted checkpoint readback requires no live publication transaction",
    )
    residual_transaction_artifacts = (
        sorted(
            path.name
            for path in RECOVERY_DIR.iterdir()
            if path.name != LOCK_NAME
        )
        if RECOVERY_DIR.exists()
        else []
    )
    assert_condition(
        not residual_transaction_artifacts,
        (
            "accepted checkpoint readback requires no residual publication "
            "transaction or receipt artifacts"
        ),
    )
    _readback_pair(RESULT, REPORT)


SECTIONS: dict[str, Callable[..., None]] = {
    "source": validate_source,
    "contracts": validate_contracts,
    "split-v2": validate_split_v2,
    "cohort": validate_cohort,
    "materials": validate_materials,
    "patterns": validate_patterns,
    "brain": validate_brain_extension,
    "prepublication": validate_prepublication_inputs,
    "candidate": validate_candidate_readback,
    "checkpoint": validate_checkpoint_readback,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate EMOTION-STATE-001 Phase A contracts.")
    parser.add_argument("--section", choices=list(SECTIONS), required=True)
    parser.add_argument("--mode", choices=("material-pending", "complete"))
    parser.add_argument("--receipt")
    args = parser.parse_args()
    if args.section == "prepublication":
        if args.mode is None or args.receipt is not None:
            parser.error("prepublication validation requires --mode and forbids --receipt")
    elif args.section == "candidate":
        if args.receipt is None or args.mode is not None:
            parser.error("candidate validation requires --receipt and forbids --mode")
    elif args.mode is not None or args.receipt is not None:
        parser.error("--mode and --receipt are section-specific")
    return args


def main() -> int:
    args = parse_args()
    try:
        if args.section == "prepublication":
            validate_prepublication_inputs(args.mode)
        elif args.section == "candidate":
            validate_candidate_readback(args.receipt)
        else:
            SECTIONS[args.section]()
    except (
        AssertionError,
        KeyError,
        OSError,
        RuntimeError,
        subprocess.TimeoutExpired,
        ValueError,
    ) as exc:
        print(f"EMOTION-STATE-001 Phase A validation failed: {exc}")
        return 1
    print(f"EMOTION-STATE-001 Phase A validation passed: {args.section}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
