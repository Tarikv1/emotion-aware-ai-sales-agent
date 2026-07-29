from __future__ import annotations

from dataclasses import fields, is_dataclass, replace
from typing import Any, Mapping

from runtime.contracts.emotion_state_contracts import (
    validate_perceived_customer_state,
)
from scripts.emotion_state_phase_c_contracts import (
    EMITTED_ABSTENTION_COUNT_ORDER,
    EVIDENCE_REF_PATTERN,
    EXPECTED_COUNTS_BY_ABSTENTION_REASON,
    EXPECTED_COUNTS_BY_FAMILY,
    EXPECTED_COUNTS_BY_MODALITY_FAMILY,
    EXPECTED_COUNTS_BY_SIGNAL_FAMILY,
    EXPECTED_SCENARIO_CLASSIFICATIONS,
    EXPECTED_SCENARIO_IDS,
    FAMILY_COUNT_ORDER,
    FORBIDDEN_PHASE_C_KEY_FRAGMENTS,
    INVARIANT_NAMES,
    MODALITY_FAMILY_COUNT_ORDER,
    PhaseCContractError,
    PhaseCEventRejected,
    PhaseCEventWatermarkV1,
    PhaseCExpectedInternalProjectionV1,
    PhaseCFrameFoldV1,
    PhaseCHysteresisV1,
    PhaseCOutputSemanticError,
    PhaseCProjectionContextV1,
    PhaseCReplayV1,
    PhaseCScenarioEvaluationV1,
    PhaseCScenarioOutcomeV1,
    PhaseCScenarioV1,
    PhaseCSignalAccumulatorV1,
    PhaseCSyntheticEvidenceAtomV1,
    PhaseCSyntheticEvidenceFrameV1,
    PhaseCTemporalSessionStateV1,
    SAFETY_INVARIANT_NAMES,
    SIGNAL_FAMILY_COUNT_ORDER,
    UNEXPECTED_ACCEPTANCE_SAFETY_INVARIANT_BY_CASE,
    _derive_phase_c_retired_independence_keys,
    canonical_json_bytes,
    initial_phase_c_watermark,
    materialize_phase_c_scenario_attempt_payload,
    parse_phase_c_frame,
    phase_c_frame_to_payload,
    sha256_bytes,
    validate_phase_c_event_identity,
    validate_phase_c_atom,
    validate_phase_c_frame,
    validate_phase_c_frame_fold,
    validate_phase_c_hysteresis,
    validate_phase_c_policy,
    validate_phase_c_perceived_state,
    validate_phase_c_seen_independence_keys,
    validate_phase_c_session_state,
    validate_phase_c_signal_accumulator,
    validate_phase_c_temporal_state,
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


def _empty_hysteresis(policy: Mapping[str, Any]) -> PhaseCHysteresisV1:
    return PhaseCHysteresisV1(
        internal_incumbent=None,
        incumbent_tenure=0,
        entry_confirmation_keys_by_signal=tuple(
            (signal, ()) for signal in policy["canonical_signal_order"]
        ),
        switch_challenger=None,
        switch_confirmation_keys=(),
        release_streak=0,
    )


def _append_or_clear(streak: tuple[str, ...], key: str | None) -> tuple[str, ...]:
    if key is None:
        return ()
    return (*streak, key) if key not in streak else (key,)


def _validate_projection_context(
    context: PhaseCProjectionContextV1,
    policy: Mapping[str, Any],
) -> None:
    if type(context) is not PhaseCProjectionContextV1:
        raise PhaseCContractError("projection_context_type")
    signal = context.prior_emitted_selected_signal
    support = context.prior_emitted_selected_support
    if (signal is None) != (support is None):
        raise PhaseCContractError("projection_context_prior")
    if signal is not None and (
        type(signal) is not str
        or signal not in policy["canonical_signal_order"]
        or type(support) is not int
        or support < 0
        or support > policy["scale"]
    ):
        raise PhaseCContractError("projection_context_prior")
    validate_phase_c_frame_fold(context.fold, context.frame, policy)


def update_hysteresis(
    previous_state: PhaseCTemporalSessionStateV1 | None,
    fold: PhaseCFrameFoldV1,
    frame: PhaseCSyntheticEvidenceFrameV1,
    policy: Mapping[str, Any],
) -> PhaseCHysteresisV1:
    validated_policy = _validated_policy(policy)
    validate_phase_c_frame(frame, validated_policy)
    validate_phase_c_frame_fold(fold, frame, validated_policy)
    if previous_state is not None:
        validate_phase_c_temporal_state(previous_state, validated_policy)
    signals = tuple(validated_policy["canonical_signal_order"])
    signal_index = {signal: index for index, signal in enumerate(signals)}
    nets = dict(fold.accumulator.capped_net_support)
    keys = dict(fold.confirming_keys_by_signal)
    previous = _empty_hysteresis(validated_policy) if previous_state is None else previous_state.hysteresis
    entry = {signal: tuple(keys_) for signal, keys_ in previous.entry_confirmation_keys_by_signal}
    switch_challenger = previous.switch_challenger
    switch_keys = previous.switch_confirmation_keys
    release_streak = previous.release_streak
    incumbent = previous.internal_incumbent
    ranked = sorted(signals, key=lambda signal: (-nets[signal], signal_index[signal]))
    top = ranked[0]
    top_tied = len(signals) > 1 and nets[ranked[1]] == nets[top]

    def new_key(signal: str) -> str | None:
        return keys[signal][0] if keys[signal] else None

    if incumbent is None:
        switch_challenger = None
        switch_keys = ()
        release_streak = 0
        if top_tied or nets[top] < validated_policy["entry_threshold"]:
            entry = {signal: () for signal in signals}
            next_incumbent = None
        else:
            entry = {signal: entry[signal] if signal == top else () for signal in signals}
            entry[top] = _append_or_clear(entry[top], new_key(top))
            explicit_now = any(
                atom.operational_signal == top
                and atom.direction == "supports"
                and atom.independence_key in keys[top]
                and atom.evidence_class == validated_policy["explicit_entry_evidence_class"]
                and (
                    validated_policy["base_support_units"][atom.evidence_class]
                    * validated_policy["quality_multipliers"][atom.quality_bucket]
                ) // validated_policy["scale"] > 0
                for atom in frame.evidence_atoms
            )
            required = (
                validated_policy["confirmation_counts"]["explicit_statement_entry"]
                if explicit_now
                else validated_policy["confirmation_counts"]["entry"]
            )
            if len(entry[top]) >= required:
                next_incumbent = top
                entry = {signal: () for signal in signals}
            else:
                next_incumbent = None
    elif nets[incumbent] < validated_policy["release_threshold"]:
        entry = {signal: () for signal in signals}
        switch_challenger = None
        switch_keys = ()
        release_streak += 1
        if release_streak >= validated_policy["confirmation_counts"]["release"]:
            next_incumbent = None
            release_streak = 0
        else:
            next_incumbent = incumbent
    else:
        entry = {signal: () for signal in signals}
        release_streak = 0
        challengers = sorted(
            (signal for signal in signals if signal != incumbent),
            key=lambda signal: (-nets[signal], signal_index[signal]),
        )
        challenger = challengers[0]
        tied = len(challengers) > 1 and nets[challengers[1]] == nets[challenger]
        qualified = (
            not tied
            and nets[challenger] >= validated_policy["switch_threshold"]
            and nets[challenger] - nets[incumbent] >= validated_policy["minimum_switch_advantage"]
        )
        if not qualified:
            switch_challenger = None
            switch_keys = ()
            next_incumbent = incumbent
        else:
            if switch_challenger != challenger:
                switch_keys = ()
            key = new_key(challenger)
            switch_keys = _append_or_clear(switch_keys, key)
            if key is None:
                next_incumbent = incumbent
                switch_challenger = None
            elif len(switch_keys) >= validated_policy["confirmation_counts"]["switch"]:
                next_incumbent = challenger
                switch_challenger = None
                switch_keys = ()
            else:
                next_incumbent = incumbent
                switch_challenger = challenger

    tenure = (
        0 if next_incumbent is None else
        1 if next_incumbent != incumbent else
        previous.incumbent_tenure + 1
    )
    result = PhaseCHysteresisV1(
        internal_incumbent=next_incumbent,
        incumbent_tenure=tenure,
        entry_confirmation_keys_by_signal=tuple((signal, entry[signal]) for signal in signals),
        switch_challenger=switch_challenger if next_incumbent is not None else None,
        switch_confirmation_keys=switch_keys if next_incumbent is not None else (),
        release_streak=release_streak if next_incumbent is not None else 0,
    )
    validate_phase_c_hysteresis(result, validated_policy)
    return result


def project_perceived_customer_state(
    session_state: PhaseCTemporalSessionStateV1,
    context: PhaseCProjectionContextV1,
    policy: Mapping[str, Any],
) -> dict[str, Any]:
    validated_policy = _validated_policy(policy)
    validate_phase_c_temporal_state(session_state, validated_policy)
    _validate_projection_context(context, validated_policy)
    signals = tuple(validated_policy["canonical_signal_order"])
    modalities = tuple(validated_policy["canonical_modality_order"])
    nets = dict(context.fold.accumulator.capped_net_support)
    visible = [
        signal
        for signal in signals
        if nets[signal] >= validated_policy["visibility_threshold"]
    ]

    reasons: list[str] = []
    if context.fold.accumulator.contradictory_signals:
        reasons.append("contradictory_evidence")
    if context.fold.low_audio_quality_only:
        reasons.append("low_audio_quality")
    if context.fold.missing_input:
        reasons.append("missing_input")
    candidate = session_state.hysteresis.internal_incumbent
    if candidate is None or candidate not in visible:
        reasons.append("insufficient_evidence")
    reason_order = tuple(validated_policy["abstention_reason_order"])
    reasons = sorted(set(reasons), key=reason_order.index)

    selected = "none" if reasons else candidate
    if selected == "none":
        emitted = [f"possible_{signal}" for signal in visible] or ["none"]
    else:
        emitted = [
            selected,
            *(
                f"possible_{signal}"
                for signal in visible
                if signal != selected
            ),
        ]

    provenance_source = {
        signal: {
            direction: dict(rows)
            for direction, rows in directions
        }
        for signal, directions in (
            context.fold.accumulator.modality_refs_by_signal_direction
        )
    }
    quality_source = {
        signal: dict(rows)
        for signal, rows in (
            context.fold.accumulator.highest_quality_by_signal_direction
        )
    }
    confidence: dict[str, float] = {}
    provenance: dict[str, dict[str, list[str]]] = {}
    refs: list[str] = []
    qualities: list[str] = []
    live_modalities: set[str] = set()

    for emitted_signal in emitted:
        if emitted_signal == "none":
            continue
        signal = emitted_signal.removeprefix("possible_")
        confidence[emitted_signal] = (
            nets[signal] / validated_policy["scale"]
        )
        modality_map: dict[str, list[str]] = {}
        ordered_lists: list[list[str]] = []
        for modality in modalities:
            items = [
                reference
                for direction in validated_policy["canonical_direction_order"]
                for reference in provenance_source[signal][direction][modality]
            ]
            if items:
                modality_map[modality] = items
                ordered_lists.append(items)
                live_modalities.add(modality)
        largest_bucket = max(
            (len(items) for items in ordered_lists),
            default=0,
        )
        for ordinal in range(largest_bucket):
            for items in ordered_lists:
                if ordinal < len(items) and items[ordinal] not in refs:
                    refs.append(items[ordinal])
        provenance[emitted_signal] = modality_map
        for direction in validated_policy["canonical_direction_order"]:
            has_references = any(
                provenance_source[signal][direction][modality]
                for modality in modalities
            )
            if (
                has_references
                and quality_source[signal][direction] is not None
            ):
                qualities.append(quality_source[signal][direction])

    if selected == "none":
        bucket = "low"
    elif (
        nets[selected]
        >= validated_policy["confidence_bucket_thresholds"]["high"]
    ):
        bucket = "high"
    elif (
        nets[selected]
        >= validated_policy["confidence_bucket_thresholds"]["medium"]
    ):
        bucket = "medium"
    else:
        bucket = "low"

    if not refs:
        quality = (
            "low_quality"
            if context.fold.low_audio_quality_only
            else "insufficient"
        )
    elif qualities and all(
        value in {"low", "unusable"}
        for value in qualities
    ):
        quality = "low_quality"
    elif live_modalities == {"text"}:
        quality = "text_only"
    elif live_modalities == {"acoustic"}:
        quality = "acoustic_only"
    elif live_modalities == {"dialogue"}:
        quality = "low_quality"
    else:
        quality = "multimodal"

    if context.fold.accumulator.contradictory_signals:
        trajectory = "contradictory"
    elif (
        selected == "none"
        or context.prior_emitted_selected_signal is None
        or selected != context.prior_emitted_selected_signal
    ):
        trajectory = "insufficient_history"
    else:
        delta = nets[selected] - context.prior_emitted_selected_support
        if abs(delta) < validated_policy["trajectory_delta_threshold"]:
            trajectory = "stable"
        elif selected == "interest":
            trajectory = "improving" if delta > 0 else "worsening"
        else:
            trajectory = "worsening" if delta > 0 else "improving"

    allowed_effects = (
        ["preserve"]
        if selected == "none" or quality == "acoustic_only"
        else list(validated_policy["allowed_effects_by_signal"][selected])
    )
    payload = {
        "call_session_id": context.frame.call_session_id,
        "campaign_profile_id": context.frame.campaign_profile_id,
        "campaign_profile_version": context.frame.campaign_profile_version,
        "turn_id": context.frame.turn_id,
        "turn_sequence": context.frame.turn_sequence,
        "valence_estimate": "not_inferable",
        "activation_estimate": "not_inferable",
        "engagement_estimate": "not_inferable",
        "operational_signals": emitted,
        "confidence_by_signal": confidence,
        "selected_policy_signal": selected,
        "selected_signal_confidence_bucket": bucket,
        "overall_evidence_quality": quality,
        "trajectory": trajectory,
        "evidence_refs": refs,
        "signal_provenance_by_modality": provenance,
        "allowed_policy_effects": allowed_effects,
        "blocked_policy_effects": list(
            validated_policy["blocked_effect_order"],
        ),
        "abstained": bool(reasons),
        "abstention_reasons": reasons,
        "evidence_policy_version": validated_policy[
            "evidence_policy_version"
        ],
        "runtime_approved": False,
    }
    validate_perceived_customer_state(payload)
    return payload


def _canonical_phase_c_value(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _canonical_phase_c_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple:
        return [_canonical_phase_c_value(item) for item in value]
    if type(value) is frozenset:
        return sorted(
            (_canonical_phase_c_value(item) for item in value),
            key=lambda item: canonical_json_bytes(item),
        )
    if type(value) is dict:
        return {
            key: _canonical_phase_c_value(item)
            for key, item in value.items()
        }
    if type(value) is list:
        return [_canonical_phase_c_value(item) for item in value]
    return value


def canonical_session_state_bytes(
    state: PhaseCTemporalSessionStateV1 | None,
) -> bytes:
    if state is not None and type(state) is not PhaseCTemporalSessionStateV1:
        raise PhaseCContractError("session_state_type")
    return canonical_json_bytes(_canonical_phase_c_value(state))


def canonical_semantic_replay_bytes(
    state: PhaseCTemporalSessionStateV1,
    output: dict[str, Any],
) -> bytes:
    if type(state) is not PhaseCTemporalSessionStateV1:
        raise PhaseCContractError("session_state_type")
    if type(output) is not dict:
        raise PhaseCContractError("replayed_output_type")
    frames: list[dict[str, Any]] = []
    for frame in state.accepted_frames:
        payload = phase_c_frame_to_payload(frame)
        del payload["event_id"]
        del payload["input_revision"]
        frames.append(payload)
    return canonical_json_bytes({
        "accepted_frames": frames,
        "accumulator": _canonical_phase_c_value(state.accumulator),
        "hysteresis": _canonical_phase_c_value(state.hysteresis),
        "contributing_evidence_refs": list(
            state.contributing_evidence_refs,
        ),
        "accepted_turn_count": state.accepted_turn_count,
        "last_emitted_selected_signal": (
            state.last_emitted_selected_signal
        ),
        "last_emitted_selected_support": (
            state.last_emitted_selected_support
        ),
        "output": output,
    })


def accepted_frames_for(
    previous_state: PhaseCTemporalSessionStateV1 | None,
) -> tuple[PhaseCSyntheticEvidenceFrameV1, ...]:
    return () if previous_state is None else previous_state.accepted_frames


def retired_independence_keys(
    previous_state: PhaseCTemporalSessionStateV1 | None,
) -> frozenset[str]:
    return (
        frozenset()
        if previous_state is None
        else frozenset(previous_state.retired_independence_keys)
    )


def watermark_for(
    previous_state: PhaseCTemporalSessionStateV1 | None,
    frame: PhaseCSyntheticEvidenceFrameV1,
) -> PhaseCEventWatermarkV1:
    if previous_state is None:
        return initial_phase_c_watermark(frame)
    return previous_state.watermark


def replaced_frame_for(
    previous_state: PhaseCTemporalSessionStateV1 | None,
    frame: PhaseCSyntheticEvidenceFrameV1,
) -> PhaseCSyntheticEvidenceFrameV1 | None:
    if previous_state is None:
        return None
    revisions = dict(previous_state.watermark.last_input_revision_by_turn)
    if frame.turn_id not in revisions:
        return None
    replaced = previous_state.accepted_frames[-1]
    if (
        replaced.turn_id != frame.turn_id
        or replaced.turn_sequence != frame.turn_sequence
    ):
        raise PhaseCEventRejected("stale_turn")
    return replaced


def candidate_frame_sequence(
    previous_state: PhaseCTemporalSessionStateV1 | None,
    frame: PhaseCSyntheticEvidenceFrameV1,
) -> tuple[PhaseCSyntheticEvidenceFrameV1, ...]:
    if previous_state is None:
        return (frame,)
    if frame.turn_id in dict(
        previous_state.watermark.last_input_revision_by_turn,
    ):
        return (*previous_state.accepted_frames[:-1], frame)
    return (*previous_state.accepted_frames, frame)


def frame_independence_keys(
    frames: tuple[PhaseCSyntheticEvidenceFrameV1, ...],
) -> frozenset[str]:
    return frozenset(
        atom.independence_key
        for frame in frames
        for atom in frame.evidence_atoms
    )


def frame_evidence_references(
    frames: tuple[PhaseCSyntheticEvidenceFrameV1, ...],
) -> frozenset[str]:
    return frozenset(
        atom.evidence_ref
        for frame in frames
        for atom in frame.evidence_atoms
    )


def validate_candidate_reference_uniqueness(
    previous_state: PhaseCTemporalSessionStateV1 | None,
    candidate_frames: tuple[PhaseCSyntheticEvidenceFrameV1, ...],
    replaced_frame: PhaseCSyntheticEvidenceFrameV1 | None,
) -> None:
    current_references = tuple(
        atom.evidence_ref
        for frame in candidate_frames
        for atom in frame.evidence_atoms
    )
    if len(set(current_references)) != len(current_references):
        raise PhaseCEventRejected("duplicate_evidence_reference")
    if previous_state is None:
        return
    incoming_references = {
        atom.evidence_ref
        for atom in candidate_frames[-1].evidence_atoms
    }
    historical_references = set(previous_state.seen_evidence_refs)
    retained_references = (
        set()
        if replaced_frame is None
        else {
            atom.evidence_ref
            for atom in replaced_frame.evidence_atoms
        }
    )
    if any(
        reference in historical_references
        and reference not in retained_references
        for reference in incoming_references
    ):
        raise PhaseCEventRejected("duplicate_evidence_reference")


def append_evidence_history_event(
    previous_state: PhaseCTemporalSessionStateV1 | None,
    frame: PhaseCSyntheticEvidenceFrameV1,
    watermark: PhaseCEventWatermarkV1,
) -> tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...]:
    history = (
        ()
        if previous_state is None
        else previous_state.evidence_history_by_event
    )
    next_history = tuple(sorted(
        (
            *history,
            (
                frame.event_id,
                tuple(
                    sorted(
                        atom.evidence_ref
                        for atom in frame.evidence_atoms
                    )
                ),
                tuple(
                    sorted(
                        atom.independence_key
                        for atom in frame.evidence_atoms
                    )
                ),
            ),
        ),
        key=lambda row: row[0],
    ))
    if (
        tuple(row[0] for row in next_history)
        != tuple(sorted(watermark.seen_event_ids))
    ):
        raise PhaseCContractError("session_state_history")
    return next_history


def _ordinal_history_union(
    rows: tuple[tuple[str, ...], ...],
) -> tuple[str, ...]:
    seen: set[str] = set()
    values: list[str] = []
    for row in rows:
        for value in row:
            if value not in seen:
                seen.add(value)
                values.append(value)
    return tuple(values)


def evidence_refs_from_history(
    history: tuple[
        tuple[str, tuple[str, ...], tuple[str, ...]],
        ...
    ],
) -> tuple[str, ...]:
    return _ordinal_history_union(
        tuple(references for _event_id, references, _keys in history),
    )


def independence_keys_from_history(
    history: tuple[
        tuple[str, tuple[str, ...], tuple[str, ...]],
        ...
    ],
) -> tuple[str, ...]:
    return _ordinal_history_union(
        tuple(keys for _event_id, _references, keys in history),
    )


def replay_frame_semantics(
    candidate_frames: tuple[PhaseCSyntheticEvidenceFrameV1, ...],
    policy: Mapping[str, Any],
    *,
    retired_independence_keys: frozenset[str],
    evidence_history_by_event: tuple[
        tuple[str, tuple[str, ...], tuple[str, ...]],
        ...
    ],
    historical_seen_evidence_refs: tuple[str, ...],
    historical_seen_independence_keys: tuple[str, ...],
    watermark: PhaseCEventWatermarkV1,
) -> tuple[
    PhaseCTemporalSessionStateV1,
    dict[str, Any],
    PhaseCProjectionContextV1,
]:
    validated_policy = _validated_policy(policy)
    if type(candidate_frames) is not tuple or not candidate_frames:
        raise PhaseCContractError("replay_frames")
    if type(retired_independence_keys) is not frozenset:
        raise PhaseCContractError("seen_independence_keys_type")
    validate_phase_c_seen_independence_keys(retired_independence_keys)
    for frame in candidate_frames:
        validate_phase_c_frame(frame, validated_policy)

    previous: PhaseCTemporalSessionStateV1 | None = None
    current_seen_keys = set(retired_independence_keys)
    current_seen_references: list[str] = []
    current_history: list[
        tuple[str, tuple[str, ...], tuple[str, ...]]
    ] = []
    output: dict[str, Any] | None = None
    context: PhaseCProjectionContextV1 | None = None
    for frame in candidate_frames:
        fold = fold_frame_support(
            None if previous is None else previous.accumulator,
            frame,
            validated_policy,
            frozenset(current_seen_keys),
        )
        hysteresis = update_hysteresis(
            previous,
            fold,
            frame,
            validated_policy,
        )
        accepted_frames = (
            (frame,)
            if previous is None
            else (*previous.accepted_frames, frame)
        )
        current_history.append((
            frame.event_id,
            tuple(
                sorted(atom.evidence_ref for atom in frame.evidence_atoms)
            ),
            tuple(
                sorted(
                    atom.independence_key
                    for atom in frame.evidence_atoms
                )
            ),
        ))
        for atom in frame.evidence_atoms:
            if atom.evidence_ref not in current_seen_references:
                current_seen_references.append(atom.evidence_ref)
            current_seen_keys.add(atom.independence_key)
        provisional = PhaseCTemporalSessionStateV1(
            schema_version="PhaseCTemporalSessionStateV1",
            policy_id=validated_policy["policy_id"],
            policy_sha256=sha256_bytes(
                canonical_json_bytes(dict(validated_policy)),
            ),
            call_session_id=frame.call_session_id,
            campaign_profile_id=frame.campaign_profile_id,
            campaign_profile_version=frame.campaign_profile_version,
            watermark=watermark,
            accepted_frames=accepted_frames,
            evidence_history_by_event=tuple(current_history),
            accumulator=fold.accumulator,
            hysteresis=hysteresis,
            seen_evidence_refs=tuple(current_seen_references),
            seen_independence_keys=tuple(sorted(current_seen_keys)),
            retired_independence_keys=tuple(
                sorted(retired_independence_keys)
            ),
            contributing_evidence_refs=fold.contributing_evidence_refs,
            accepted_turn_count=len(accepted_frames),
            last_emitted_selected_signal=(
                None
                if previous is None
                else previous.last_emitted_selected_signal
            ),
            last_emitted_selected_support=(
                None
                if previous is None
                else previous.last_emitted_selected_support
            ),
        )
        validate_phase_c_temporal_state(
            provisional,
            validated_policy,
        )
        context = PhaseCProjectionContextV1(
            provisional.last_emitted_selected_signal,
            provisional.last_emitted_selected_support,
            fold,
            frame,
        )
        output = project_perceived_customer_state(
            provisional,
            context,
            validated_policy,
        )
        selected = output["selected_policy_signal"]
        previous = PhaseCTemporalSessionStateV1(
            **{
                **provisional.__dict__,
                "last_emitted_selected_signal": (
                    None if selected == "none" else selected
                ),
                "last_emitted_selected_support": (
                    None
                    if selected == "none"
                    else dict(fold.accumulator.capped_net_support)[selected]
                ),
            },
        )
        validate_phase_c_perceived_state(
            output,
            previous,
            context,
            validated_policy,
        )
        validate_phase_c_temporal_state(previous, validated_policy)

    if previous is None or output is None or context is None:
        raise PhaseCContractError("replay_frames")
    derived_retired = _derive_phase_c_retired_independence_keys(
        watermark,
        evidence_history_by_event,
    )
    stored_retired = (
        derived_retired
        if frozenset(derived_retired) == retired_independence_keys
        else tuple(sorted(retired_independence_keys))
    )
    final_state = PhaseCTemporalSessionStateV1(
        schema_version=previous.schema_version,
        policy_id=previous.policy_id,
        policy_sha256=previous.policy_sha256,
        call_session_id=previous.call_session_id,
        campaign_profile_id=previous.campaign_profile_id,
        campaign_profile_version=previous.campaign_profile_version,
        watermark=watermark,
        accepted_frames=candidate_frames,
        evidence_history_by_event=evidence_history_by_event,
        accumulator=previous.accumulator,
        hysteresis=previous.hysteresis,
        seen_evidence_refs=historical_seen_evidence_refs,
        seen_independence_keys=historical_seen_independence_keys,
        retired_independence_keys=stored_retired,
        contributing_evidence_refs=previous.contributing_evidence_refs,
        accepted_turn_count=len(candidate_frames),
        last_emitted_selected_signal=(
            previous.last_emitted_selected_signal
        ),
        last_emitted_selected_support=(
            previous.last_emitted_selected_support
        ),
    )
    return final_state, output, context


def _recomputed_state_projection(
    state: PhaseCTemporalSessionStateV1,
    policy: Mapping[str, Any],
) -> tuple[
    PhaseCTemporalSessionStateV1,
    dict[str, Any],
    PhaseCProjectionContextV1,
]:
    return replay_frame_semantics(
        state.accepted_frames,
        policy,
        retired_independence_keys=frozenset(
            state.retired_independence_keys,
        ),
        evidence_history_by_event=state.evidence_history_by_event,
        historical_seen_evidence_refs=state.seen_evidence_refs,
        historical_seen_independence_keys=state.seen_independence_keys,
        watermark=state.watermark,
    )


def _validate_recomputed_state_fields(
    state: PhaseCTemporalSessionStateV1,
    recomputed: PhaseCTemporalSessionStateV1,
) -> None:
    comparisons = (
        ("state_replay_accumulator", state.accumulator, recomputed.accumulator),
        ("state_replay_hysteresis", state.hysteresis, recomputed.hysteresis),
        (
            "state_replay_provenance",
            state.contributing_evidence_refs,
            recomputed.contributing_evidence_refs,
        ),
        (
            "state_replay_counter",
            state.accepted_turn_count,
            recomputed.accepted_turn_count,
        ),
        (
            "state_replay_emission",
            (
                state.last_emitted_selected_signal,
                state.last_emitted_selected_support,
            ),
            (
                recomputed.last_emitted_selected_signal,
                recomputed.last_emitted_selected_support,
            ),
        ),
    )
    for code, actual, expected in comparisons:
        if actual != expected:
            raise PhaseCContractError(code)


def validate_phase_c_state_replay(
    state: PhaseCTemporalSessionStateV1,
    policy: Mapping[str, Any],
) -> None:
    validated_policy = _validated_policy(policy)
    validate_phase_c_session_state(state, validated_policy)
    recomputed, expected_output, context = _recomputed_state_projection(
        state,
        validated_policy,
    )
    _validate_recomputed_state_fields(state, recomputed)
    validate_phase_c_perceived_state(
        expected_output,
        state,
        context,
        validated_policy,
    )


def validate_phase_c_replayed_output(
    payload: object,
    state: PhaseCTemporalSessionStateV1,
    policy: Mapping[str, Any],
) -> dict[str, Any]:
    validated_policy = _validated_policy(policy)
    validate_phase_c_session_state(state, validated_policy)
    recomputed, expected_output, context = _recomputed_state_projection(
        state,
        validated_policy,
    )
    _validate_recomputed_state_fields(state, recomputed)
    validated_payload = validate_phase_c_perceived_state(
        payload,
        state,
        context,
        validated_policy,
    )
    if canonical_json_bytes(validated_payload) != canonical_json_bytes(
        expected_output,
    ):
        raise PhaseCOutputSemanticError("replayed_output_mismatch")
    return validated_payload


def advance(
    previous_state: PhaseCTemporalSessionStateV1 | None,
    frame: PhaseCSyntheticEvidenceFrameV1,
    policy: Mapping[str, Any],
) -> tuple[PhaseCTemporalSessionStateV1, dict[str, Any]]:
    validated_policy = _validated_policy(policy)
    if previous_state is not None:
        validate_phase_c_session_state(
            previous_state,
            validated_policy,
        )
        validate_phase_c_state_replay(
            previous_state,
            validated_policy,
        )
    validate_phase_c_frame(frame, validated_policy)
    next_watermark = validate_phase_c_event_identity(
        frame,
        watermark_for(previous_state, frame),
    )
    replaced_frame = replaced_frame_for(previous_state, frame)
    candidate_frames = candidate_frame_sequence(previous_state, frame)
    validate_candidate_reference_uniqueness(
        previous_state,
        candidate_frames,
        replaced_frame,
    )
    prior_current_keys = frame_independence_keys(
        accepted_frames_for(previous_state),
    )
    candidate_current_keys = frame_independence_keys(candidate_frames)
    retired_keys = retired_independence_keys(previous_state) | (
        prior_current_keys - candidate_current_keys
    )
    next_evidence_history = append_evidence_history_event(
        previous_state,
        frame,
        next_watermark,
    )
    candidate_state, output, projection_context = replay_frame_semantics(
        candidate_frames,
        validated_policy,
        retired_independence_keys=retired_keys,
        evidence_history_by_event=next_evidence_history,
        historical_seen_evidence_refs=evidence_refs_from_history(
            next_evidence_history,
        ),
        historical_seen_independence_keys=independence_keys_from_history(
            next_evidence_history,
        ),
        watermark=next_watermark,
    )
    validate_phase_c_session_state(candidate_state, validated_policy)
    validate_phase_c_perceived_state(
        output,
        candidate_state,
        projection_context,
        validated_policy,
    )
    return candidate_state, output


def replay_validated_frames(
    frames: tuple[PhaseCSyntheticEvidenceFrameV1, ...],
    policy: Mapping[str, Any],
) -> PhaseCReplayV1:
    validated_policy = _validated_policy(policy)
    if type(frames) is not tuple or not frames:
        raise PhaseCContractError("replay_frames")
    for frame in frames:
        validate_phase_c_frame(frame, validated_policy)
    first = frames[0]
    identities = (first.call_session_id, first.campaign_profile_id, first.campaign_profile_version)
    if any((frame.call_session_id, frame.campaign_profile_id, frame.campaign_profile_version) != identities for frame in frames):
        raise PhaseCContractError("replay_identity")
    if any(frame.input_revision != 0 for frame in frames):
        raise PhaseCContractError("replay_correction_not_supported")
    if any(later.turn_sequence <= earlier.turn_sequence for earlier, later in zip(frames, frames[1:])):
        raise PhaseCContractError("replay_turn_sequence")
    turn_ids = tuple(frame.turn_id for frame in frames)
    event_ids = tuple(frame.event_id for frame in frames)
    refs = tuple(atom.evidence_ref for frame in frames for atom in frame.evidence_atoms)
    if len(set(turn_ids)) != len(turn_ids) or len(set(event_ids)) != len(event_ids) or len(set(refs)) != len(refs):
        raise PhaseCContractError("replay_duplicate_identity")
    watermark = initial_phase_c_watermark(first)
    previous: PhaseCTemporalSessionStateV1 | None = None
    states: list[PhaseCTemporalSessionStateV1] = []
    outputs: list[dict[str, Any]] = []
    seen_keys: frozenset[str] = frozenset()
    seen_refs: tuple[str, ...] = ()
    for frame in frames:
        watermark = validate_phase_c_event_identity(frame, watermark)
        fold = fold_frame_support(
            None if previous is None else previous.accumulator,
            frame,
            validated_policy,
            seen_keys,
        )
        hysteresis = update_hysteresis(previous, fold, frame, validated_policy)
        accepted_frames = (frame,) if previous is None else (*previous.accepted_frames, frame)
        history = (
            (frame.event_id, fold.accepted_evidence_refs, fold.accepted_independence_keys),
        ) if previous is None else (*previous.evidence_history_by_event, (frame.event_id, fold.accepted_evidence_refs, fold.accepted_independence_keys))
        seen_refs = (*seen_refs, *fold.accepted_evidence_refs)
        provisional = PhaseCTemporalSessionStateV1(
            schema_version="PhaseCTemporalSessionStateV1",
            policy_id=validated_policy["policy_id"],
            policy_sha256=sha256_bytes(canonical_json_bytes(dict(validated_policy))),
            call_session_id=frame.call_session_id,
            campaign_profile_id=frame.campaign_profile_id,
            campaign_profile_version=frame.campaign_profile_version,
            watermark=watermark,
            accepted_frames=accepted_frames,
            evidence_history_by_event=history,
            accumulator=fold.accumulator,
            hysteresis=hysteresis,
            seen_evidence_refs=seen_refs,
            seen_independence_keys=(
                fold.accepted_independence_keys if previous is None
                else (*previous.seen_independence_keys, *fold.accepted_independence_keys)
            ),
            retired_independence_keys=(),
            contributing_evidence_refs=fold.contributing_evidence_refs,
            accepted_turn_count=len(accepted_frames),
            last_emitted_selected_signal=None if previous is None else previous.last_emitted_selected_signal,
            last_emitted_selected_support=None if previous is None else previous.last_emitted_selected_support,
        )
        validate_phase_c_temporal_state(provisional, validated_policy)
        context = PhaseCProjectionContextV1(
            provisional.last_emitted_selected_signal,
            provisional.last_emitted_selected_support,
            fold,
            frame,
        )
        output = project_perceived_customer_state(provisional, context, validated_policy)
        selected = output["selected_policy_signal"]
        final = PhaseCTemporalSessionStateV1(
            **{
                **provisional.__dict__,
                "last_emitted_selected_signal": None if selected == "none" else selected,
                "last_emitted_selected_support": None if selected == "none" else dict(fold.accumulator.capped_net_support)[selected],
            },
        )
        validate_phase_c_perceived_state(output, final, context, validated_policy)
        validate_phase_c_temporal_state(final, validated_policy)
        previous = final
        seen_keys = frozenset(final.seen_independence_keys)
        states.append(final)
        outputs.append(output)
    return PhaseCReplayV1(final_state=states[-1], states=tuple(states), outputs=tuple(outputs))


def _execute_scenario_attempt(
    prior: PhaseCTemporalSessionStateV1 | None,
    scenario: PhaseCScenarioV1,
    attempt: Any,
    policy: Mapping[str, Any],
) -> tuple[PhaseCTemporalSessionStateV1, dict[str, Any]]:
    payload = materialize_phase_c_scenario_attempt_payload(scenario, attempt)
    frame = parse_phase_c_frame(payload, dict(policy))
    return advance(prior, frame, policy)


def exact_internal_projection(
    state: PhaseCTemporalSessionStateV1,
) -> dict[str, Any]:
    if type(state) is not PhaseCTemporalSessionStateV1:
        raise PhaseCContractError("session_state_type")
    return {
        "gross_supporting_units": dict(
            state.accumulator.gross_supporting_units,
        ),
        "gross_opposing_units": dict(
            state.accumulator.gross_opposing_units,
        ),
        "uncapped_net_support": dict(
            state.accumulator.uncapped_net_support,
        ),
        "capped_net_support": dict(
            state.accumulator.capped_net_support,
        ),
        "contradictory_signals": state.accumulator.contradictory_signals,
        "seen_independence_keys": state.seen_independence_keys,
        "internal_incumbent": state.hysteresis.internal_incumbent,
        "incumbent_tenure": state.hysteresis.incumbent_tenure,
        "entry_confirmation_keys_by_signal": dict(
            state.hysteresis.entry_confirmation_keys_by_signal,
        ),
        "switch_challenger": state.hysteresis.switch_challenger,
        "switch_confirmation_keys": (
            state.hysteresis.switch_confirmation_keys
        ),
        "release_streak": state.hysteresis.release_streak,
        "contributing_evidence_refs": state.contributing_evidence_refs,
        "seen_evidence_refs": state.seen_evidence_refs,
        "retired_independence_keys": state.retired_independence_keys,
        "accepted_turn_count": state.accepted_turn_count,
        "last_emitted_selected_signal": (
            state.last_emitted_selected_signal
        ),
        "last_emitted_selected_support": (
            state.last_emitted_selected_support
        ),
    }


def _expected_internal_projection(
    expected: PhaseCExpectedInternalProjectionV1,
) -> dict[str, Any]:
    if type(expected) is not PhaseCExpectedInternalProjectionV1:
        raise PhaseCContractError("expected_internal_not_object")
    return {
        "gross_supporting_units": dict(expected.gross_supporting_units),
        "gross_opposing_units": dict(expected.gross_opposing_units),
        "uncapped_net_support": dict(expected.uncapped_net_support),
        "capped_net_support": dict(expected.capped_net_support),
        "contradictory_signals": expected.contradictory_signals,
        "seen_independence_keys": expected.seen_independence_keys,
        "internal_incumbent": expected.internal_incumbent,
        "incumbent_tenure": expected.incumbent_tenure,
        "entry_confirmation_keys_by_signal": dict(
            expected.entry_confirmation_keys_by_signal,
        ),
        "switch_challenger": expected.switch_challenger,
        "switch_confirmation_keys": expected.switch_confirmation_keys,
        "release_streak": expected.release_streak,
        "contributing_evidence_refs": expected.contributing_evidence_refs,
        "seen_evidence_refs": expected.seen_evidence_refs,
        "retired_independence_keys": expected.retired_independence_keys,
        "accepted_turn_count": expected.accepted_turn_count,
        "last_emitted_selected_signal": (
            expected.last_emitted_selected_signal
        ),
        "last_emitted_selected_support": (
            expected.last_emitted_selected_support
        ),
    }


def _deterministic_replay_failed(
    scenario: PhaseCScenarioV1,
    policy: Mapping[str, Any],
) -> bool:
    try:
        frames = scenario.sessions[0].frames
        first = replay_validated_frames(frames, policy)
        second = replay_validated_frames(frames, policy)
        return (
            tuple(
                canonical_session_state_bytes(state)
                for state in first.states
            )
            != tuple(
                canonical_session_state_bytes(state)
                for state in second.states
            )
            or tuple(canonical_json_bytes(output) for output in first.outputs)
            != tuple(canonical_json_bytes(output) for output in second.outputs)
        )
    except PhaseCContractError:
        return True


def _correction_semantic_replay_failed(
    scenario: PhaseCScenarioV1,
    state: PhaseCTemporalSessionStateV1 | None,
    output: dict[str, Any] | None,
    policy: Mapping[str, Any],
) -> bool:
    if state is None or output is None:
        return True
    try:
        correction = scenario.sessions[0].frames[-1]
        normalized = replace(
            correction,
            event_id=f"event:{scenario.case_id}:normalized",
            input_revision=0,
        )
        fresh = replay_validated_frames((normalized,), policy)
        validate_phase_c_state_replay(state, policy)
        validate_phase_c_replayed_output(output, state, policy)
        return (
            len(state.accepted_frames) != 1
            or len(state.evidence_history_by_event) != 2
            or len(state.watermark.event_history_by_id) != 2
            or dict(state.watermark.last_input_revision_by_turn).get(
                correction.turn_id,
            ) != 1
            or canonical_semantic_replay_bytes(state, output)
            != canonical_semantic_replay_bytes(
                fresh.final_state,
                fresh.outputs[-1],
            )
        )
    except PhaseCContractError:
        return True


def _session_isolation_failed(
    scenario: PhaseCScenarioV1,
    states: Mapping[str, PhaseCTemporalSessionStateV1 | None],
    policy: Mapping[str, Any],
) -> bool:
    try:
        sessions = {
            session.session_alias: session
            for session in scenario.sessions
        }
        separate = {
            alias: replay_validated_frames(session.frames, policy)
            for alias, session in sessions.items()
        }
        if any(
            states[alias] is None
            or canonical_session_state_bytes(states[alias])
            != canonical_session_state_bytes(replay.final_state)
            for alias, replay in separate.items()
        ):
            return True
        aliases = tuple(sessions)
        left, _ = advance(None, sessions[aliases[0]].frames[0], policy)
        right, _ = advance(None, sessions[aliases[1]].frames[0], policy)
        for prior, incoming in (
            (left, sessions[aliases[1]].frames[1]),
            (right, sessions[aliases[0]].frames[1]),
        ):
            before = canonical_session_state_bytes(prior)
            try:
                advance(prior, incoming, policy)
            except PhaseCContractError as exc:
                if (
                    exc.code != "cross_session"
                    or canonical_session_state_bytes(prior) != before
                ):
                    return True
            else:
                return True
        return False
    except (KeyError, PhaseCContractError):
        return True


def _phase_c_privacy_inspection_failed(value: object) -> bool:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                return True
            lowered = key.lower()
            if (
                any(
                    fragment in lowered
                    for fragment in FORBIDDEN_PHASE_C_KEY_FRAGMENTS
                )
                or any(case_id in key for case_id in EXPECTED_SCENARIO_IDS)
            ):
                return True
            if _phase_c_privacy_inspection_failed(item):
                return True
        return False
    if type(value) in (list, tuple):
        return any(
            _phase_c_privacy_inspection_failed(item)
            for item in value
        )
    if type(value) is str:
        return (
            EVIDENCE_REF_PATTERN.fullmatch(value) is not None
            or value.startswith((
                "evidence:uuid:",
                "ind:",
                "session:",
                "turn:",
                "event:",
                "campaign:",
                "version:",
            ))
            or any(case_id in value for case_id in EXPECTED_SCENARIO_IDS)
        )
    return type(value) not in (bool, int)


def _build_phase_c_evaluation(
    outcomes: tuple[PhaseCScenarioOutcomeV1, ...],
) -> PhaseCScenarioEvaluationV1:
    family_counts = {
        name: sum(outcome.family == name for outcome in outcomes)
        for name in FAMILY_COUNT_ORDER
    }
    signal_counts = {
        name: sum(outcome.signal_family == name for outcome in outcomes)
        for name in SIGNAL_FAMILY_COUNT_ORDER
    }
    modality_counts = {
        name: sum(outcome.modality_family == name for outcome in outcomes)
        for name in MODALITY_FAMILY_COUNT_ORDER
    }
    abstention_counts = {
        name: sum(
            dict(outcome.abstention_reason_counts)[name]
            for outcome in outcomes
        )
        for name in EMITTED_ABSTENTION_COUNT_ORDER
    }
    invariant_counts = {
        name: sum(
            name in outcome.failed_invariants
            for outcome in outcomes
        )
        for name in INVARIANT_NAMES
    }
    if (
        family_counts != dict(EXPECTED_COUNTS_BY_FAMILY)
        or signal_counts != dict(EXPECTED_COUNTS_BY_SIGNAL_FAMILY)
        or modality_counts != dict(EXPECTED_COUNTS_BY_MODALITY_FAMILY)
    ):
        raise PhaseCContractError("scenario_classification_counts")
    passed = sum(outcome.passed for outcome in outcomes)
    failed = len(outcomes) - passed
    if (
        failed == 0
        and abstention_counts
        != dict(EXPECTED_COUNTS_BY_ABSTENTION_REASON)
    ):
        raise PhaseCContractError("scenario_abstention_counts")
    return PhaseCScenarioEvaluationV1(
        total_scenarios=len(outcomes),
        passed_scenarios=passed,
        failed_scenarios=failed,
        outcomes=outcomes,
        counts_by_family=tuple(
            (name, family_counts[name])
            for name in FAMILY_COUNT_ORDER
        ),
        counts_by_signal=tuple(
            (name, signal_counts[name])
            for name in SIGNAL_FAMILY_COUNT_ORDER
        ),
        counts_by_modality=tuple(
            (name, modality_counts[name])
            for name in MODALITY_FAMILY_COUNT_ORDER
        ),
        counts_by_abstention_reason=tuple(
            (name, abstention_counts[name])
            for name in EMITTED_ABSTENTION_COUNT_ORDER
        ),
        invariant_counts=tuple(
            (name, invariant_counts[name])
            for name in INVARIANT_NAMES
        ),
        deterministic_replay_passed=(
            invariant_counts["deterministic_replay"] == 0
        ),
        privacy_boundary_passed=all(
            invariant_counts[name] == 0
            for name in (
                "rejection_no_mutation",
                "session_isolation",
                "semantic_output",
                "privacy_boundary",
            )
        ),
    )


def evaluate_phase_c_scenarios(
    policy: Mapping[str, Any],
    scenarios: object,
) -> PhaseCScenarioEvaluationV1:
    validated_policy = _validated_policy(policy)
    if type(scenarios) is dict:
        ordered_scenarios = tuple(scenarios.values())
    elif type(scenarios) is tuple:
        ordered_scenarios = scenarios
    else:
        raise PhaseCContractError("scenario_evaluation_scenarios")
    if (
        tuple(
            scenario.case_id
            for scenario in ordered_scenarios
            if type(scenario) is PhaseCScenarioV1
        )
        != EXPECTED_SCENARIO_IDS
        or len(ordered_scenarios) != len(EXPECTED_SCENARIO_IDS)
    ):
        raise PhaseCContractError("scenario_ids")

    outcomes: list[PhaseCScenarioOutcomeV1] = []
    for scenario in ordered_scenarios:
        if type(scenario) is not PhaseCScenarioV1:
            raise PhaseCContractError("scenario_type")
        if (
            scenario.family,
            scenario.signal_family,
            scenario.modality_family,
        ) != EXPECTED_SCENARIO_CLASSIFICATIONS[scenario.case_id]:
            raise PhaseCContractError("scenario_classification")
        states: dict[str, PhaseCTemporalSessionStateV1 | None] = {
            session.session_alias: None
            for session in scenario.sessions
        }
        outputs: dict[str, dict[str, Any]] = {}
        failed: set[str] = set()
        rejection_count = 0
        abstention_counts = {
            name: 0
            for name in EMITTED_ABSTENTION_COUNT_ORDER
        }

        for attempt, expected in zip(
            scenario.attempt_order,
            scenario.expected_steps,
            strict=True,
        ):
            prior = states[attempt.state_session_alias]
            prior_bytes = canonical_session_state_bytes(prior)
            try:
                successor, output = _execute_scenario_attempt(
                    prior,
                    scenario,
                    attempt,
                    validated_policy,
                )
            except PhaseCOutputSemanticError:
                failed.add("golden_projection")
                failed.add("semantic_output")
                if canonical_session_state_bytes(prior) != prior_bytes:
                    failed.add("rejection_no_mutation")
                continue
            except PhaseCContractError as exc:
                if (
                    expected.disposition != "rejected"
                    or exc.code != expected.rejection_code
                ):
                    failed.add("golden_projection")
                else:
                    rejection_count += 1
                if canonical_session_state_bytes(prior) != prior_bytes:
                    failed.add("rejection_no_mutation")
                continue

            if expected.disposition == "rejected":
                failed.add("golden_projection")
                failed.add(
                    UNEXPECTED_ACCEPTANCE_SAFETY_INVARIANT_BY_CASE[
                        scenario.case_id
                    ],
                )
                if canonical_session_state_bytes(prior) != prior_bytes:
                    failed.add("rejection_no_mutation")
                continue

            try:
                validated_output = validate_phase_c_replayed_output(
                    output,
                    successor,
                    validated_policy,
                )
            except PhaseCContractError:
                failed.add("golden_projection")
                failed.add("semantic_output")
                continue

            if (
                canonical_json_bytes(validated_output)
                != expected.expected_output_bytes
            ):
                failed.add("golden_projection")
            if exact_internal_projection(successor) != (
                _expected_internal_projection(expected.expected_internal)
            ):
                failed.add("golden_projection")
            states[attempt.state_session_alias] = successor
            outputs[attempt.state_session_alias] = validated_output
            for reason in validated_output["abstention_reasons"]:
                abstention_counts[reason] += 1

        if (
            scenario.case_id == "canonical_replay_bytes"
            and _deterministic_replay_failed(
                scenario,
                validated_policy,
            )
        ):
            failed.add("deterministic_replay")
        if (
            scenario.case_id == "latest_turn_correction_replay"
            and _correction_semantic_replay_failed(
                scenario,
                states["A"],
                outputs.get("A"),
                validated_policy,
            )
        ):
            failed.add("correction_semantic_replay")
        if (
            scenario.case_id == "simultaneous_sessions_isolated"
            and _session_isolation_failed(
                scenario,
                states,
                validated_policy,
            )
        ):
            failed.add("session_isolation")

        failed_invariants = tuple(
            name
            for name in INVARIANT_NAMES
            if name in failed
        )
        outcomes.append(PhaseCScenarioOutcomeV1(
            case_id=scenario.case_id,
            family=scenario.family,
            signal_family=scenario.signal_family,
            modality_family=scenario.modality_family,
            passed=not failed_invariants,
            failed_invariants=failed_invariants,
            rejection_count=rejection_count,
            abstention_reason_counts=tuple(
                (name, abstention_counts[name])
                for name in EMITTED_ABSTENTION_COUNT_ORDER
            ),
        ))

    evaluation = _build_phase_c_evaluation(tuple(outcomes))
    privacy_projection = {
        "total_scenarios": evaluation.total_scenarios,
        "passed_scenarios": evaluation.passed_scenarios,
        "failed_scenarios": evaluation.failed_scenarios,
        "counts_by_family": dict(evaluation.counts_by_family),
        "counts_by_signal": dict(evaluation.counts_by_signal),
        "counts_by_modality": dict(evaluation.counts_by_modality),
        "counts_by_abstention_reason": dict(
            evaluation.counts_by_abstention_reason,
        ),
        "invariant_counts": dict(evaluation.invariant_counts),
        "deterministic_replay_passed": (
            evaluation.deterministic_replay_passed
        ),
        "privacy_boundary_passed": evaluation.privacy_boundary_passed,
    }
    privacy_failed = _phase_c_privacy_inspection_failed(
        privacy_projection,
    )
    if not privacy_failed:
        try:
            canonical_json_bytes(privacy_projection)
        except PhaseCContractError:
            privacy_failed = True
    if privacy_failed:
        first = evaluation.outcomes[0]
        first_failed = tuple(
            name
            for name in INVARIANT_NAMES
            if name in (*first.failed_invariants, "privacy_boundary")
        )
        outcomes = [
            replace(
                first,
                passed=False,
                failed_invariants=first_failed,
            ),
            *evaluation.outcomes[1:],
        ]
        evaluation = _build_phase_c_evaluation(tuple(outcomes))
    return evaluation
