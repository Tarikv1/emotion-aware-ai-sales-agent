from __future__ import annotations

from typing import Any, Mapping

from scripts.emotion_state_phase_c_contracts import (
    PhaseCContractError,
    PhaseCFrameFoldV1,
    PhaseCSignalAccumulatorV1,
    PhaseCSyntheticEvidenceAtomV1,
    PhaseCSyntheticEvidenceFrameV1,
    validate_phase_c_atom,
    validate_phase_c_frame,
    validate_phase_c_frame_fold,
    validate_phase_c_policy,
    validate_phase_c_seen_independence_keys,
    validate_phase_c_signal_accumulator,
)


def _validated_policy(policy: Mapping[str, Any]) -> dict[str, Any]:
    if type(policy) is not dict:
        raise PhaseCContractError("policy object mismatch: policy")
    validate_phase_c_policy(policy)
    return policy


def atom_support_units(
    atom: PhaseCSyntheticEvidenceAtomV1,
    policy: Mapping[str, Any],
) -> int:
    validated_policy = _validated_policy(policy)
    validate_phase_c_atom(atom, validated_policy)
    base = validated_policy["base_support_units"][atom.evidence_class]
    multiplier = validated_policy["quality_multipliers"][atom.quality_bucket]
    return (base * multiplier) // validated_policy["scale"]


def decay_units(units: int, policy: Mapping[str, Any]) -> int:
    validated_policy = _validated_policy(policy)
    if type(units) is not int or units < 0:
        raise PhaseCContractError("invalid_support_units")
    return (
        units * validated_policy["retained_support_milli"]
    ) // validated_policy["scale"]


def _better_quality(
    current: str | None,
    candidate: str,
    quality_order: list[str],
) -> str:
    if current is None:
        return candidate
    if quality_order.index(candidate) < quality_order.index(current):
        return candidate
    return current


