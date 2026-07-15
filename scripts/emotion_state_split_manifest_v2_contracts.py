from __future__ import annotations

import re
from copy import deepcopy
from types import MappingProxyType
from typing import Any, Mapping

from scripts.emotion_state_public_dataset_contracts import AMI_DATASET_ID, CREMA_DATASET_ID


DEPENDENCY_KEYS_V2 = (
    "speaker", "call_session", "dialogue_dyad", "source_corpus",
    "scripted_scenario", "meeting_series", "recording_site",
)
DEPENDENCY_REQUIREMENTS = frozenset({
    "required", "covered_by_higher_dependency", "advisory", "not_applicable",
})
DEPENDENCY_STATUSES = frozenset({"available", "not_available", "not_applicable"})
PARTITIONS = ("training_discovery", "calibration", "balanced_diagnostic", "final_lockbox")

SPLIT_MANIFEST_V2_FIELDS = frozenset({
    "manifest_id",
    "dataset_manifest_ids",
    "dependency_profile_id",
    "highest_dependency_unit",
    "dependency_keys",
    "dependency_requirement_by_key",
    "dependency_status_by_key",
    "dependency_applicability_reason_by_key",
    "dependency_covering_key_by_key",
    "dependency_unknown_quarantine",
    "training_discovery",
    "calibration",
    "balanced_diagnostic",
    "final_lockbox",
    "metric_denominator_case_ids",
    "claim_denominator_case_ids",
    "frozen_candidate_family_digest",
    "confirmatory_claims_allowed",
    "runtime_influence_allowed",
})
PARTITION_FIELDS_V2: Mapping[str, frozenset[str]] = MappingProxyType({
    "training_discovery": frozenset({"case_ids", "dependency_groups"}),
    "calibration": frozenset({
        "case_ids", "dependency_groups", "prevalence_representative",
    }),
    "balanced_diagnostic": frozenset({
        "case_ids", "dependency_groups", "calibration_claims_allowed",
    }),
    "final_lockbox": frozenset({
        "case_ids", "dependency_groups", "prevalence_representative",
        "one_use_only", "open_count",
    }),
})
CASE_RECORD_FIELDS_V2 = frozenset({
    "case_id",
    "dataset_manifest_id",
    "dependency_value_by_key",
    "dependency_status_by_key",
})
QUARANTINE_FIELDS_V2 = frozenset({"case_ids", "reason_codes", "claims_allowed"})


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return deepcopy(value)


def _profile(
    dataset_manifest_id: str,
    requirements: dict[str, str],
    statuses: dict[str, str],
    applicability_reasons: dict[str, str],
    covering_keys: dict[str, str | None],
) -> dict[str, Any]:
    return {
        "dataset_manifest_id": dataset_manifest_id,
        "dependency_requirement_by_key": requirements,
        "dependency_status_by_key": statuses,
        "dependency_applicability_reason_by_key": applicability_reasons,
        "dependency_covering_key_by_key": covering_keys,
    }


