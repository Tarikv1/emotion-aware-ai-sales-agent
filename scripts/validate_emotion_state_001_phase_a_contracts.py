#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
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
CODEBOOK = ROOT / "docs" / "data" / "EMOTION_STATE_001_ANNOTATION_CODEBOOK.md"
THESIS_REFERENCE_REGISTRY = ROOT / "docs" / "thesis" / "THESIS_REFERENCE_REGISTRY.md"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "emotion-state-001-phase-a-contracts.json"
RUNNER = ROOT / "scripts" / "run_emotion_state_001_phase_a_contracts.py"
RESULT = ROOT / "research" / "experiments" / "generated" / "EMOTION-STATE-001-phase-a-contracts" / "result.json"
REPORT = RESULT.with_name("report.md")
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
    assert_condition(manifest["source_repository_url"] is None, manifest)
    assert_condition(manifest["source_repository_url_status"] == "unverified", manifest)
    assert_condition(manifest["source_revision"] is None, manifest)
    assert_condition(manifest["source_revision_status"] == "unverified", manifest)
    assert_condition(manifest["source_archive_date"] is None, manifest)
    assert_condition(manifest["source_archive_date_status"] == "unverified", manifest)
    assert_condition(manifest["observed_license_status"] == "unverified_not_relied_on_for_permission", manifest)
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
    assert_condition(manifest["adaptation_blockers"] == [
        "source_repository_url_unverified",
        "source_revision_or_authoritative_archive_date_unverified",
        "phase_b_reuse_scope_not_defined",
        "phase_b_attribution_wording_pending",
        "phase_b_approval_not_granted",
    ], manifest)
    expected_reviewed_files = [
        {
            "path": "src/features/temporal/speech_prosody.py",
            "reuse_status": "inspiration_only",
            "phase_a_action": "reviewed_no_code_adapted",
        },
        {
            "path": "src/features/temporal/speech_turn_dynamics.py",
            "reuse_status": "inspiration_only",
            "phase_a_action": "reviewed_no_code_adapted",
        },
        {
            "path": "src/aggregation/speech_call_readiness.py",
            "reuse_status": "excluded_from_emotion_labels",
            "phase_a_action": "reviewed_no_code_adapted",
        },
    ]
    assert_condition(manifest["reviewed_files"] == expected_reviewed_files, manifest)
    if manifest["source_repository_url_status"] != "verified":
        assert_condition(manifest["source_repository_url"] is None, manifest)
        assert_condition(manifest["adaptation_allowed"] is False, manifest)
    if manifest["source_revision_status"] != "verified" and manifest["source_archive_date_status"] != "verified":
        assert_condition(manifest["source_revision"] is None, manifest)
        assert_condition(manifest["source_archive_date"] is None, manifest)
        assert_condition(manifest["adaptation_allowed"] is False, manifest)
    derived_adaptation_allowed = all([
        manifest["source_repository_url_status"] == "verified",
        manifest["source_revision_status"] == "verified" or manifest["source_archive_date_status"] == "verified",
        manifest["attribution"]["phase_b_reuse_scope_status"] == "approved",
        bool(manifest["attribution"]["phase_b_reuse_scope"]),
        manifest["attribution"]["phase_b_attribution_wording_status"] == "recorded",
        isinstance(manifest["attribution"]["phase_b_wording"], str) and bool(manifest["attribution"]["phase_b_wording"].strip()),
        manifest["phase_b_approval"]["status"] == "approved",
        manifest["phase_b_approval"]["approved"] is True,
        isinstance(manifest["phase_b_approval"]["approval_reference"], str) and bool(manifest["phase_b_approval"]["approval_reference"].strip()),
    ])
    assert_condition(manifest["adaptation_allowed"] is derived_adaptation_allowed, manifest)
    dataset_contract = read_json(DATASET_CONTRACT)
    assert_condition(dataset_contract["schema_id"] == "emotion-state-dataset-manifest-v1", dataset_contract)
    assert_condition(set(dataset_contract["required_fields"]) == {
        "dataset_id", "canonical_source_url", "release_or_version", "accessed_on",
        "terms_or_license", "access_restrictions", "local_file_hashes", "source_label",
        "source_labels", "project_label_mapping", "excluded_labels", "language", "domain",
        "domain_limitations", "permitted_research_lanes", "redistribution_status",
    }, dataset_contract)
    assert_condition(set(dataset_contract["allowed_source_labels"]) == {
        "public-only", "private-restricted", "mixed-source", "synthetic-only",
    }, dataset_contract)
    assert_condition(dataset_contract["selected_public_datasets"] == [], dataset_contract)
    assert_condition(dataset_contract["runtime_influence_allowed"] is False, dataset_contract)
    assert_condition(dataset_contract["domain_boundary"] == "acted_and_non_sales_corpora_support_offline_thesis_comparison_only", dataset_contract)
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
    require_text(SOURCE_NOTES, ["inspiration only", "source_repository_url_unverified", "No code was copied"])
    require_text(CODEBOOK, [
        "not_inferable", "ambiguous", "Krippendorff", "three independent reviewers",
        "practice set", "`none` means", "abstention-policy error", "redacted, nonreversible",
        "evidence:uuid:", "Retain reviewer-level disagreement", "Derive every split dependency summary",
    ])
    require_text(ROOT / "docs" / "third-party-inspirations.md", ["Creative Analysis Engine", "research/sources/creative_analysis_engine/source_manifest.json"])
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
    assert_condition(case["source_label"] == "synthetic-only", case)
    assert_condition(case["selected_public_datasets"] == [], case)
    assert_condition(case["private_data_access_allowed"] is False, case)
    assert_condition(case["provider_operations_allowed"] is False, case)
    assert_condition(case["runtime_behavior_change_allowed"] is False, case)
    assert_condition(case["runtime_activation_allowed"] is False, case)
    assert_condition(case["baseline_fingerprints"] == EXPECTED_BASELINE_FINGERPRINTS, case)
    from runtime.contracts.emotion_state_contracts import contract_self_check

    assert_condition(contract_self_check() == "pass", "emotion-state contract self-check failed")


