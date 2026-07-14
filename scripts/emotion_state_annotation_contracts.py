from __future__ import annotations

import re
from statistics import median
from typing import Any

ANNOTATION_FIELDS = frozenset({
    "annotation_record_id", "dataset_manifest_id", "turn_id", "dependency_group_ids",
    "reviewer_id", "reviewer_round", "valence", "activation", "engagement",
    "operational_signals", "reviewer_confidence", "not_inferable",
    "not_inferable_reason_code", "evidence_class", "explicit_statement_reference",
})
DEPENDENCY_GROUP_FIELDS = frozenset({
    "speaker", "call_session", "dialogue_dyad", "source_corpus", "scripted_scenario",
})
SPLIT_MANIFEST_FIELDS = frozenset({
    "manifest_id", "dataset_manifest_ids", "highest_dependency_unit", "dependency_keys",
    "training_discovery", "calibration", "balanced_diagnostic", "final_lockbox",
    "frozen_candidate_family_digest", "runtime_influence_allowed",
})
PARTITION_FIELDS = {
    "training_discovery": frozenset({"case_ids", "dependency_groups"}),
    "calibration": frozenset({"case_ids", "dependency_groups", "prevalence_representative"}),
    "balanced_diagnostic": frozenset({"case_ids", "dependency_groups", "calibration_claims_allowed"}),
    "final_lockbox": frozenset({"case_ids", "dependency_groups", "prevalence_representative", "one_use_only", "open_count"}),
}
OPERATIONAL_SIGNALS = frozenset({
    "hesitation", "frustration", "confusion", "interest", "disengagement",
})
NOT_INFERABLE_REASONS = frozenset({
    "unusable_audio", "insufficient_context", "contradictory_evidence", "other_codebook_reason",
})
OPAQUE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,159}$")
EVIDENCE_REFERENCE_PATTERN = re.compile(
    r"^evidence:uuid:[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


class AnnotationContractError(ValueError):
    pass


def _require_opaque_id(value: Any, field: str) -> None:
    if not isinstance(value, str) or OPAQUE_ID_PATTERN.fullmatch(value) is None:
        raise AnnotationContractError(f"{field} must be a bounded opaque identifier, not free text")


def _require_evidence_reference(value: Any, field: str) -> None:
    if not isinstance(value, str) or EVIDENCE_REFERENCE_PATTERN.fullmatch(value) is None:
        raise AnnotationContractError(
            f"{field} must be a typed content-independent evidence UUID, not transcript text"
        )


def validate_annotation_record(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise AnnotationContractError("annotation record must be an object")
    if set(payload) != ANNOTATION_FIELDS:
        raise AnnotationContractError("annotation record fields mismatch")
    for field in ("annotation_record_id", "dataset_manifest_id", "turn_id", "reviewer_id"):
        _require_opaque_id(payload[field], field)
    if type(payload["reviewer_round"]) is not int or payload["reviewer_round"] < 1:
        raise AnnotationContractError("reviewer_round must be a positive integer")
    groups = payload["dependency_group_ids"]
    if not isinstance(groups, dict) or set(groups) != DEPENDENCY_GROUP_FIELDS:
        raise AnnotationContractError("dependency_group_ids fields mismatch")
    if groups["speaker"] is None or groups["source_corpus"] is None:
        raise AnnotationContractError("speaker and source_corpus dependency groups are required")
    for field, value in groups.items():
        if value is not None:
            _require_opaque_id(value, f"dependency_group_ids.{field}")
    signals = payload["operational_signals"]
    if not isinstance(signals, list) or any(not isinstance(signal, str) for signal in signals):
        raise AnnotationContractError("operational_signals must be a string list")
    if len(signals) != len(set(signals)):
        raise AnnotationContractError("operational_signals must be a unique list")
    if any(signal not in OPERATIONAL_SIGNALS for signal in signals):
        raise AnnotationContractError("operational_signals contains an unknown label")
    if payload["reviewer_confidence"] not in {"low", "medium", "high"}:
        raise AnnotationContractError("reviewer_confidence is invalid")
    if type(payload["not_inferable"]) is not bool:
        raise AnnotationContractError("not_inferable must be boolean")

    dimensions = (payload["valence"], payload["activation"], payload["engagement"])
    if payload["not_inferable"]:
        if dimensions != (None, None, None) or signals:
            raise AnnotationContractError("not_inferable excludes dimensional and operational labels")
        if payload["not_inferable_reason_code"] not in NOT_INFERABLE_REASONS:
            raise AnnotationContractError("not_inferable requires an enumerated reason")
        if payload["evidence_class"] != "not_inferable" or payload["explicit_statement_reference"] is not None:
            raise AnnotationContractError("not_inferable evidence fields are inconsistent")
        return payload

    if type(payload["valence"]) is not int or payload["valence"] not in {-2, -1, 0, 1, 2}:
        raise AnnotationContractError("valence must use the frozen five-point ordinal scale")
    for field in ("activation", "engagement"):
        if type(payload[field]) is not int or payload[field] not in {1, 2, 3, 4, 5}:
            raise AnnotationContractError(f"{field} must use the frozen five-point ordinal scale")
    if payload["not_inferable_reason_code"] is not None:
        raise AnnotationContractError("inferable records cannot carry an abstention reason")
    if payload["evidence_class"] not in {"direct_explicit", "observer_inference"}:
        raise AnnotationContractError("inferable evidence_class is invalid")
    reference = payload["explicit_statement_reference"]
    if payload["evidence_class"] == "direct_explicit":
        _require_evidence_reference(reference, "explicit_statement_reference")
    elif reference is not None:
        raise AnnotationContractError("observer inference cannot carry an explicit-statement reference")
    return payload


def _require_unique_opaque_list(value: Any, field: str, *, allow_empty: bool = True) -> list[str]:
    if not isinstance(value, list) or (not allow_empty and not value):
        raise AnnotationContractError(f"{field} must be a list")
    for item in value:
        _require_opaque_id(item, field)
    if len(value) != len(set(value)):
        raise AnnotationContractError(f"{field} must be unique")
    return value


def validate_split_manifest(
    payload: dict[str, Any],
    annotation_records: list[dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != SPLIT_MANIFEST_FIELDS:
        raise AnnotationContractError("split manifest fields mismatch")
    _require_opaque_id(payload["manifest_id"], "manifest_id")
    _require_unique_opaque_list(payload["dataset_manifest_ids"], "dataset_manifest_ids", allow_empty=False)
    if payload["runtime_influence_allowed"] is not False:
        raise AnnotationContractError("split manifests cannot influence runtime")
    if (
        not isinstance(payload["dependency_keys"], list)
        or set(payload["dependency_keys"]) != DEPENDENCY_GROUP_FIELDS
        or len(payload["dependency_keys"]) != len(DEPENDENCY_GROUP_FIELDS)
    ):
        raise AnnotationContractError("dependency_keys must contain the frozen dependency dimensions")
    if payload["highest_dependency_unit"] not in DEPENDENCY_GROUP_FIELDS:
        raise AnnotationContractError("highest_dependency_unit is invalid")
    digest = payload["frozen_candidate_family_digest"]
    if not isinstance(digest, str) or re.fullmatch(r"[0-9A-F]{64}", digest) is None:
        raise AnnotationContractError("frozen_candidate_family_digest must be an uppercase SHA-256")

    if not isinstance(annotation_records, list) or not annotation_records:
        raise AnnotationContractError("split validation requires immutable reviewer records")
    records_by_turn: dict[str, list[dict[str, Any]]] = {}
    for record in annotation_records:
        validated = validate_annotation_record(record)
        records_by_turn.setdefault(validated["turn_id"], []).append(validated)
    case_dependencies: dict[str, dict[str, str | None]] = {}
    case_dataset_manifest_ids: set[str] = set()
    for turn_id, records in records_by_turn.items():
        aggregate_three_reviewer_labels(records)
        case_dependencies[turn_id] = dict(records[0]["dependency_group_ids"])
        case_dataset_manifest_ids.add(records[0]["dataset_manifest_id"])

    if set(payload["dataset_manifest_ids"]) != case_dataset_manifest_ids:
        raise AnnotationContractError("split dataset manifests do not match the supplied reviewer records")

    manifest_case_ids: set[str] = set()
    seen_cases: set[str] = set()
    seen_groups = {key: set() for key in DEPENDENCY_GROUP_FIELDS}
    for partition_name, expected_fields in PARTITION_FIELDS.items():
        partition = payload[partition_name]
        if not isinstance(partition, dict) or set(partition) != expected_fields:
            raise AnnotationContractError(f"{partition_name} fields mismatch")
        case_ids = _require_unique_opaque_list(partition["case_ids"], f"{partition_name}.case_ids")
        if any(case_id not in case_dependencies for case_id in case_ids):
            raise AnnotationContractError(f"{partition_name} references a case without reviewer records")
        overlap = seen_cases & set(case_ids)
        if overlap:
            raise AnnotationContractError(f"case leakage across partitions: {sorted(overlap)}")
        seen_cases.update(case_ids)
        manifest_case_ids.update(case_ids)
        groups = partition["dependency_groups"]
        if not isinstance(groups, dict) or set(groups) != DEPENDENCY_GROUP_FIELDS:
            raise AnnotationContractError(f"{partition_name}.dependency_groups fields mismatch")
        derived_groups = {
            dependency_key: sorted({
                case_dependencies[case_id][dependency_key]
                for case_id in case_ids
                if case_dependencies[case_id][dependency_key] is not None
            })
            for dependency_key in DEPENDENCY_GROUP_FIELDS
        }
        if groups != derived_groups:
            raise AnnotationContractError(
                f"{partition_name}.dependency_groups do not match immutable reviewer records"
            )
        for dependency_key, identifiers in groups.items():
            identifiers = _require_unique_opaque_list(
                identifiers,
                f"{partition_name}.dependency_groups.{dependency_key}",
            )
            dependency_overlap = seen_groups[dependency_key] & set(identifiers)
            if dependency_overlap:
                raise AnnotationContractError(
                    f"{dependency_key} leakage across partitions: {sorted(dependency_overlap)}"
                )
            seen_groups[dependency_key].update(identifiers)
        if case_ids and not groups[payload["highest_dependency_unit"]]:
            raise AnnotationContractError(f"{partition_name} lacks its highest dependency groups")

    if manifest_case_ids != set(case_dependencies):
        raise AnnotationContractError("split cases must exactly match the supplied reviewer records")

    if payload["calibration"]["prevalence_representative"] is not True:
        raise AnnotationContractError("calibration must preserve prevalence")
    if payload["balanced_diagnostic"]["calibration_claims_allowed"] is not False:
        raise AnnotationContractError("balanced diagnostic data cannot support calibration claims")
    lockbox = payload["final_lockbox"]
    if lockbox["prevalence_representative"] is not True or lockbox["one_use_only"] is not True:
        raise AnnotationContractError("final lockbox controls are invalid")
    if type(lockbox["open_count"]) is not int or lockbox["open_count"] not in {0, 1}:
        raise AnnotationContractError("final lockbox may be opened at most once")
    return payload


def _empty_consensus(turn_id: str, status: str, not_inferable_count: int) -> dict[str, Any]:
    return {
        "turn_id": turn_id,
        "label_status": status,
        "valence": None,
        "activation": None,
        "engagement": None,
        "operational_signals": [],
        "none_selected": False,
        "reviewer_count": 3,
        "not_inferable_count": not_inferable_count,
    }


def aggregate_three_reviewer_labels(records: list[dict[str, Any]]) -> dict[str, Any]:
    if len(records) != 3:
        raise AnnotationContractError("exactly three reviewer records are required")
    validated = [validate_annotation_record(record) for record in records]
    for field in ("dataset_manifest_id", "turn_id", "reviewer_round"):
        if len({record[field] for record in validated}) != 1:
            raise AnnotationContractError(f"review records disagree on {field}")
    if any(record["dependency_group_ids"] != validated[0]["dependency_group_ids"] for record in validated[1:]):
        raise AnnotationContractError("review records disagree on dependency_group_ids")
    if len({record["reviewer_id"] for record in validated}) != 3:
        raise AnnotationContractError("reviewers must be distinct")
    if len({record["annotation_record_id"] for record in validated}) != 3:
        raise AnnotationContractError("annotation records must be distinct")

    turn_id = validated[0]["turn_id"]
    not_inferable = [record for record in validated if record["not_inferable"]]
    inferable = [record for record in validated if not record["not_inferable"]]
    if len(not_inferable) >= 2:
        return _empty_consensus(turn_id, "not_inferable", len(not_inferable))
    if len(not_inferable) == 1:
        first, second = inferable
        first_labels = (
            first["valence"], first["activation"], first["engagement"],
            frozenset(first["operational_signals"]),
        )
        second_labels = (
            second["valence"], second["activation"], second["engagement"],
            frozenset(second["operational_signals"]),
        )
        if first_labels != second_labels:
            return _empty_consensus(turn_id, "ambiguous", 1)

    consensus_signals = sorted(
        signal
        for signal in OPERATIONAL_SIGNALS
        if sum(signal in record["operational_signals"] for record in inferable) >= 2
    )
    return {
        "turn_id": turn_id,
        "label_status": "consensus",
        "valence": int(median(record["valence"] for record in inferable)),
        "activation": int(median(record["activation"] for record in inferable)),
        "engagement": int(median(record["engagement"] for record in inferable)),
        "operational_signals": consensus_signals,
        "none_selected": not consensus_signals,
        "reviewer_count": 3,
        "not_inferable_count": len(not_inferable),
    }


def _expect_annotation_error(callback: Any) -> None:
    try:
        callback()
    except AnnotationContractError:
        return
    raise AssertionError("expected AnnotationContractError")


def _fixture_record(record_id: str, reviewer_id: str) -> dict[str, Any]:
    return {
        "annotation_record_id": record_id,
        "dataset_manifest_id": "synthetic-fixture-manifest-v1",
        "turn_id": "turn-fixture-1",
        "dependency_group_ids": {
            "speaker": "speaker-fixture-1",
            "call_session": "call-fixture-1",
            "dialogue_dyad": None,
            "source_corpus": "synthetic-fixture-corpus",
            "scripted_scenario": "scenario-fixture-1",
        },
        "reviewer_id": reviewer_id,
        "reviewer_round": 1,
        "valence": 0,
        "activation": 3,
        "engagement": 2,
        "operational_signals": ["confusion"],
        "reviewer_confidence": "medium",
        "not_inferable": False,
        "not_inferable_reason_code": None,
        "evidence_class": "observer_inference",
        "explicit_statement_reference": None,
    }


def _not_inferable(record: dict[str, Any]) -> dict[str, Any]:
    return dict(
        record,
        valence=None,
        activation=None,
        engagement=None,
        operational_signals=[],
        not_inferable=True,
        not_inferable_reason_code="insufficient_context",
        evidence_class="not_inferable",
        explicit_statement_reference=None,
    )


def annotation_contract_self_check() -> str:
    first = _fixture_record("annotation-1", "reviewer-1")
    second = _fixture_record("annotation-2", "reviewer-2")
    third = dict(
        _fixture_record("annotation-3", "reviewer-3"),
        valence=1,
        activation=4,
        engagement=3,
        operational_signals=["confusion", "interest"],
    )
    consensus = aggregate_three_reviewer_labels([first, second, third])
    assert consensus["label_status"] == "consensus"
    assert consensus["valence"] == 0
    assert consensus["operational_signals"] == ["confusion"]

    two_abstain = aggregate_three_reviewer_labels([first, _not_inferable(second), _not_inferable(third)])
    assert two_abstain["label_status"] == "not_inferable"

    one_abstains_agree = aggregate_three_reviewer_labels([first, second, _not_inferable(third)])
    assert one_abstains_agree["label_status"] == "consensus"
    assert type(one_abstains_agree["valence"]) is int
    one_abstains_disagree = aggregate_three_reviewer_labels([
        first,
        dict(second, valence=-1),
        _not_inferable(third),
    ])
    assert one_abstains_disagree["label_status"] == "ambiguous"

    _expect_annotation_error(lambda: validate_annotation_record(dict(_not_inferable(first), valence=0)))
    _expect_annotation_error(lambda: validate_annotation_record(dict(
        first,
        evidence_class="direct_explicit",
        explicit_statement_reference="raw transcript sentence",
    )))
    for transcript_like_reference in (
        "I-am-confused-about-price",
        "I_am_confused_about_price",
        "I%20am%20confused",
        "Ich-bin-verwirrt-wegen-des-Preises",
    ):
        _expect_annotation_error(lambda reference=transcript_like_reference: validate_annotation_record(dict(
            first,
            evidence_class="direct_explicit",
            explicit_statement_reference=reference,
        )))
    validate_annotation_record(dict(
        first,
        evidence_class="direct_explicit",
        explicit_statement_reference="evidence:uuid:11111111-1111-4111-8111-111111111111",
    ))
    _expect_annotation_error(lambda: aggregate_three_reviewer_labels([
        first,
        dict(second, reviewer_id="reviewer-1"),
        third,
    ]))
    _expect_annotation_error(lambda: aggregate_three_reviewer_labels([
        first,
        dict(second, dependency_group_ids=dict(second["dependency_group_ids"], speaker="speaker-fixture-2")),
        third,
    ]))

    def dependency_groups(suffix: str) -> dict[str, list[str]]:
        return {key: [f"{key}-{suffix}"] for key in DEPENDENCY_GROUP_FIELDS}

    def records_for_case(case_id: str, suffix: str) -> list[dict[str, Any]]:
        groups = {key: f"{key}-{suffix}" for key in DEPENDENCY_GROUP_FIELDS}
        return [
            dict(
                _fixture_record(f"annotation-{suffix}-{index}", f"reviewer-{index}"),
                turn_id=case_id,
                dependency_group_ids=groups,
            )
            for index in range(1, 4)
        ]

    split_records = [
        record
        for case_id, suffix in (
            ("case-training-1", "training"),
            ("case-calibration-1", "calibration"),
            ("case-diagnostic-1", "diagnostic"),
            ("case-lockbox-1", "lockbox"),
        )
        for record in records_for_case(case_id, suffix)
    ]

    split = {
        "manifest_id": "split-fixture-v1",
        "dataset_manifest_ids": ["synthetic-fixture-manifest-v1"],
        "highest_dependency_unit": "speaker",
        "dependency_keys": sorted(DEPENDENCY_GROUP_FIELDS),
        "training_discovery": {
            "case_ids": ["case-training-1"],
            "dependency_groups": dependency_groups("training"),
        },
        "calibration": {
            "case_ids": ["case-calibration-1"],
            "dependency_groups": dependency_groups("calibration"),
            "prevalence_representative": True,
        },
        "balanced_diagnostic": {
            "case_ids": ["case-diagnostic-1"],
            "dependency_groups": dependency_groups("diagnostic"),
            "calibration_claims_allowed": False,
        },
        "final_lockbox": {
            "case_ids": ["case-lockbox-1"],
            "dependency_groups": dependency_groups("lockbox"),
            "prevalence_representative": True,
            "one_use_only": True,
            "open_count": 0,
        },
        "frozen_candidate_family_digest": "A" * 64,
        "runtime_influence_allowed": False,
    }
    validate_split_manifest(split, split_records)
    leaky_groups = dict(split["calibration"]["dependency_groups"], speaker=["speaker-training"])
    _expect_annotation_error(lambda: validate_split_manifest(dict(
        split,
        calibration=dict(split["calibration"], dependency_groups=leaky_groups),
    ), split_records))
    fabricated_distinct_speaker_records = [
        dict(
            record,
            dependency_group_ids=dict(record["dependency_group_ids"], speaker="speaker-training"),
        )
        if record["turn_id"] == "case-calibration-1"
        else record
        for record in split_records
    ]
    _expect_annotation_error(lambda: validate_split_manifest(
        split,
        fabricated_distinct_speaker_records,
    ))
    _expect_annotation_error(lambda: validate_split_manifest(dict(
        split,
        calibration=dict(split["calibration"], case_ids=["case-training-1"]),
    ), split_records))
    _expect_annotation_error(lambda: validate_split_manifest(dict(
        split,
        final_lockbox=dict(split["final_lockbox"], open_count=2),
    ), split_records))
    _expect_annotation_error(lambda: validate_split_manifest(split, split_records[:-1]))
    return "pass"