DEPENDENCY_PROFILES_V2: Mapping[str, Mapping[str, Any]] = _freeze({
    "crema-d-session-nesting-verified": _profile(
        CREMA_DATASET_ID,
        {
            "speaker": "required",
            "call_session": "covered_by_higher_dependency",
            "dialogue_dyad": "not_applicable",
            "source_corpus": "required",
            "scripted_scenario": "required",
            "meeting_series": "not_applicable",
            "recording_site": "advisory",
        },
        {
            "speaker": "available",
            "call_session": "available",
            "dialogue_dyad": "not_applicable",
            "source_corpus": "available",
            "scripted_scenario": "available",
            "meeting_series": "not_applicable",
            "recording_site": "not_available",
        },
        {
            "speaker": "",
            "call_session": "",
            "dialogue_dyad": "crema_d_isolated_utterance_has_no_dialogue_dyad",
            "source_corpus": "",
            "scripted_scenario": "",
            "meeting_series": "crema_d_isolated_utterance_has_no_meeting_series",
            "recording_site": "",
        },
        {
            "speaker": None,
            "call_session": "speaker",
            "dialogue_dyad": None,
            "source_corpus": None,
            "scripted_scenario": None,
            "meeting_series": None,
            "recording_site": None,
        },
    ),
    "crema-d-session-nesting-unverified": _profile(
        CREMA_DATASET_ID,
        {
            "speaker": "required",
            "call_session": "advisory",
            "dialogue_dyad": "not_applicable",
            "source_corpus": "required",
            "scripted_scenario": "required",
            "meeting_series": "not_applicable",
            "recording_site": "advisory",
        },
        {
            "speaker": "available",
            "call_session": "not_available",
            "dialogue_dyad": "not_applicable",
            "source_corpus": "available",
            "scripted_scenario": "available",
            "meeting_series": "not_applicable",
            "recording_site": "not_available",
        },
        {
            "speaker": "",
            "call_session": "",
            "dialogue_dyad": "crema_d_isolated_utterance_has_no_dialogue_dyad",
            "source_corpus": "",
            "scripted_scenario": "",
            "meeting_series": "crema_d_isolated_utterance_has_no_meeting_series",
            "recording_site": "",
        },
        {
            "speaker": None,
            "call_session": None,
            "dialogue_dyad": None,
            "source_corpus": None,
            "scripted_scenario": None,
            "meeting_series": None,
            "recording_site": None,
        },
    ),
    "ami-scenario-series": _profile(
        AMI_DATASET_ID,
        {
            "speaker": "required",
            "call_session": "required",
            "dialogue_dyad": "not_applicable",
            "source_corpus": "required",
            "scripted_scenario": "required",
            "meeting_series": "required",
            "recording_site": "required",
        },
        {
            "speaker": "available",
            "call_session": "available",
            "dialogue_dyad": "not_applicable",
            "source_corpus": "available",
            "scripted_scenario": "available",
            "meeting_series": "available",
            "recording_site": "available",
        },
        {
            "speaker": "",
            "call_session": "",
            "dialogue_dyad": "ami_multi_party_meeting_has_no_dialogue_dyad",
            "source_corpus": "",
            "scripted_scenario": "",
            "meeting_series": "",
            "recording_site": "",
        },
        {key: None for key in DEPENDENCY_KEYS_V2},
    ),
    "ami-natural-standalone": _profile(
        AMI_DATASET_ID,
        {
            "speaker": "required",
            "call_session": "required",
            "dialogue_dyad": "not_applicable",
            "source_corpus": "required",
            "scripted_scenario": "not_applicable",
            "meeting_series": "not_applicable",
            "recording_site": "required",
        },
        {
            "speaker": "available",
            "call_session": "available",
            "dialogue_dyad": "not_applicable",
            "source_corpus": "available",
            "scripted_scenario": "not_applicable",
            "meeting_series": "not_applicable",
            "recording_site": "available",
        },
        {
            "speaker": "",
            "call_session": "",
            "dialogue_dyad": "ami_multi_party_meeting_has_no_dialogue_dyad",
            "source_corpus": "",
            "scripted_scenario": "ami_documented_natural_meeting_has_no_scripted_scenario",
            "meeting_series": "ami_documented_standalone_meeting_has_no_meeting_series",
            "recording_site": "",
        },
        {key: None for key in DEPENDENCY_KEYS_V2},
    ),
})


def dependency_profiles_v2_contract() -> dict[str, Any]:
    return _thaw(DEPENDENCY_PROFILES_V2)


