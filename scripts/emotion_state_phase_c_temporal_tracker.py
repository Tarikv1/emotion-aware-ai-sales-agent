from __future__ import annotations

from typing import Any, Mapping

from runtime.contracts.emotion_state_contracts import (
    validate_perceived_customer_state,
)
from scripts.emotion_state_phase_c_contracts import (
    PhaseCContractError,
    PhaseCFrameFoldV1,
    PhaseCHysteresisV1,
    PhaseCProjectionContextV1,
    PhaseCReplayV1,
    PhaseCSignalAccumulatorV1,
    PhaseCSyntheticEvidenceAtomV1,
    PhaseCSyntheticEvidenceFrameV1,
    PhaseCTemporalSessionStateV1,
    canonical_json_bytes,
    initial_phase_c_watermark,
    sha256_bytes,
    validate_phase_c_event_identity,
    validate_phase_c_atom,
    validate_phase_c_frame,
    validate_phase_c_frame_fold,
    validate_phase_c_hysteresis,
    validate_phase_c_policy,
    validate_phase_c_perceived_state,
    validate_phase_c_seen_independence_keys,
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
