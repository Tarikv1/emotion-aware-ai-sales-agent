from __future__ import annotations

import hashlib
import json
from pathlib import Path
from collections.abc import Mapping
from typing import Any

from runtime.contracts.emotion_pattern_contracts import pattern_contract_self_check
from runtime.contracts.emotion_state_brain_extension import brain_extension_self_check
from runtime.contracts.emotion_state_contracts import contract_self_check
from scripts.emotion_state_annotation_contracts import annotation_contract_self_check
from scripts.emotion_state_cohort_release_contracts import cohort_release_contract_self_check
from scripts.exp_002_frozen_response_baseline import frozen_baseline_self_check


EXPECTED_ARCHIVE_SHA256 = "E579B966E226F2AF6E4F8F8203C7189FEC94FB448EFC09B4B6640C10A398ECCC"
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
MATERIAL_PENDING_CONTRACT_STATUSES = {
    "public_dataset_contract": "pass",
    "split_manifest_v2_contract": "pass",
    "cohort_release_contract": "pass",
}
MATERIAL_PENDING_COMPLETION_SCOPE = (
    "source_provenance_dataset_selection_and_offline_contracts_only_"
    "material_verification_pending"
)
MATERIAL_PENDING_BLOCKERS = [
    "dataset_download_not_authorized",
    "selected_dataset_manifests_not_verified",
]

EXPECTED_CASE = {
    "checkpoint_id": "EMOTION-STATE-001-phase-a-contracts",
    "schema_version": 2,
    "source_label": "public-only",
    "campaign_profile_id": "emotion-state-phase-a-fixture",
    "campaign_profile_version": "fixture-v2",
    "selected_public_datasets": list(SELECTED_PUBLIC_DATASET_IDS),
    "dataset_download_authorized": False,
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
    if "phase_a_complete" in evidence:
        raise ValueError("phase_a_complete is derived-only and cannot be supplied")
    expected_fields = {
        "mode",
        "selected_dataset_ids",
        "dataset_download_authorized",
        "dataset_evidence",
        "contract_statuses",
    }
    if set(evidence) != expected_fields:
        raise ValueError("invalid Phase A completion evidence fields")
    mode = evidence["mode"]
    if mode not in {"material_pending", "complete"}:
        raise ValueError("invalid Phase A completion mode")
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
    if dict(contract_statuses) != MATERIAL_PENDING_CONTRACT_STATUSES:
        raise ValueError("offline material-pending contract checks must all pass")

    if mode == "material_pending":
        if download_authorized is not False:
            raise ValueError("material-pending mode requires download authorization false")
        if dataset_evidence:
            raise ValueError("material-pending mode requires zero dataset-evidence entries")
        blockers = list(MATERIAL_PENDING_BLOCKERS)
        completion_scope = MATERIAL_PENDING_COMPLETION_SCOPE
    else:
        blockers = []
        if not download_authorized:
            blockers.append("dataset_download_not_authorized")
        if len(dataset_evidence) != len(SELECTED_PUBLIC_DATASET_IDS):
            blockers.append("selected_dataset_manifests_not_verified")
        blockers.append("complete_material_verification_gate_not_implemented")
        completion_scope = "complete_mode_material_verification_gate_pending"

    return {
        "phase_a_contract_artifacts_built": True,
        "phase_a_complete": False,
        "phase_a_completion_scope": completion_scope,
        "full_repository_gate_claimed_by_this_artifact": False,
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


def build_phase_a_payload(
    case_path: Path,
    *,
    root: Path,
    verification_evidence: Mapping[str, Any] | None = None,
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
        "baseline_fingerprints",
        "readiness_boundary",
    }
    if reserved_fields.intersection(normalized_verification):
        raise ValueError("verification evidence collides with checkpoint fields")
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
    completion = determine_phase_a_completion({
        "mode": "material_pending",
        "selected_dataset_ids": list(case["selected_public_datasets"]),
        "dataset_download_authorized": case["dataset_download_authorized"],
        "dataset_evidence": [],
        "contract_statuses": contract_statuses,
    })
    blockers = completion.pop("blocking_reason_codes")
    payload = {
        "checkpoint_id": "EMOTION-STATE-001-phase-a-contracts",
        "schema_version": 2,
        "mode": "material_pending",
        "status": "material_pending",
        "selected_public_datasets": list(case["selected_public_datasets"]),
        "dataset_download_authorized": case["dataset_download_authorized"],
        "dataset_evaluation_started": case["dataset_evaluation_started"],
        "dataset_manifest_evidence": [],
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
            "dataset_download_authorized": case["dataset_download_authorized"],
            "dataset_evaluation_started": case["dataset_evaluation_started"],
            "material_verification_status": "pending",
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
    payload.update(normalized_verification)
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