def _require_exact_fields(value: Any, expected: frozenset[str], field: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError(f"{field} fields mismatch")
    return value


def _require_identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or any(char.isspace() for char in value):
        raise ValueError(f"{field} must be a nonempty opaque identifier")
    return value


def _require_identifier_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    for item in value:
        _require_identifier(item, field)
    if len(value) != len(set(value)):
        raise ValueError(f"{field} must contain unique identifiers")
    return value


def _require_dependency_map(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != set(DEPENDENCY_KEYS_V2):
        raise ValueError(f"{field} must have all seven dependency keys")
    return value


def validate_split_manifest_v2(
    payload: dict[str, Any],
    case_records: list[dict[str, Any]],
) -> dict[str, Any]:
    # 1. Exact top-level, partition, quarantine, and immutable-record fields.
    _require_exact_fields(payload, SPLIT_MANIFEST_V2_FIELDS, "split manifest v2")
    partition_case_ids: dict[str, list[str]] = {}
    partition_groups: dict[str, dict[str, list[str]]] = {}
    for partition_name in PARTITIONS:
        partition = _require_exact_fields(
            payload[partition_name],
            PARTITION_FIELDS_V2[partition_name],
            partition_name,
        )
        partition_case_ids[partition_name] = _require_identifier_list(
            partition["case_ids"],
            f"{partition_name}.case_ids",
        )
        groups = _require_dependency_map(
            partition["dependency_groups"],
            f"{partition_name}.dependency_groups",
        )
        partition_groups[partition_name] = {
            key: _require_identifier_list(groups[key], f"{partition_name}.dependency_groups.{key}")
            for key in DEPENDENCY_KEYS_V2
        }
    quarantine = _require_exact_fields(
        payload["dependency_unknown_quarantine"],
        QUARANTINE_FIELDS_V2,
        "dependency_unknown_quarantine",
    )
    if not isinstance(case_records, list) or not case_records:
        raise ValueError("split manifest v2 requires immutable case records")
    records_by_id: dict[str, dict[str, Any]] = {}
    for record in case_records:
        _require_exact_fields(record, CASE_RECORD_FIELDS_V2, "case dependency record")
        case_id = _require_identifier(record["case_id"], "case_id")
        if case_id in records_by_id:
            raise ValueError(f"duplicate immutable case record: {case_id}")
        _require_identifier(record["dataset_manifest_id"], "dataset_manifest_id")
        records_by_id[case_id] = record

    profile_id = payload["dependency_profile_id"]
    if not isinstance(profile_id, str) or profile_id not in DEPENDENCY_PROFILES_V2:
        raise ValueError(f"unsupported dependency profile: {profile_id}")
    profile = dependency_profiles_v2_contract()[profile_id]
    dataset_manifest_ids = _require_identifier_list(
        payload["dataset_manifest_ids"],
        "dataset_manifest_ids",
    )
    record_dataset_ids = {record["dataset_manifest_id"] for record in case_records}
    if len(dataset_manifest_ids) != 1 or len(record_dataset_ids) != 1:
        raise ValueError("split manifest v2 requires one dataset manifest ID")
    if dataset_manifest_ids[0] != profile["dataset_manifest_id"] or record_dataset_ids != set(dataset_manifest_ids):
        raise ValueError("dependency profile dataset mismatch")

    # 2. Exact dependency-key order.
    if payload["dependency_keys"] != list(DEPENDENCY_KEYS_V2):
        raise ValueError("dependency_keys must equal the frozen ordered v2 dimensions")

    # 3. Runtime isolation.
    if payload["runtime_influence_allowed"] is not False:
        raise ValueError("split manifest v2 cannot influence runtime")

    # 4. Every requirement/status map has all seven keys and matches one profile.
    requirements = _require_dependency_map(
        payload["dependency_requirement_by_key"],
        "dependency_requirement_by_key",
    )
    statuses = _require_dependency_map(
        payload["dependency_status_by_key"],
        "dependency_status_by_key",
    )
    applicability_reasons = _require_dependency_map(
        payload["dependency_applicability_reason_by_key"],
        "dependency_applicability_reason_by_key",
    )
    covering_keys = _require_dependency_map(
        payload["dependency_covering_key_by_key"],
        "dependency_covering_key_by_key",
    )
    if any(value not in DEPENDENCY_REQUIREMENTS for value in requirements.values()):
        raise ValueError("dependency_requirement_by_key contains an unsupported requirement")
    if any(value not in DEPENDENCY_STATUSES for value in statuses.values()):
        raise ValueError("dependency_status_by_key contains an unsupported status")
    for field, actual in (
        ("dependency_requirement_by_key", requirements),
        ("dependency_status_by_key", statuses),
        ("dependency_applicability_reason_by_key", applicability_reasons),
        ("dependency_covering_key_by_key", covering_keys),
    ):
        if actual != profile[field]:
            if field == "dependency_covering_key_by_key":
                raise ValueError(f"covering key map does not match dependency profile {profile_id}")
            raise ValueError(f"{field} does not match dependency profile {profile_id}")
    for case_id, record in records_by_id.items():
        values = _require_dependency_map(
            record["dependency_value_by_key"],
            f"{case_id}.dependency_value_by_key",
        )
        record_statuses = _require_dependency_map(
            record["dependency_status_by_key"],
            f"{case_id}.dependency_status_by_key",
        )
        if any(value not in DEPENDENCY_STATUSES for value in record_statuses.values()):
            raise ValueError(f"{case_id}.dependency_status_by_key contains an unsupported status")

    # 5. Not-applicable dimensions require a reason and never carry a value.
    for dependency_key in DEPENDENCY_KEYS_V2:
        is_not_applicable = requirements[dependency_key] == "not_applicable"
        if is_not_applicable:
            if statuses[dependency_key] != "not_applicable":
                raise ValueError(f"{dependency_key} not_applicable status mismatch")
            reason = applicability_reasons[dependency_key]
            if not isinstance(reason, str) or not reason.strip():
                raise ValueError(f"{dependency_key} not_applicable requires an applicability reason")
        elif applicability_reasons[dependency_key] != "":
            raise ValueError(f"{dependency_key} applicability reason must be empty")
        for case_id, record in records_by_id.items():
            record_status = record["dependency_status_by_key"][dependency_key]
            dependency_value = record["dependency_value_by_key"][dependency_key]
            if record_status == "not_applicable":
                if not is_not_applicable or dependency_value is not None:
                    raise ValueError(f"{case_id} {dependency_key} not_applicable is invalid")
            elif is_not_applicable:
                raise ValueError(f"{case_id} {dependency_key} must be not_applicable")
            elif record_status == "available":
                _require_identifier(dependency_value, f"{case_id}.{dependency_key}")
            elif dependency_value is not None:
                raise ValueError(f"{case_id} {dependency_key} not_available cannot carry a value")

    # 6. Only quarantined required dependencies may deviate to not_available.
    quarantine_case_ids = _require_identifier_list(quarantine["case_ids"], "quarantine.case_ids")
    quarantine_reason_codes = _require_identifier_list(
        quarantine["reason_codes"],
        "quarantine.reason_codes",
    )
    if quarantine["claims_allowed"] is not False:
        raise ValueError("dependency_unknown_quarantine claims_allowed must be false")
    unknown_by_case: dict[str, list[str]] = {}
    for case_id, record in records_by_id.items():
        deviations: list[str] = []
        for dependency_key in DEPENDENCY_KEYS_V2:
            baseline_status = statuses[dependency_key]
            record_status = record["dependency_status_by_key"][dependency_key]
            if record_status == baseline_status:
                continue
            if (
                requirements[dependency_key] == "required"
                and baseline_status == "available"
                and record_status == "not_available"
            ):
                deviations.append(dependency_key)
                continue
            raise ValueError(
                f"{case_id} has mixed dependency profile status for {dependency_key}"
            )
        if deviations:
            unknown_by_case[case_id] = deviations
    expected_quarantine_ids = sorted(unknown_by_case)
    if set(quarantine_case_ids) != set(expected_quarantine_ids):
        raise ValueError("required/not_available cases must appear only in dependency_unknown_quarantine")
    expected_reason_codes = sorted({
        f"{dependency_key}:required_not_available"
        for dependency_keys in unknown_by_case.values()
        for dependency_key in dependency_keys
    })
    if set(quarantine_reason_codes) != set(expected_reason_codes):
        raise ValueError("dependency_unknown_quarantine reason_codes mismatch")

    # 7. Covered dependencies require an available covering key and proven nesting.
    non_quarantine_ids = set(records_by_id) - set(quarantine_case_ids)
    for dependency_key in DEPENDENCY_KEYS_V2:
        if requirements[dependency_key] != "covered_by_higher_dependency":
            if covering_keys[dependency_key] is not None:
                raise ValueError(f"{dependency_key} has an unexpected covering key")
            continue
        covering_key = covering_keys[dependency_key]
        if (
            covering_key not in DEPENDENCY_KEYS_V2
            or covering_key == dependency_key
            or statuses[dependency_key] != "available"
            or statuses[covering_key] != "available"
        ):
            raise ValueError(f"{dependency_key} covering key is unavailable or unsupported")
        covered_to_covering: dict[str, str] = {}
        for case_id in non_quarantine_ids:
            record = records_by_id[case_id]
            covered_value = record["dependency_value_by_key"][dependency_key]
            covering_value = record["dependency_value_by_key"][covering_key]
            existing = covered_to_covering.setdefault(covered_value, covering_value)
            if existing != covering_value:
                raise ValueError(
                    f"{dependency_key} is not functionally nested under covering key {covering_key}"
                )
        seen_covering_groups: set[str] = set()
        for partition_name in PARTITIONS:
            covering_groups = {
                records_by_id[case_id]["dependency_value_by_key"][covering_key]
                for case_id in partition_case_ids[partition_name]
                if case_id in non_quarantine_ids
            }
            overlap = seen_covering_groups & covering_groups
            if overlap:
                raise ValueError(f"{covering_key} leakage across partitions: {sorted(overlap)}")
            seen_covering_groups.update(covering_groups)

    # 8. Advisory unavailable dimensions block confirmatory claims.
    if type(payload["confirmatory_claims_allowed"]) is not bool:
        raise ValueError("confirmatory_claims_allowed must be boolean")
    advisory_unavailable = any(
        requirements[key] == "advisory" and statuses[key] == "not_available"
        for key in DEPENDENCY_KEYS_V2
    )
    if advisory_unavailable and payload["confirmatory_claims_allowed"] is not False:
        raise ValueError("advisory/not_available requires confirmatory_claims_allowed=false")

    # 9. Quarantine is excluded from partitions and all metric/claim denominators.
    metric_denominators = _require_identifier_list(
        payload["metric_denominator_case_ids"],
        "metric_denominator_case_ids",
    )
    claim_denominators = _require_identifier_list(
        payload["claim_denominator_case_ids"],
        "claim_denominator_case_ids",
    )
    partition_id_set = {
        case_id
        for partition_name in PARTITIONS
        for case_id in partition_case_ids[partition_name]
    }
    quarantine_set = set(quarantine_case_ids)
    if quarantine_set & (partition_id_set | set(metric_denominators) | set(claim_denominators)):
        raise ValueError("quarantine cases cannot enter partitions or metric/claim denominators")

    # 10. Case IDs and every dependency group remain partition-disjoint.
    seen_case_ids: set[str] = set()
    seen_dependency_groups = {key: set() for key in DEPENDENCY_KEYS_V2}
    for partition_name in PARTITIONS:
        case_overlap = seen_case_ids & set(partition_case_ids[partition_name])
        if case_overlap:
            raise ValueError(f"case leakage across partitions: {sorted(case_overlap)}")
        seen_case_ids.update(partition_case_ids[partition_name])
        for dependency_key in DEPENDENCY_KEYS_V2:
            groups = set(partition_groups[partition_name][dependency_key])
            overlap = seen_dependency_groups[dependency_key] & groups
            if overlap:
                raise ValueError(f"{dependency_key} leakage across partitions: {sorted(overlap)}")
            seen_dependency_groups[dependency_key].update(groups)

    # 11. Groups and population are derived exactly from immutable case records.
    if seen_case_ids != non_quarantine_ids:
        raise ValueError("partition cases must equal all non-quarantined immutable case records")
    for partition_name in PARTITIONS:
        for case_id in partition_case_ids[partition_name]:
            if case_id not in records_by_id:
                raise ValueError(f"{partition_name} references an unknown immutable case record")
        derived_groups = {
            dependency_key: sorted({
                records_by_id[case_id]["dependency_value_by_key"][dependency_key]
                for case_id in partition_case_ids[partition_name]
                if records_by_id[case_id]["dependency_status_by_key"][dependency_key] == "available"
            })
            for dependency_key in DEPENDENCY_KEYS_V2
        }
        if partition_groups[partition_name] != derived_groups:
            raise ValueError(
                f"{partition_name}.dependency_groups do not match immutable case records"
            )
    if any(case_id not in non_quarantine_ids for case_id in metric_denominators + claim_denominators):
        raise ValueError("metric/claim denominators must reference non-quarantined partition cases")
    for record in records_by_id.values():
        source_corpus = record["dependency_value_by_key"]["source_corpus"]
        if source_corpus is not None and source_corpus != record["dataset_manifest_id"]:
            raise ValueError("source_corpus must equal dataset_manifest_id")

    _require_identifier(payload["manifest_id"], "manifest_id")
    if payload["highest_dependency_unit"] not in DEPENDENCY_KEYS_V2:
        raise ValueError("highest_dependency_unit must be a v2 dependency key")
    digest = payload["frozen_candidate_family_digest"]
    if not isinstance(digest, str) or re.fullmatch(r"[0-9A-F]{64}", digest) is None:
        raise ValueError("frozen_candidate_family_digest must be an uppercase SHA-256")
    if payload["calibration"]["prevalence_representative"] is not True:
        raise ValueError("calibration must preserve prevalence")
    if payload["balanced_diagnostic"]["calibration_claims_allowed"] is not False:
        raise ValueError("balanced diagnostic cannot support calibration claims")
    lockbox = payload["final_lockbox"]
    if lockbox["prevalence_representative"] is not True or lockbox["one_use_only"] is not True:
        raise ValueError("final lockbox controls are invalid")
    if type(lockbox["open_count"]) is not int or lockbox["open_count"] not in {0, 1}:
        raise ValueError("final lockbox may be opened at most once")
    return payload


def fixture_split_records_v2(
    include_required_unknown: bool = False,
    dependency_profile_id: str = "crema-d-session-nesting-verified",
) -> list[dict[str, Any]]:
    if dependency_profile_id not in DEPENDENCY_PROFILES_V2:
        raise ValueError(f"unsupported dependency profile: {dependency_profile_id}")
    profile = dependency_profiles_v2_contract()[dependency_profile_id]
    statuses = profile["dependency_status_by_key"]
    dataset_manifest_id = profile["dataset_manifest_id"]

    def value_for(key: str, suffix: str) -> str | None:
        if statuses[key] != "available":
            return None
        if key == "speaker":
            return "speaker-training"
        if key == "call_session":
            return f"call-session-{suffix}"
        if key == "source_corpus":
            return dataset_manifest_id
        if key == "scripted_scenario":
            return f"scripted-scenario-{suffix}"
        if key == "meeting_series":
            return "meeting-series-training"
        if key == "recording_site":
            return "recording-site-training"
        return None

    records = [
        {
            "case_id": f"case-training-{suffix}",
            "dataset_manifest_id": dataset_manifest_id,
            "dependency_value_by_key": {
                key: value_for(key, suffix) for key in DEPENDENCY_KEYS_V2
            },
            "dependency_status_by_key": dict(statuses),
        }
        for suffix in ("a", "b")
    ]
    if include_required_unknown:
        unknown = deepcopy(records[0])
        unknown["case_id"] = "case-unknown"
        unknown["dependency_value_by_key"]["speaker"] = None
        unknown["dependency_status_by_key"]["speaker"] = "not_available"
        records.append(unknown)
    return records


def fixture_split_manifest_v2(
    case_records: list[dict[str, Any]],
    dependency_profile_id: str = "crema-d-session-nesting-verified",
) -> dict[str, Any]:
    if dependency_profile_id not in DEPENDENCY_PROFILES_V2:
        raise ValueError(f"unsupported dependency profile: {dependency_profile_id}")
    profile = dependency_profiles_v2_contract()[dependency_profile_id]
    baseline_statuses = profile["dependency_status_by_key"]
    quarantine_ids = sorted(
        record["case_id"]
        for record in case_records
        if any(
            profile["dependency_requirement_by_key"][key] == "required"
            and baseline_statuses[key] == "available"
            and record["dependency_status_by_key"][key] == "not_available"
            for key in DEPENDENCY_KEYS_V2
        )
    )
    quarantine_reasons = sorted({
        f"{key}:required_not_available"
        for record in case_records
        if record["case_id"] in quarantine_ids
        for key in DEPENDENCY_KEYS_V2
        if profile["dependency_requirement_by_key"][key] == "required"
        and baseline_statuses[key] == "available"
        and record["dependency_status_by_key"][key] == "not_available"
    })
    training_case_ids = sorted(
        record["case_id"] for record in case_records if record["case_id"] not in quarantine_ids
    )
    records_by_id = {record["case_id"]: record for record in case_records}

    def groups_for(case_ids: list[str]) -> dict[str, list[str]]:
        return {
            key: sorted({
                records_by_id[case_id]["dependency_value_by_key"][key]
                for case_id in case_ids
                if records_by_id[case_id]["dependency_status_by_key"][key] == "available"
            })
            for key in DEPENDENCY_KEYS_V2
        }

    empty_groups = {key: [] for key in DEPENDENCY_KEYS_V2}
    return {
        "manifest_id": "emotion-state-split-manifest-v2-fixture",
        "dataset_manifest_ids": [profile["dataset_manifest_id"]],
        "dependency_profile_id": dependency_profile_id,
        "highest_dependency_unit": "speaker",
        "dependency_keys": list(DEPENDENCY_KEYS_V2),
        "dependency_requirement_by_key": deepcopy(profile["dependency_requirement_by_key"]),
        "dependency_status_by_key": deepcopy(profile["dependency_status_by_key"]),
        "dependency_applicability_reason_by_key": deepcopy(
            profile["dependency_applicability_reason_by_key"]
        ),
        "dependency_covering_key_by_key": deepcopy(profile["dependency_covering_key_by_key"]),
        "dependency_unknown_quarantine": {
            "case_ids": quarantine_ids,
            "reason_codes": quarantine_reasons,
            "claims_allowed": False,
        },
        "training_discovery": {
            "case_ids": training_case_ids,
            "dependency_groups": groups_for(training_case_ids),
        },
        "calibration": {
            "case_ids": [],
            "dependency_groups": deepcopy(empty_groups),
            "prevalence_representative": True,
        },
        "balanced_diagnostic": {
            "case_ids": [],
            "dependency_groups": deepcopy(empty_groups),
            "calibration_claims_allowed": False,
        },
        "final_lockbox": {
            "case_ids": [],
            "dependency_groups": deepcopy(empty_groups),
            "prevalence_representative": True,
            "one_use_only": True,
            "open_count": 0,
        },
        "metric_denominator_case_ids": training_case_ids,
        "claim_denominator_case_ids": training_case_ids,
        "frozen_candidate_family_digest": "A" * 64,
        "confirmatory_claims_allowed": False,
        "runtime_influence_allowed": False,
    }


def _expect_value_error(operation: Any, marker: str) -> None:
    try:
        operation()
    except ValueError as exc:
        if marker not in str(exc):
            raise AssertionError(f"expected {marker!r} in {exc!r}") from exc
        return
    raise AssertionError(f"expected ValueError containing {marker!r}")


def split_manifest_v2_self_check() -> str:
    for profile_id in DEPENDENCY_PROFILES_V2:
        records = fixture_split_records_v2(dependency_profile_id=profile_id)
        manifest = fixture_split_manifest_v2(records, dependency_profile_id=profile_id)
        validate_split_manifest_v2(manifest, records)

    records = fixture_split_records_v2(include_required_unknown=True)
    manifest = fixture_split_manifest_v2(records)
    validate_split_manifest_v2(manifest, records)

    unsupported = deepcopy(manifest)
    unsupported["dependency_profile_id"] = "unsupported-profile"
    _expect_value_error(
        lambda: validate_split_manifest_v2(unsupported, records),
        "unsupported dependency profile",
    )

    mixed_records = deepcopy(records)
    mixed_records[1]["dataset_manifest_id"] = AMI_DATASET_ID
    _expect_value_error(
        lambda: validate_split_manifest_v2(manifest, mixed_records),
        "one dataset manifest ID",
    )

    leaked = deepcopy(manifest)
    leaked["calibration"]["dependency_groups"]["speaker"] = ["speaker-training"]
    _expect_value_error(
        lambda: validate_split_manifest_v2(leaked, records),
        "speaker leakage",
    )

    broken_covering = deepcopy(manifest)
    broken_covering["dependency_covering_key_by_key"]["call_session"] = "missing-key"
    _expect_value_error(
        lambda: validate_split_manifest_v2(broken_covering, records),
        "covering key",
    )

    broken_nesting_records = fixture_split_records_v2()
    broken_nesting_manifest = fixture_split_manifest_v2(broken_nesting_records)
    broken_nesting_records[1]["dependency_value_by_key"]["call_session"] = (
        broken_nesting_records[0]["dependency_value_by_key"]["call_session"]
    )
    broken_nesting_records[1]["dependency_value_by_key"]["speaker"] = "speaker-other"
    _expect_value_error(
        lambda: validate_split_manifest_v2(broken_nesting_manifest, broken_nesting_records),
        "functionally nested",
    )
    return "pass"