def fold_frame_support(
    previous: PhaseCSignalAccumulatorV1 | None,
    frame: PhaseCSyntheticEvidenceFrameV1,
    policy: Mapping[str, Any],
    seen_independence_keys: frozenset[str],
) -> PhaseCFrameFoldV1:
    validated_policy = _validated_policy(policy)
    validate_phase_c_frame(frame, validated_policy)
    validate_phase_c_seen_independence_keys(seen_independence_keys)
    if previous is not None:
        validate_phase_c_signal_accumulator(previous, validated_policy)

    signals = tuple(validated_policy["canonical_signal_order"])
    directions = tuple(validated_policy["canonical_direction_order"])
    modalities = tuple(validated_policy["canonical_modality_order"])
    quality_order = validated_policy["canonical_quality_order"]

    gross: dict[str, dict[str, int]] = {
        signal: {direction: 0 for direction in directions}
        for signal in signals
    }
    quality: dict[str, dict[str, str | None]] = {
        signal: {direction: None for direction in directions}
        for signal in signals
    }
    provenance: dict[str, dict[str, dict[str, list[str]]]] = {
        signal: {
            direction: {modality: [] for modality in modalities}
            for direction in directions
        }
        for signal in signals
    }

    prior_gross = {
        "supports": (
            {}
            if previous is None
            else dict(previous.gross_supporting_units)
        ),
        "opposes": (
            {}
            if previous is None
            else dict(previous.gross_opposing_units)
        ),
    }
    prior_quality = (
        {}
        if previous is None
        else {
            signal: dict(direction_items)
            for signal, direction_items in (
                previous.highest_quality_by_signal_direction
            )
        }
    )
    prior_provenance = (
        {}
        if previous is None
        else {
            signal: {
                direction: {
                    modality: tuple(references)
                    for modality, references in modality_items
                }
                for direction, modality_items in direction_items
            }
            for signal, direction_items in (
                previous.modality_refs_by_signal_direction
            )
        }
    )

    for signal in signals:
        for direction in directions:
            prior_units = (
                0
                if previous is None
                else prior_gross[direction][signal]
            )
            decayed = decay_units(prior_units, validated_policy)
            gross[signal][direction] = decayed
            if decayed == 0:
                quality[signal][direction] = None
                provenance[signal][direction] = {
                    modality: [] for modality in modalities
                }
            else:
                quality[signal][direction] = prior_quality[signal][direction]
                provenance[signal][direction] = {
                    modality: list(
                        prior_provenance[signal][direction][modality],
                    )
                    for modality in modalities
                }

    local_seen = set(seen_independence_keys)
    accepted_refs: list[str] = []
    accepted_new_keys: list[str] = []
    new_contributors_by_signal: dict[
        str,
        list[PhaseCSyntheticEvidenceAtomV1],
    ] = {signal: [] for signal in signals}

    for atom in frame.evidence_atoms:
        signal = atom.operational_signal
        direction = atom.direction
        modality = atom.modality
        accepted_refs.append(atom.evidence_ref)
        is_fresh = atom.independence_key not in local_seen
        local_seen.add(atom.independence_key)
        if is_fresh:
            accepted_new_keys.append(atom.independence_key)
        units = atom_support_units(atom, validated_policy)
        if not is_fresh or units == 0:
            continue
        gross[signal][direction] += units
        provenance[signal][direction][modality].append(atom.evidence_ref)
        quality[signal][direction] = _better_quality(
            quality[signal][direction],
            atom.quality_bucket,
            quality_order,
        )
        new_contributors_by_signal[signal].append(atom)

    for signal in signals:
        eligible = [
            atom
            for atom in new_contributors_by_signal[signal]
            if atom.direction == "supports"
        ]
        if (
            len({atom.evidence_ref for atom in eligible}) >= 2
            and len({atom.independence_key for atom in eligible}) >= 2
            and len({atom.modality for atom in eligible}) >= 2
        ):
            gross[signal]["supports"] += validated_policy["agreement_bonus"]

    for signal in signals:
        for direction in directions:
            gross[signal][direction] = min(
                gross[signal][direction],
                validated_policy["support_saturation"],
            )

    uncapped: dict[str, int] = {}
    capped: dict[str, int] = {}
    contradictory_signals: list[str] = []
    for signal in signals:
        gross_support = gross[signal]["supports"]
        gross_opposition = gross[signal]["opposes"]
        contradictory = (
            gross_support
            >= validated_policy["contradiction_thresholds"]["gross_support"]
            and gross_opposition
            >= validated_policy["contradiction_thresholds"]["gross_opposition"]
        )
        if contradictory:
            contradictory_signals.append(signal)
        net = max(0, gross_support - gross_opposition)
        uncapped[signal] = net
        live_qualities = [
            quality[signal][direction]
            for direction in directions
            if quality[signal][direction] is not None
        ]
        quality_cap = 0
        if live_qualities:
            best_quality = min(
                live_qualities,
                key=quality_order.index,
            )
            quality_cap = validated_policy["total_quality_caps"][best_quality]
        live_modalities = {
            modality
            for direction in directions
            for modality in modalities
            if provenance[signal][direction][modality]
        }
        caps = [net, quality_cap]
        if live_modalities == {"acoustic"}:
            caps.append(validated_policy["acoustic_only_cap"])
        if contradictory:
            caps.append(validated_policy["contradiction_cap"])
        capped[signal] = min(caps)

    accumulator = PhaseCSignalAccumulatorV1(
        gross_supporting_units=tuple(
            (signal, gross[signal]["supports"])
            for signal in signals
        ),
        gross_opposing_units=tuple(
            (signal, gross[signal]["opposes"])
            for signal in signals
        ),
        uncapped_net_support=tuple(
            (signal, uncapped[signal])
            for signal in signals
        ),
        capped_net_support=tuple(
            (signal, capped[signal])
            for signal in signals
        ),
        highest_quality_by_signal_direction=tuple(
            (
                signal,
                tuple(
                    (direction, quality[signal][direction])
                    for direction in directions
                ),
            )
            for signal in signals
        ),
        contradictory_signals=tuple(contradictory_signals),
        modality_refs_by_signal_direction=tuple(
            (
                signal,
                tuple(
                    (
                        direction,
                        tuple(
                            (
                                modality,
                                tuple(
                                    provenance[signal][direction][modality],
                                ),
                            )
                            for modality in modalities
                        ),
                    )
                    for direction in directions
                ),
            )
            for signal in signals
        ),
    )
    validate_phase_c_signal_accumulator(accumulator, validated_policy)

    all_live_refs_list: list[str] = []
    for signal in signals:
        for direction in directions:
            largest_bucket = max(
                len(provenance[signal][direction][modality])
                for modality in modalities
            )
            for ordinal in range(largest_bucket):
                for modality in modalities:
                    references = provenance[signal][direction][modality]
                    if ordinal < len(references):
                        all_live_refs_list.append(references[ordinal])
    all_live_refs = tuple(all_live_refs_list)
    confirming_keys_by_signal = tuple(
        (
            signal,
            tuple(
                atom.independence_key
                for atom in new_contributors_by_signal[signal]
                if atom.direction == "supports"
            )[:1],
        )
        for signal in signals
    )
    live_modalities = {
        modality
        for signal in signals
        for direction in directions
        for modality in modalities
        if provenance[signal][direction][modality]
    }
    fold = PhaseCFrameFoldV1(
        accumulator=accumulator,
        accepted_evidence_refs=tuple(accepted_refs),
        contributing_evidence_refs=all_live_refs,
        accepted_independence_keys=tuple(accepted_new_keys),
        confirming_keys_by_signal=confirming_keys_by_signal,
        acoustic_only=(
            bool(live_modalities)
            and live_modalities == {"acoustic"}
        ),
        missing_input=len(frame.evidence_atoms) == 0,
        low_audio_quality_only=(
            bool(frame.evidence_atoms)
            and all(
                atom.modality == "acoustic"
                and atom.quality_bucket in {"low", "unusable"}
                for atom in frame.evidence_atoms
            )
        ),
    )
    validate_phase_c_frame_fold(fold, frame, validated_policy)
    return fold
