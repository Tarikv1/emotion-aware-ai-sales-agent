from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.contracts.emotion_pattern_contracts import pattern_contract_self_check
from runtime.contracts.emotion_state_brain_extension import brain_extension_self_check
from runtime.contracts.emotion_state_contracts import contract_self_check
from scripts.emotion_state_annotation_contracts import annotation_contract_self_check
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

EXPECTED_CASE = {
    "checkpoint_id": "EMOTION-STATE-001-phase-a-contracts",
    "schema_version": 1,
    "source_label": "synthetic-only",
    "campaign_profile_id": "emotion-state-phase-a-fixture",
    "campaign_profile_version": "fixture-v1",
    "selected_public_datasets": [],
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
        "source_repository_url": None,
        "source_repository_url_status": "unverified",
        "source_revision": None,
        "source_revision_status": "unverified",
        "source_archive_date": None,
        "source_archive_date_status": "unverified",
        "observed_license_status": "unverified_not_relied_on_for_permission",
    }
    mismatched = {
        key: manifest.get(key)
        for key, value in expected_values.items()
        if manifest.get(key) != value
    }
    if mismatched:
        raise ValueError(f"invalid source manifest boundary: {sorted(mismatched)}")
    expected_booleans = {
        "adaptation_allowed": False,
        "runtime_dependency_added": False,
        "project_local_only": True,
    }
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


def build_phase_a_payload(case_path: Path, *, root: Path) -> dict[str, Any]:
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
    code_adaptation_started = any(manifest[field] for field in MATERIAL_FIELDS)
    baseline = {
        relative_path: sha256_file(root / relative_path)
        for relative_path in EXPECTED_BASELINE_FINGERPRINTS
    }
    if baseline != case["baseline_fingerprints"]:
        raise ValueError("frozen baseline fingerprint drift")
    checks = {
        "exp_002_frozen_response_baseline": frozen_baseline_self_check(root),
        "emotion_state_annotation_contracts": annotation_contract_self_check(),
        "emotion_state_contracts": contract_self_check(),
        "emotion_pattern_contracts": pattern_contract_self_check(),
        "emotion_state_brain_extension": brain_extension_self_check(),
    }
    if set(checks.values()) != {"pass"}:
        raise ValueError("one or more Phase A contract self-checks failed")
    return {
        "checkpoint_id": "EMOTION-STATE-001-phase-a-contracts",
        "schema_version": 1,
        "status": "contract_artifact_validation_only_source_dataset_and_privacy_gates_open",
        "summary": {
            "contract_check_count": len(checks),
            "contract_checks": checks,
            "baseline_fingerprint_count": len(baseline),
            "selected_public_dataset_count": len(case["selected_public_datasets"]),
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
        "readiness_boundary": {
            "phase_a_contract_artifacts_built": True,
            "phase_a_complete": False,
            "full_repository_gate_claimed_by_this_artifact": False,
            "live_aggregate_release_unblocked": False,
            "phase_b_unblocked": False,
            "public_dataset_evaluation_unblocked": False,
            "private_research_unblocked": False,
            "provider_feasibility_unblocked": False,
            "runtime_activation_unblocked": False,
        },
    }


def render_phase_a_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    return "\n".join([
        "# EMOTION-STATE-001 Phase A Contract Report",
        "",
        "This artifact validates offline contract artifacts only; it does not claim that the full repository gate or all of Phase A is complete.",
        "",
        f"- Contract checks: `{summary['contract_check_count']}`",
        f"- Baseline fingerprints: `{summary['baseline_fingerprint_count']}`",
        f"- Selected public datasets: `{summary['selected_public_dataset_count']}`",
        f"- Source URL status: `{summary['source_repository_url_status']}`",
        f"- Code adaptation started: `{summary['code_adaptation_started']}`",
        f"- Frozen EXP-002 evaluator provenance status: `{summary['frozen_exp_002_evaluator_provenance_status']}`",
        f"- Provider operations performed by this runner: `{summary['provider_operations_performed_by_runner']}`",
        f"- Private data read by this runner: `{summary['private_data_read_by_runner']}`",
        f"- Runtime behavior changed by this runner: `{summary['runtime_behavior_changed_by_runner']}`",
        "",
        "Source adaptation remains blocked by the source URL, revision or authoritative archive date, Phase B reuse scope, Phase B attribution wording, and separate Phase B approval.",
        "Per-public-dataset manifests remain open. Acted and non-sales corpora can support offline thesis comparison only. Runtime activation remains blocked.",
        "Live aggregate release remains blocked until a separately approved privacy-preserving unique-speaker cohort-release and dedup gate exists.",
        "",
        "This is not production readiness, real-customer validation, PSTN/ASR/latency validation, provider-feasibility evidence, runtime activation, or proof of internal customer emotion.",
        "",
    ])