def validate_patterns() -> None:
    from runtime.contracts.emotion_pattern_contracts import pattern_contract_self_check

    assert_condition(pattern_contract_self_check() == "pass", "pattern contract self-check failed")


def validate_brain_extension() -> None:
    from runtime.contracts.emotion_state_brain_extension import brain_extension_self_check

    assert_condition(brain_extension_self_check() == "pass", "BRAIN extension self-check failed")
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_brain_002_runtime_state_schema.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert_condition(completed.returncode == 0, completed.stdout + completed.stderr)


def validate_checkpoint() -> None:
    assert_condition(RUNNER.exists(), f"missing runner: {RUNNER.relative_to(ROOT)}")
    baseline_gate = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_exp_002_frozen_response_baseline.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert_condition(baseline_gate.returncode == 0, baseline_gate.stdout + baseline_gate.stderr)
    from scripts.run_emotion_state_001_phase_a_contracts import (
        DEFAULT_CASE as RUNNER_DEFAULT_CASE,
        DEFAULT_OUTPUT_DIR as RUNNER_DEFAULT_OUTPUT_DIR,
        resolve_project_path,
    )

    assert_condition(
        resolve_project_path(str(RUNNER_DEFAULT_CASE), allowed_root=RUNNER_DEFAULT_CASE.parent)
        == RUNNER_DEFAULT_CASE.resolve(strict=False),
        "runner rejected its fixed case path",
    )
    for blocked_path in (
        ROOT.parent / "outside-result.json",
        ROOT / "runtime" / "overwrite-result.json",
        ROOT / "data" / "private" / "blocked-result.json",
    ):
        try:
            resolve_project_path(str(blocked_path), allowed_root=RUNNER_DEFAULT_OUTPUT_DIR)
        except ValueError:
            pass
        else:
            raise AssertionError(f"runner accepted blocked output path: {blocked_path}")
    completed = subprocess.run(
        [sys.executable, str(RUNNER)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert_condition(completed.returncode == 0, completed.stdout + completed.stderr)
    result = read_json(RESULT)
    report = require_text(REPORT, [
        "EMOTION-STATE-001", "offline", "all of Phase A is complete",
        "Per-public-dataset manifests remain open", "Live aggregate release remains blocked",
        "Runtime activation remains blocked",
    ])
    assert_condition(result["checkpoint_id"] == "EMOTION-STATE-001-phase-a-contracts", result)
    assert_condition(result["archive_sha256"] == EXPECTED_ARCHIVE_SHA256, result)
    assert_condition(
        result["status"] == "contract_artifact_validation_only_source_dataset_and_privacy_gates_open",
        result,
    )
    assert_condition(result["summary"]["provider_operations_performed_by_runner"] is False, result)
    assert_condition(result["summary"]["private_data_read_by_runner"] is False, result)
    assert_condition(result["summary"]["runtime_behavior_changed_by_runner"] is False, result)
    assert_condition(result["summary"]["code_adaptation_started"] is False, result)
    assert_condition(result["summary"]["runtime_activation_allowed"] is False, result)
    assert_condition(result["summary"]["source_adaptation_allowed"] is False, result)
    assert_condition(result["readiness_boundary"] == {
        "phase_a_contract_artifacts_built": True,
        "phase_a_complete": False,
        "full_repository_gate_claimed_by_this_artifact": False,
        "live_aggregate_release_unblocked": False,
        "phase_b_unblocked": False,
        "public_dataset_evaluation_unblocked": False,
        "private_research_unblocked": False,
        "provider_feasibility_unblocked": False,
        "runtime_activation_unblocked": False,
    }, result)
    expected_checks = {
        "exp_002_frozen_response_baseline",
        "emotion_state_annotation_contracts",
        "emotion_state_contracts",
        "emotion_pattern_contracts",
        "emotion_state_brain_extension",
    }
    assert_condition(set(result["summary"]["contract_checks"]) == expected_checks, result)
    assert_condition(set(result["summary"]["contract_checks"].values()) == {"pass"}, result)
    assert_condition(result["summary"]["contract_check_count"] == len(expected_checks), result)
    assert_condition(result["baseline_fingerprints"] == EXPECTED_BASELINE_FINGERPRINTS, result)
    assert_condition(all(
        isinstance(digest, str) and len(digest) == 64 and all(character in "0123456789ABCDEF" for character in digest)
        for digest in result["baseline_fingerprints"].values()
    ), result)
    assert_condition("production ready" not in report.lower(), "report overclaims readiness")
    rendered_packet = ROOT / ".tmp" / "emotion-state-001" / "EXP-002-prompt-packet.md"
    baseline_run = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_prompt_baseline.py"),
            "--cases",
            str(ROOT / "research" / "experiments" / "cases" / "exp-002-dataset-derived.json"),
            "--out",
            str(rendered_packet),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert_condition(baseline_run.returncode == 0, baseline_run.stdout + baseline_run.stderr)
    tracked_packet = ROOT / "research" / "experiments" / "generated" / "EXP-002" / "EXP-002-prompt-packet.md"
    assert_condition(
        normalized_prompt_packet_digest(tracked_packet) == EXPECTED_NORMALIZED_PROMPT_PACKET_SHA256,
        "tracked EXP-002 normalized prompt packet drifted from the frozen baseline",
    )
    assert_condition(
        normalized_prompt_packet_digest(rendered_packet) == EXPECTED_NORMALIZED_PROMPT_PACKET_SHA256,
        "EXP-002 normalized prompt packet drifted",
    )


SECTIONS: dict[str, Callable[[], None]] = {
    "source": validate_source,
    "contracts": validate_contracts,
    "patterns": validate_patterns,
    "brain": validate_brain_extension,
    "checkpoint": validate_checkpoint,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate EMOTION-STATE-001 Phase A contracts.")
    parser.add_argument("--section", choices=["all", *SECTIONS], default="all")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    selected = SECTIONS.values() if args.section == "all" else [SECTIONS[args.section]]
    try:
        for validator in selected:
            validator()
    except (AssertionError, KeyError, ValueError) as exc:
        print(f"EMOTION-STATE-001 Phase A validation failed: {exc}")
        return 1
    print(f"EMOTION-STATE-001 Phase A validation passed: {args.section}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
