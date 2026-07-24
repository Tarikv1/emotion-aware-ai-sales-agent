# EMOTION-STATE-003 Phase C0 Synthetic Temporal Mechanics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a fail-closed offline reference reducer that proves exact
synthetic temporal-state mechanics without admitting Phase B acoustic outputs,
customer data, runtime behavior, or performance claims.

**Architecture:** A pure reducer consumes an immutable explicit session state,
one validated symbolic evidence frame, and one hash-bound fixed-point policy.
It returns the next explicit session state and a contract-valid
`PerceivedCustomerStateV1`; runners and validators operate only on frozen
tracked fixtures and publish aggregate-only evidence.

**Tech Stack:** Python 3.11 or newer; standard-library `dataclasses`, `hashlib`,
`json`, `os`, `pathlib`, `re`, `stat`, `types`, and `unittest`; existing
`runtime/contracts/emotion_state_contracts.py` as a read-only output validator
and event-identity parity oracle.

## Global Constraints

- Planning base:
  `bb1c4231e6d4552f215a96bd0a1d862986775c32`.
- Approved design:
  `docs/superpowers/specs/2026-07-24-emotion-state-phase-c0-synthetic-temporal-mechanics-design.md`.
- Checkpoint ID:
  `EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics`.
- Evidence policy version:
  `emotion-state-evidence-v2`.
- Policy ID:
  `emotion-state-phase-c0-synthetic-v1`.
- `fixture_only` is always `true`; `runtime_approved` is always `false`.
- Valence, activation, and engagement are always `not_inferable`.
- All tracker arithmetic is integer/fixed-point. Float construction occurs only
  at the final `capped_net_support / 1000.0` contract projection.
- Every JSON byte authority uses:

```python
(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
```

- Policy/scenario identity hashes use the canonical bytes of the strictly
  parsed object, never raw checkout bytes; Windows `core.autocrlf=true` may
  change tracked source-file line endings. Generated result/report files are
  written as physical LF bytes and their raw bytes are authoritative. Two
  exact-path `text eol=lf` rules in `.gitattributes` preserve those bytes across
  checkout; no pattern or other path is affected.
- The policy and scenario JSON files are frozen and committed before reducer
  implementation begins.
- Phase B features, probabilities, model outputs, fitted parameters, result
  content, report content, ignored state, and the closed lockbox are forbidden
  tracker inputs.
- No task may read CREMA-D, AMI, public-dataset material, `data/private/`, or
  `data/private-restricted/`.
- No task may install dependencies, access the network, call a provider, place
  a call, run a provider/conversation simulation, adapt an external source,
  modify prompts/responses/KB/voice/LLM/phone settings, modify runtime code,
  activate runtime behavior, create a policy adapter, create BRAIN integration,
  merge, rewrite history, begin Phase D, or claim production/customer-emotion/
  commercial readiness.
- Local deterministic fixture tests are not conversation simulations.
- Existing `runtime/contracts/emotion_state_contracts.py` remains byte
  unchanged.
- Every implementation task follows strict RED/GREEN TDD, receives independent
  specification review and code-quality review, and commits only its declared
  files.
- No gate implicitly authorizes the next gate.

## Boundary Gates

1. **Plan gate:** this document may be written, reviewed, and committed. It
   authorizes no implementation.
2. **Offline implementation gate:** Tasks 1-8 may edit the declared tracked
   files and run deterministic fixture tests only after explicit implementation
   authorization.
3. **Candidate gate:** Task 9 may create and independently validate the exact
   ignored candidate pair, and may commit the reviewed candidate disposition
   to the tracked protocol, only after separate explicit candidate
   authorization and after Tasks 1-8 pass and are independently reviewed.
4. **Canonical gate:** Task 10 may publish, independently validate, document,
   and commit the exact aggregate canonical pair only after separate explicit
   canonical authorization and after candidate review.
5. **Push gate:** pushing the implementation branch requires separate explicit
   authorization. Merge and Phase D remain separate regardless of push.

## Per-Task Post-GREEN Ledger

After each task-specific focused GREEN in Tasks 1-9, and before that task's
independent review or commit, run this exact common ledger:

```powershell
python -m unittest scripts.test_emotion_state_003_phase_c0 -v
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe -m unittest scripts.test_emotion_state_002_phase_b.PhaseBContractTests -v
git diff --check
```

The reviewed Phase B interpreter is an immutable test dependency only. The
task-specific GREEN block must also compile every Phase C0 Python file that
exists at that task. Tasks 1 and 3 run thesis-reference, drift, context-policy,
and setup gates for their protocol/fixture changes. Tasks 8 and 9 also update
the methodology trace and therefore run those four gates plus the thesis-update
gate. Tasks 2 and 4-7 do not claim the complete documentation-gate ledger;
any extra focused repository guard named in their block still applies. Task 10
runs the complete pre-canonical guarded ledger. A common-ledger failure blocks
review and commit.

## File Responsibility Map

### Tracked additions

- `.gitattributes`
  contains only the two exact Phase C0 canonical output `text eol=lf` rules.
- `scripts/emotion_state_phase_c_contracts.py`
  owns exact policy, atom, frame, watermark, session-state, scenario, aggregate,
  and semantic-output validation. It contains no reducer logic.
- `scripts/emotion_state_phase_c_temporal_tracker.py`
  owns fixed-point folding, decay, caps, contradiction, hysteresis, correction
  replay, and output projection. It performs no I/O.
- `scripts/run_emotion_state_003_phase_c0.py`
  loads frozen tracked inputs, evaluates scenarios, builds aggregate evidence,
  renders deterministic bytes, and writes only an allowlisted pair root.
- `scripts/validate_emotion_state_003_phase_c0.py`
  independently validates policy/scenarios, candidate or canonical aggregate
  content, decision semantics, privacy boundaries, and report/result binding.
- `scripts/test_emotion_state_003_phase_c0.py`
  contains all focused, golden, mutation, parity, metamorphic, runner, and
  validator tests.
- `research/experiments/cases/emotion-state-003-phase-c0-policy.json`
  is the sole immutable fixed-point policy.
- `research/experiments/cases/emotion-state-003-phase-c0-scenarios.json`
  is the sole frozen scenario/golden-expectation matrix.
- `research/experiments/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics.md`
  records the question, protocol, decision rule, execution boundary, and
  non-claims.
- `research/experiments/generated/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics/result.json`
  is the aggregate-only canonical machine result.
- `research/experiments/generated/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics/report.md`
  is the deterministic human-readable rendering of the result.

### Tracked documentation modifications

- `docs/thesis/METHODOLOGY_LOG.md`
  is updated at Tasks 8 and 9 and again at canonical closeout.
- `docs/product/CHECKPOINT_INDEX.md`
- `docs/product/COMMANDS.md`
- `docs/thesis/ROADMAP.md`

The three paths after the methodology log are modified only at Task 10
closeout.

### Ignored local state

- `.tmp/emotion-state-003-phase-c0/`
- `.tmp/emotion-state-003-phase-c0/candidate/result.json`
- `.tmp/emotion-state-003-phase-c0/candidate/report.md`

The candidate command may create the exact real parent
`.tmp/emotion-state-003-phase-c0` when absent, after verifying `.tmp` is a real
non-reparse directory. That parent may contain only `candidate` or
`candidate.stage`. The runner may use only the exact sibling directory
`.tmp/emotion-state-003-phase-c0/candidate.stage` while atomically publishing
the candidate. Canonical publication similarly uses only
`research/experiments/generated/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics.stage`.
Each staging directory must be absent before the run and absent after success
or handled failure. No other ignored or staging path is authorized.

## Frozen Policy Authority

Task 1 writes this exact semantic policy. JSON key order is irrelevant because
canonical bytes sort keys; array order is authoritative.

```json
{
  "abstained_allowed_effects": ["preserve"],
  "abstention_primary_priority": [
    "contradictory_evidence",
    "low_audio_quality",
    "missing_input",
    "insufficient_evidence"
  ],
  "abstention_reason_order": [
    "phase_a_no_audio",
    "insufficient_evidence",
    "contradictory_evidence",
    "low_audio_quality",
    "missing_input",
    "stale_input"
  ],
  "acoustic_only_cap": 400,
  "acoustic_only_allowed_effects": ["preserve"],
  "agreement_bonus": 100,
  "agreement_eligibility": "newly_contributing_positive_support_atoms_only",
  "agreement_requirements": {
    "distinct_evidence_refs": 2,
    "distinct_independence_keys": 2,
    "distinct_modalities": 2
  },
  "allowed_effect_order": [
    "preserve",
    "soften",
    "shorten",
    "clarify",
    "acknowledge",
    "handoff",
    "abstain",
    "stop"
  ],
  "allowed_effects_by_signal": {
    "confusion": ["preserve", "shorten", "clarify", "acknowledge", "handoff"],
    "disengagement": ["preserve", "soften", "shorten", "acknowledge", "handoff"],
    "frustration": ["preserve", "soften", "shorten", "acknowledge", "handoff"],
    "hesitation": ["preserve", "clarify", "acknowledge"],
    "interest": ["preserve"]
  },
  "allowed_modalities_by_evidence_class": {
    "dialogue_context": ["dialogue"],
    "synthetic_acoustic_symbol": ["acoustic"],
    "transcript_meaning": ["text"],
    "unsolicited_explicit_statement": ["text"],
    "weak_behavioral_proxy": ["dialogue"]
  },
  "base_support_units": {
    "dialogue_context": 300,
    "synthetic_acoustic_symbol": 180,
    "transcript_meaning": 450,
    "unsolicited_explicit_statement": 700,
    "weak_behavioral_proxy": 100
  },
  "blocked_effect_order": [
    "expand_action_set",
    "increase_persuasion_intensity",
    "create_new_close",
    "override_refusal",
    "override_do_not_call",
    "rewrite_protected_text",
    "exploit_vulnerability",
    "voice_only_emotional_appeal",
    "unsupported_claim",
    "automatic_close_or_payment"
  ],
  "canonical_direction_order": ["supports", "opposes"],
  "canonical_evidence_class_order": [
    "unsolicited_explicit_statement",
    "transcript_meaning",
    "dialogue_context",
    "synthetic_acoustic_symbol",
    "weak_behavioral_proxy"
  ],
  "canonical_modality_order": ["text", "dialogue", "acoustic"],
  "canonical_quality_order": ["high", "medium", "low", "unusable"],
  "canonical_signal_order": [
    "confusion",
    "disengagement",
    "frustration",
    "hesitation",
    "interest"
  ],
  "confirmation_counts": {
    "entry": 2,
    "explicit_statement_entry": 1,
    "release": 2,
    "switch": 2
  },
  "confirmation_key_policy": "one_canonical_new_supporting_key_per_signal_per_turn",
  "confidence_bucket_thresholds": {
    "high": 750,
    "medium": 550
  },
  "contradiction_cap": 350,
  "contradiction_thresholds": {
    "gross_opposition": 300,
    "gross_support": 300
  },
  "correction_policy": "most_recent_turn_exact_next_revision_only",
  "evidence_policy_version": "emotion-state-evidence-v2",
  "emitted_abstention_reasons": [
    "insufficient_evidence",
    "contradictory_evidence",
    "low_audio_quality",
    "missing_input"
  ],
  "entry_threshold": 550,
  "explicit_entry_evidence_class": "unsolicited_explicit_statement",
  "fixture_only": true,
  "minimum_switch_advantage": 150,
  "policy_id": "emotion-state-phase-c0-synthetic-v1",
  "quality_multipliers": {
    "high": 1000,
    "low": 400,
    "medium": 750,
    "unusable": 0
  },
  "quality_cap_basis": "highest_nonzero_current_contributing_quality",
  "release_threshold": 350,
  "retained_support_milli": 800,
  "rounding_policy": "integer_floor_toward_zero",
  "scale": 1000,
  "schema_version": "PhaseCFrozenEvidencePolicyV1",
  "support_saturation": 1000,
  "switch_threshold": 650,
  "tie_policy": {
    "incumbent": "retain_unless_all_switch_conditions_pass",
    "no_incumbent": "abstain"
  },
  "total_quality_caps": {
    "high": 1000,
    "low": 400,
    "medium": 750,
    "unusable": 0
  },
  "trajectory_delta_threshold": 100,
  "visibility_threshold": 200
}
```

## Frozen Scenario Authority

The scenario matrix has exactly these 30 IDs. No reducer code may exist before
this list and every expected projection are tracked and committed.

Stale turn, turn-ID/sequence rebound, duplicate/skipped revision, and nonzero
first-revision cases remain exact Task 2 identity-parity tests; output-contract
field/cross-field failures remain Task 5 semantic mutation tests. They are not
additional matrix IDs.

```python
EXPECTED_SCENARIO_IDS = (
    "explicit_confusion_entry",
    "explicit_disengagement_entry",
    "explicit_frustration_entry",
    "explicit_hesitation_entry",
    "explicit_interest_entry",
    "transcript_three_turn_entry",
    "repeated_independence_zero_addition",
    "duplicate_event_rejected",
    "duplicate_reference_rejected",
    "acoustic_only_capped",
    "multimodal_two_turn_entry",
    "same_signal_contradiction",
    "low_quality_acoustic_abstains",
    "empty_frame_missing_input",
    "release_after_two_below_threshold",
    "switch_after_two_confirmations",
    "entry_tie_abstains",
    "incumbent_survives_unqualified_challenger",
    "latest_turn_correction_replay",
    "closed_turn_correction_rejected",
    "cross_session_rejected",
    "cross_campaign_rejected",
    "wrong_campaign_version_rejected",
    "noncanonical_atom_order_rejected",
    "forbidden_phase_b_field_rejected",
    "simultaneous_sessions_isolated",
    "canonical_replay_bytes",
    "dialogue_only_low_quality",
    "support_saturation",
    "opposition_below_contradiction_threshold",
)

REJECTION_CASE_IDS = (
    "duplicate_event_rejected",
    "duplicate_reference_rejected",
    "closed_turn_correction_rejected",
    "cross_session_rejected",
    "cross_campaign_rejected",
    "wrong_campaign_version_rejected",
    "noncanonical_atom_order_rejected",
    "forbidden_phase_b_field_rejected",
)

UNEXPECTED_ACCEPTANCE_SAFETY_INVARIANT_BY_CASE = {
    "duplicate_event_rejected": "rejection_no_mutation",
    "duplicate_reference_rejected": "rejection_no_mutation",
    "closed_turn_correction_rejected": "rejection_no_mutation",
    "cross_session_rejected": "session_isolation",
    "cross_campaign_rejected": "session_isolation",
    "wrong_campaign_version_rejected": "session_isolation",
    "noncanonical_atom_order_rejected": "privacy_boundary",
    "forbidden_phase_b_field_rejected": "privacy_boundary",
}

EXPECTED_SCENARIO_CLASSIFICATIONS = {
    "explicit_confusion_entry": ("entry", "confusion", "text"),
    "explicit_disengagement_entry": ("entry", "disengagement", "text"),
    "explicit_frustration_entry": ("entry", "frustration", "text"),
    "explicit_hesitation_entry": ("entry", "hesitation", "text"),
    "explicit_interest_entry": ("entry", "interest", "text"),
    "transcript_three_turn_entry": ("entry", "confusion", "text"),
    "repeated_independence_zero_addition": ("independence", "interest", "text"),
    "duplicate_event_rejected": ("rejection", "confusion", "text"),
    "duplicate_reference_rejected": ("rejection", "confusion", "text"),
    "acoustic_only_capped": ("abstention", "hesitation", "acoustic"),
    "multimodal_two_turn_entry": ("entry", "frustration", "multimodal"),
    "same_signal_contradiction": ("contradiction", "confusion", "multimodal"),
    "low_quality_acoustic_abstains": ("abstention", "hesitation", "acoustic"),
    "empty_frame_missing_input": ("abstention", "none", "none"),
    "release_after_two_below_threshold": ("hysteresis", "frustration", "text"),
    "switch_after_two_confirmations": ("hysteresis", "mixed", "text"),
    "entry_tie_abstains": ("hysteresis", "mixed", "text"),
    "incumbent_survives_unqualified_challenger": ("hysteresis", "mixed", "text"),
    "latest_turn_correction_replay": ("correction", "interest", "text"),
    "closed_turn_correction_rejected": ("rejection", "confusion", "text"),
    "cross_session_rejected": ("rejection", "confusion", "text"),
    "cross_campaign_rejected": ("rejection", "confusion", "text"),
    "wrong_campaign_version_rejected": ("rejection", "confusion", "text"),
    "noncanonical_atom_order_rejected": ("rejection", "mixed", "text"),
    "forbidden_phase_b_field_rejected": ("rejection", "confusion", "text"),
    "simultaneous_sessions_isolated": ("isolation", "mixed", "text"),
    "canonical_replay_bytes": ("determinism", "confusion", "text"),
    "dialogue_only_low_quality": ("abstention", "hesitation", "dialogue"),
    "support_saturation": ("saturation", "confusion", "text"),
    "opposition_below_contradiction_threshold": (
        "contradiction",
        "confusion",
        "multimodal",
    ),
}

FAMILY_COUNT_ORDER = (
    "entry",
    "independence",
    "rejection",
    "abstention",
    "contradiction",
    "hysteresis",
    "correction",
    "isolation",
    "determinism",
    "saturation",
)
SIGNAL_FAMILY_COUNT_ORDER = (
    "confusion",
    "disengagement",
    "frustration",
    "hesitation",
    "interest",
    "mixed",
    "none",
)
MODALITY_FAMILY_COUNT_ORDER = (
    "text",
    "dialogue",
    "acoustic",
    "multimodal",
    "none",
)
EMITTED_ABSTENTION_COUNT_ORDER = (
    "insufficient_evidence",
    "contradictory_evidence",
    "low_audio_quality",
    "missing_input",
)

EXPECTED_COUNTS_BY_FAMILY = {
    "entry": 7,
    "independence": 1,
    "rejection": 8,
    "abstention": 4,
    "contradiction": 2,
    "hysteresis": 4,
    "correction": 1,
    "isolation": 1,
    "determinism": 1,
    "saturation": 1,
}
EXPECTED_COUNTS_BY_SIGNAL_FAMILY = {
    "confusion": 13,
    "disengagement": 1,
    "frustration": 3,
    "hesitation": 4,
    "interest": 3,
    "mixed": 5,
    "none": 1,
}
EXPECTED_COUNTS_BY_MODALITY_FAMILY = {
    "text": 23,
    "dialogue": 1,
    "acoustic": 2,
    "multimodal": 3,
    "none": 1,
}
EXPECTED_COUNTS_BY_ABSTENTION_REASON = {
    "insufficient_evidence": 24,
    "contradictory_evidence": 1,
    "low_audio_quality": 1,
    "missing_input": 11,
}

INVARIANT_NAMES = (
    "golden_projection",
    "rejection_no_mutation",
    "correction_semantic_replay",
    "session_isolation",
    "deterministic_replay",
    "semantic_output",
    "privacy_boundary",
)

SAFETY_INVARIANT_NAMES = (
    "rejection_no_mutation",
    "session_isolation",
    "deterministic_replay",
    "semantic_output",
    "privacy_boundary",
)

CLAIM_OR_CONSUMPTION_FLAG_NAMES = (
    "phase_b_inputs_consumed",
    "public_or_private_data_consumed",
    "runtime_modified_or_activated",
    "provider_or_call_used",
    "policy_enforcement_proven",
    "emotion_accuracy_proven",
    "production_readiness_proven",
)
```

All Python mapping literals in the frozen authority are semantic display.
Production module authorities expose them as `types.MappingProxyType` over a
fresh unreferenced dict whose nested values are tuples/frozensets/scalars.
No production module global has runtime type `dict`, `list`, or `set`; tests
may construct mutable copies locally.

Scenario container field sets are exact:

```python
SCENARIO_MATRIX_FIELDS = frozenset({
    "schema_version", "policy_id", "scenarios",
})
SCENARIO_FIELDS = frozenset({
    "case_id", "family", "signal_family", "modality_family",
    "sessions", "attempt_order", "expected_steps",
})
SCENARIO_SESSION_FIELDS = frozenset({"session_alias", "frames"})
SCENARIO_ATTEMPT_FIELDS = frozenset({
    "state_session_alias", "frame_session_alias", "frame_index",
    "mutation_kind", "mutation_parameter",
})
```

Each expected accepted step records the complete output bytes and an exact
internal projection. The scenario loader canonicalizes the `expected_output`
object directly; no reducer or output renderer may construct golden bytes.
This is the complete shape, shown for `explicit_confusion_entry`:

```json
{
  "disposition": "accepted",
  "expected_output": {
    "call_session_id": "session:explicit_confusion_entry:A",
    "campaign_profile_id": "campaign:phase-c0",
    "campaign_profile_version": "version:1",
    "turn_id": "turn:explicit_confusion_entry:A:0",
    "turn_sequence": 0,
    "valence_estimate": "not_inferable",
    "activation_estimate": "not_inferable",
    "engagement_estimate": "not_inferable",
    "operational_signals": ["confusion"],
    "confidence_by_signal": {"confusion": 0.7},
    "selected_policy_signal": "confusion",
    "selected_signal_confidence_bucket": "medium",
    "overall_evidence_quality": "text_only",
    "trajectory": "insufficient_history",
    "evidence_refs": [
      "evidence:uuid:00000000-0000-4000-8000-010100000000"
    ],
    "signal_provenance_by_modality": {
      "confusion": {
        "text": [
          "evidence:uuid:00000000-0000-4000-8000-010100000000"
        ]
      }
    },
    "allowed_policy_effects": [
      "preserve",
      "shorten",
      "clarify",
      "acknowledge",
      "handoff"
    ],
    "blocked_policy_effects": [
      "expand_action_set",
      "increase_persuasion_intensity",
      "create_new_close",
      "override_refusal",
      "override_do_not_call",
      "rewrite_protected_text",
      "exploit_vulnerability",
      "voice_only_emotional_appeal",
      "unsupported_claim",
      "automatic_close_or_payment"
    ],
    "abstained": false,
    "abstention_reasons": [],
    "evidence_policy_version": "emotion-state-evidence-v2",
    "runtime_approved": false
  },
  "expected_internal": {
    "gross_supporting_units": {
      "confusion": 700,
      "disengagement": 0,
      "frustration": 0,
      "hesitation": 0,
      "interest": 0
    },
    "gross_opposing_units": {
      "confusion": 0,
      "disengagement": 0,
      "frustration": 0,
      "hesitation": 0,
      "interest": 0
    },
    "uncapped_net_support": {
      "confusion": 700,
      "disengagement": 0,
      "frustration": 0,
      "hesitation": 0,
      "interest": 0
    },
    "capped_net_support": {
      "confusion": 700,
      "disengagement": 0,
      "frustration": 0,
      "hesitation": 0,
      "interest": 0
    },
    "contradictory_signals": [],
    "seen_independence_keys": [
      "ind:explicit_confusion_entry:A:0:0:0"
    ],
    "internal_incumbent": "confusion",
    "incumbent_tenure": 1,
    "entry_confirmation_keys_by_signal": {
      "confusion": [],
      "disengagement": [],
      "frustration": [],
      "hesitation": [],
      "interest": []
    },
    "switch_challenger": null,
    "switch_confirmation_keys": [],
    "release_streak": 0,
    "contributing_evidence_refs": [
      "evidence:uuid:00000000-0000-4000-8000-010100000000"
    ],
    "seen_evidence_refs": [
      "evidence:uuid:00000000-0000-4000-8000-010100000000"
    ],
    "retired_independence_keys": [],
    "accepted_turn_count": 1,
    "last_emitted_selected_signal": "confusion",
    "last_emitted_selected_support": 700
  }
}
```

Every accepted expectation contains every one of the 22 exact
`PERCEIVED_STATE_FIELDS`, with all maps/lists in canonical policy order.
`expected_internal` contains exactly the 18 fields shown above; its four
numeric signal maps and entry-confirmation map are dense across all five
signals. Thus confidence, provenance, confirmation, release, switch, and
last-emission behavior are frozen before reducer code exists. Rejection
expectations retain the smaller exact shape below because no successor state
or output may exist.

Each expected rejection records:

```json
{
  "disposition": "rejected",
  "rejection_code": "duplicate_event",
  "prior_state_bytes_unchanged": true
}
```

All `sessions[*].frames` are valid base-frame payloads. Parser-negative cases
do not smuggle malformed frames through the scenario loader. Instead, an
attempt carries one exact mutation descriptor:

- `mutation_kind="none"` with `mutation_parameter=null`;
- `mutation_kind="reverse_atom_order"` with `mutation_parameter=null`; or
- `mutation_kind="add_forbidden_field"` with `mutation_parameter` equal to one
  of `acoustic_features`, `probabilities`, `model_id`, or `dataset_id`.

The scenario contract materializes the mutation only at attempt execution and
then routes the resulting payload through the normal strict frame parser.
Mutation descriptors are negative-test authority only and never become
tracker inputs.

### Exact fixture-recipe language

The matrix is hand-authored from this closed recipe language. A zero-context
worker must expand it mechanically and may not choose alternative frames:

- sessions are `A` then `B`; their one-based ordinals are `01` and `02`;
- a frame label `A.2r1` means session `A`, `turn_sequence=2`,
  `input_revision=1`;
- default identities are
  `session:<case_id>:<alias>`, `campaign:phase-c0`, `version:1`,
  `turn:<case_id>:<alias>:<turn_sequence>`, and
  `event:<case_id>:<alias>:<turn_sequence>:<input_revision>`;
- for case ordinal `cc`, session ordinal `ss`, zero-padded three-digit turn
  `ttt`, two-digit revision `rr`, and three-digit atom index `aaa`, the default
  reference is
  `evidence:uuid:00000000-0000-4000-8000-<cc><ss><ttt><rr><aaa>`;
- the default independence key is
  `ind:<case_id>:<alias>:<turn_sequence>:<input_revision>:<atom_index>`;
- atoms are `U`, `T`, `D`, `A`, and `W` for, respectively,
  `unsolicited_explicit_statement`, `transcript_meaning`,
  `dialogue_context`, `synthetic_acoustic_symbol`, and
  `weak_behavioral_proxy`; their modalities are fixed by
  `allowed_modalities_by_evidence_class`;
- an atom is `<kind>(<signal>,<+|->,<H|M|L|X>)`, where directions are
  `supports`/`opposes` and qualities are `high`/`medium`/`low`/`unusable`;
- `[]` is an empty frame. Atom order in every stored base frame is the exact
  policy sort order;
- `{ref=@A.0r0.0}` or `{key=@A.0r0.0}` reuses that atom's default identity;
  frame-level `{event=@A.0r0}`, `{campaign_id=<opaque-id>}`, and
  `{campaign_version=<opaque-version>}` are the only identity overrides;
- an attempt `A<-A.0r0/none` advances state `A` with that frame. Source and
  state aliases differ only in the deliberate cross-session rejection.
  The other suffixes are `/reverse_atom_order` and
  `/add_forbidden_field:<exact-field>`;
- attempts are executed left-to-right and expected steps are positionally
  aligned one-for-one.

These are the exact 30 frame and attempt recipes:

| # | Case | Frames | Ordered attempts |
| --- | --- | --- | --- |
| 01 | `explicit_confusion_entry` | `A.0r0[U(confusion,+,H)]` | `A<-A.0r0/none` |
| 02 | `explicit_disengagement_entry` | `A.0r0[U(disengagement,+,H)]` | `A<-A.0r0/none` |
| 03 | `explicit_frustration_entry` | `A.0r0[U(frustration,+,H)]` | `A<-A.0r0/none` |
| 04 | `explicit_hesitation_entry` | `A.0r0[U(hesitation,+,H)]` | `A<-A.0r0/none` |
| 05 | `explicit_interest_entry` | `A.0r0[U(interest,+,H)]` | `A<-A.0r0/none` |
| 06 | `transcript_three_turn_entry` | `A.0r0[T(confusion,+,H)]; A.1r0[T(confusion,+,H)]; A.2r0[T(confusion,+,H)]` | `A<-A.0r0/none; A<-A.1r0/none; A<-A.2r0/none` |
| 07 | `repeated_independence_zero_addition` | `A.0r0[T(interest,+,H)]; A.1r0[T(interest,+,H){key=@A.0r0.0}]` | `A<-A.0r0/none; A<-A.1r0/none` |
| 08 | `duplicate_event_rejected` | `A.0r0[T(confusion,+,H)]; A.1r0[T(confusion,+,H)]{event=@A.0r0}` | `A<-A.0r0/none; A<-A.1r0/none` |
| 09 | `duplicate_reference_rejected` | `A.0r0[T(confusion,+,H)]; A.1r0[T(confusion,+,H){ref=@A.0r0.0}]` | `A<-A.0r0/none; A<-A.1r0/none` |
| 10 | `acoustic_only_capped` | `A.0r0[A(hesitation,+,H)]; A.1r0[A(hesitation,+,H)]; A.2r0[A(hesitation,+,H)]` | `A<-A.0r0/none; A<-A.1r0/none; A<-A.2r0/none` |
| 11 | `multimodal_two_turn_entry` | `A.0r0[T(frustration,+,H),A(frustration,+,H)]; A.1r0[T(frustration,+,H),A(frustration,+,H)]` | `A<-A.0r0/none; A<-A.1r0/none` |
| 12 | `same_signal_contradiction` | `A.0r0[U(confusion,+,H),D(confusion,+,H),D(confusion,-,H)]` | `A<-A.0r0/none` |
| 13 | `low_quality_acoustic_abstains` | `A.0r0[A(hesitation,+,L)]` | `A<-A.0r0/none` |
| 14 | `empty_frame_missing_input` | `A.0r0[]` | `A<-A.0r0/none` |
| 15 | `release_after_two_below_threshold` | `A.0r0[U(frustration,+,H)]; A.1r0[]; A.2r0[]; A.3r0[]; A.4r0[]; A.5r0[]` | `A<-A.0r0/none; A<-A.1r0/none; A<-A.2r0/none; A<-A.3r0/none; A<-A.4r0/none; A<-A.5r0/none` |
| 16 | `switch_after_two_confirmations` | `A.0r0[U(frustration,+,H)]; A.1r0[U(confusion,+,H)]; A.2r0[T(confusion,+,H)]; A.3r0[T(confusion,+,H)]` | `A<-A.0r0/none; A<-A.1r0/none; A<-A.2r0/none; A<-A.3r0/none` |
| 17 | `entry_tie_abstains` | `A.0r0[U(confusion,+,H),U(frustration,+,H)]` | `A<-A.0r0/none` |
| 18 | `incumbent_survives_unqualified_challenger` | `A.0r0[U(frustration,+,H)]; A.1r0[U(confusion,+,H)]; A.2r0[T(confusion,+,H)]; A.3r0[]` | `A<-A.0r0/none; A<-A.1r0/none; A<-A.2r0/none; A<-A.3r0/none` |
| 19 | `latest_turn_correction_replay` | `A.0r0[T(interest,+,H)]; A.0r1[U(interest,+,H)]` | `A<-A.0r0/none; A<-A.0r1/none` |
| 20 | `closed_turn_correction_rejected` | `A.0r0[T(confusion,+,H)]; A.1r0[]; A.0r1[U(confusion,+,H)]` | `A<-A.0r0/none; A<-A.1r0/none; A<-A.0r1/none` |
| 21 | `cross_session_rejected` | `A.0r0[T(confusion,+,H)]; B.0r0[T(confusion,+,H)]` | `A<-A.0r0/none; A<-B.0r0/none` |
| 22 | `cross_campaign_rejected` | `A.0r0[T(confusion,+,H)]; A.1r0[T(confusion,+,H)]{campaign_id=campaign:phase-c0-other}` | `A<-A.0r0/none; A<-A.1r0/none` |
| 23 | `wrong_campaign_version_rejected` | `A.0r0[T(confusion,+,H)]; A.1r0[T(confusion,+,H)]{campaign_version=version:2}` | `A<-A.0r0/none; A<-A.1r0/none` |
| 24 | `noncanonical_atom_order_rejected` | `A.0r0[U(confusion,+,H),U(frustration,+,H)]` | `A<-A.0r0/reverse_atom_order` |
| 25 | `forbidden_phase_b_field_rejected` | `A.0r0[U(confusion,+,H)]` | `A<-A.0r0/add_forbidden_field:acoustic_features; A<-A.0r0/add_forbidden_field:probabilities; A<-A.0r0/add_forbidden_field:model_id; A<-A.0r0/add_forbidden_field:dataset_id` |
| 26 | `simultaneous_sessions_isolated` | `A.0r0[U(confusion,+,H)]; A.1r0[]; B.0r0[U(interest,+,H)]; B.1r0[]` | `A<-A.0r0/none; B<-B.0r0/none; A<-A.1r0/none; B<-B.1r0/none` |
| 27 | `canonical_replay_bytes` | `A.0r0[T(confusion,+,H)]; A.1r0[]; A.2r0[U(confusion,+,H)]` | `A<-A.0r0/none; A<-A.1r0/none; A<-A.2r0/none` |
| 28 | `dialogue_only_low_quality` | `A.0r0[D(hesitation,+,H),W(hesitation,+,X)]` | `A<-A.0r0/none` |
| 29 | `support_saturation` | `A.0r0[U(confusion,+,H),T(confusion,+,H)]` | `A<-A.0r0/none` |
| 30 | `opposition_below_contradiction_threshold` | `A.0r0[U(confusion,+,H),W(confusion,-,H)]` | `A<-A.0r0/none` |

The recipes freeze frames and attempt routing; the scenario JSON additionally
stores every per-attempt `expected_output` and `expected_internal` value. Task
3 hand-calculates those values from the frozen policy and this table, and the
independent Task 3 review checks every value before reducer code is created.

The numeric golden projections are:

| Scenario | Exact projection |
| --- | --- |
| `explicit_*_entry` | One high unsolicited explicit statement produces capped net `700`, immediate internal/emitted selection, `text_only`, and `insufficient_history`. |
| `transcript_three_turn_entry` | Confusion net sequence `450,810,1000`; entry confirmations `0,1,2`; selection occurs only on turn 3. |
| `repeated_independence_zero_addition` | Interest net `450` then `360`; turn 2 has a fresh reference, repeated independence key, normal decay, zero addition, and no contributing provenance for the new reference. |
| `duplicate_event_rejected` | Second use of the same event ID rejects with `duplicate_event`; state bytes equal pre-call bytes. |
| `duplicate_reference_rejected` | A new event reusing an accepted evidence reference rejects with `duplicate_evidence_reference`; state bytes remain identical. |
| `acoustic_only_capped` | Hesitation net `180,324,400`; every output abstains; turns 2-3 expose `possible_hesitation`; acoustic-only allowed effects equal `["preserve"]`. |
| `multimodal_two_turn_entry` | Frustration net `730,1000`; confirmations `1,2`; turn 2 selects frustration. |
| `same_signal_contradiction` | Gross confusion support/opposition `1000/300`; uncapped net `700`; capped net `350`; output abstains with `contradictory_evidence` and `possible_confusion`. |
| `low_quality_acoustic_abstains` | Low acoustic symbol yields `72`, `low_quality`, `low_audio_quality`, selected `none`, preserve only. |
| `empty_frame_missing_input` | Empty frame yields zero support, `missing_input`, selected `none`, preserve only. |
| `release_after_two_below_threshold` | Internal frustration net `700,560,448,358,286,228`; below-release streak `0,0,0,0,1,2`; incumbent releases on turn 6. Empty turns emit abstention/`none` while the internal incumbent persists through turn 5. |
| `switch_after_two_confirmations` | Frustration/confusion net by turn: `700/0`, `560/700`, `448/1000`, `358/1000`; challenger streak `0,0,1,2`; emitted selection switches on turn 4. |
| `entry_tie_abstains` | High explicit confusion and frustration each yield `700`; no incumbent; output abstains with both possible signals in canonical order. |
| `incumbent_survives_unqualified_challenger` | Frustration/confusion net by turn is `700/0`, `560/700`, `448/1000`, `358/800`. Turn 2 fails the `150` advantage by `10`; turn 3 records one switch key; turn 4 has no new key and clears the switch streak. Frustration remains the internal incumbent throughout and is emitted through turn 3; the empty turn 4 abstains, emits `none`, and clears the switch streak. |
| `latest_turn_correction_replay` | Original interest transcript gives `450` and abstains; revision 1 replaces it with high explicit interest, fresh-fold net `700`, and selects interest. |
| `closed_turn_correction_rejected` | Revision targeting a nonlatest turn rejects with `stale_turn` because stale-sequence precedence matches the read-only runtime parity oracle; bytes unchanged. |
| `cross_session_rejected` | Reject `cross_session`; bytes unchanged. |
| `cross_campaign_rejected` | Reject `cross_campaign`; bytes unchanged. |
| `wrong_campaign_version_rejected` | Reject `wrong_campaign_version`; bytes unchanged. |
| `noncanonical_atom_order_rejected` | Reverse a valid two-atom frame; reject `noncanonical_atom_order`; bytes unchanged. |
| `forbidden_phase_b_field_rejected` | Add `acoustic_features`, `probabilities`, `model_id`, or `dataset_id`; each rejects `forbidden_field`; bytes unchanged. |
| `simultaneous_sessions_isolated` | Golden attempts are the accepted interleaving of confusion and interest sessions and equal separate-fold state/output bytes. A Task 6 metamorphic swap cross-feeds each next frame and must reject `cross_session`. |
| `canonical_replay_bytes` | Two complete folds over the same scenario produce identical session-state and output bytes. |
| `dialogue_only_low_quality` | One high dialogue-context atom plus one unusable dialogue weak-proxy atom yields net `300`; the unusable atom adds zero and is excluded from provenance. Output is `possible_hesitation`, `low_quality`, and insufficient-evidence abstention. |
| `support_saturation` | High explicit plus high transcript support produces gross/capped net `1000`, never `1150`. |
| `opposition_below_contradiction_threshold` | High explicit support `700` plus high weak-proxy opposition `100` yields net `600`, no contradiction, and immediate explicit-statement selection. |

Evidence references use
`evidence:uuid:00000000-0000-4000-8000-<12-digit-counter>`.
Independence keys use
`ind:<case_id>:<alias>:<turn_sequence>:<input_revision>:<atom_index>`, exactly
the zero-based recipe formula above.
Every atom list follows the exact policy sort tuple.

## Exact Type And Test-Harness Map

These types are introduced by the named tasks. Field names and types are
authoritative across every later task.

```python
@dataclass(frozen=True)
class PhaseCSyntheticEvidenceAtomV1:
    schema_version: str
    evidence_ref: str
    independence_key: str
    operational_signal: str
    direction: str
    modality: str
    evidence_class: str
    quality_bucket: str


@dataclass(frozen=True)
class PhaseCSyntheticEvidenceFrameV1:
    schema_version: str
    fixture_only: bool
    call_session_id: str
    campaign_profile_id: str
    campaign_profile_version: str
    turn_id: str
    turn_sequence: int
    event_id: str
    input_revision: int
    evidence_atoms: tuple[PhaseCSyntheticEvidenceAtomV1, ...]


@dataclass(frozen=True)
class PhaseCEventWatermarkV1:
    expected_session_id: str
    expected_campaign_profile_id: str
    expected_campaign_profile_version: str
    last_turn_sequence: int
    turn_sequence_by_id: tuple[tuple[str, int], ...]
    turn_id_by_sequence: tuple[tuple[int, str], ...]
    last_input_revision_by_turn: tuple[tuple[str, int], ...]
    seen_event_ids: frozenset[str]
    event_history_by_id: tuple[tuple[str, str, int], ...]


@dataclass(frozen=True)
class PhaseCExpectedInternalProjectionV1:
    gross_supporting_units: tuple[tuple[str, int], ...]
    gross_opposing_units: tuple[tuple[str, int], ...]
    uncapped_net_support: tuple[tuple[str, int], ...]
    capped_net_support: tuple[tuple[str, int], ...]
    contradictory_signals: tuple[str, ...]
    seen_independence_keys: tuple[str, ...]
    internal_incumbent: str | None
    incumbent_tenure: int
    entry_confirmation_keys_by_signal: tuple[
        tuple[str, tuple[str, ...]],
        ...
    ]
    switch_challenger: str | None
    switch_confirmation_keys: tuple[str, ...]
    release_streak: int
    contributing_evidence_refs: tuple[str, ...]
    seen_evidence_refs: tuple[str, ...]
    retired_independence_keys: tuple[str, ...]
    accepted_turn_count: int
    last_emitted_selected_signal: str | None
    last_emitted_selected_support: int | None


@dataclass(frozen=True)
class PhaseCExpectedAcceptedStepV1:
    disposition: str
    expected_output_bytes: bytes
    expected_internal: PhaseCExpectedInternalProjectionV1


@dataclass(frozen=True)
class PhaseCExpectedRejectedStepV1:
    disposition: str
    rejection_code: str
    prior_state_bytes_unchanged: bool


@dataclass(frozen=True)
class PhaseCScenarioSessionV1:
    session_alias: str
    frames: tuple[PhaseCSyntheticEvidenceFrameV1, ...]


@dataclass(frozen=True)
class PhaseCScenarioAttemptV1:
    state_session_alias: str
    frame_session_alias: str
    frame_index: int
    mutation_kind: str
    mutation_parameter: str | None


@dataclass(frozen=True)
class PhaseCScenarioV1:
    case_id: str
    family: str
    signal_family: str
    modality_family: str
    sessions: tuple[PhaseCScenarioSessionV1, ...]
    attempt_order: tuple[PhaseCScenarioAttemptV1, ...]
    expected_steps: tuple[
        PhaseCExpectedAcceptedStepV1 | PhaseCExpectedRejectedStepV1,
        ...
    ]


@dataclass(frozen=True)
class PhaseCSignalAccumulatorV1:
    gross_supporting_units: tuple[tuple[str, int], ...]
    gross_opposing_units: tuple[tuple[str, int], ...]
    uncapped_net_support: tuple[tuple[str, int], ...]
    capped_net_support: tuple[tuple[str, int], ...]
    highest_quality_by_signal_direction: tuple[
        tuple[str, tuple[tuple[str, str | None], ...]],
        ...
    ]
    contradictory_signals: tuple[str, ...]
    modality_refs_by_signal_direction: tuple[
        tuple[
            str,
            tuple[
                tuple[
                    str,
                    tuple[tuple[str, tuple[str, ...]], ...],
                ],
                ...
            ],
        ],
        ...
    ]


@dataclass(frozen=True)
class PhaseCFrameFoldV1:
    accumulator: PhaseCSignalAccumulatorV1
    accepted_evidence_refs: tuple[str, ...]
    contributing_evidence_refs: tuple[str, ...]
    accepted_independence_keys: tuple[str, ...]
    confirming_keys_by_signal: tuple[tuple[str, tuple[str, ...]], ...]
    acoustic_only: bool
    missing_input: bool
    low_audio_quality_only: bool


@dataclass(frozen=True)
class PhaseCProjectionContextV1:
    prior_emitted_selected_signal: str | None
    prior_emitted_selected_support: int | None
    fold: PhaseCFrameFoldV1
    frame: PhaseCSyntheticEvidenceFrameV1


@dataclass(frozen=True)
class PhaseCHysteresisV1:
    internal_incumbent: str | None
    incumbent_tenure: int
    entry_confirmation_keys_by_signal: tuple[
        tuple[str, tuple[str, ...]],
        ...
    ]
    switch_challenger: str | None
    switch_confirmation_keys: tuple[str, ...]
    release_streak: int


@dataclass(frozen=True)
class PhaseCTemporalSessionStateV1:
    schema_version: str
    policy_id: str
    policy_sha256: str
    call_session_id: str
    campaign_profile_id: str
    campaign_profile_version: str
    watermark: PhaseCEventWatermarkV1
    accepted_frames: tuple[PhaseCSyntheticEvidenceFrameV1, ...]
    evidence_history_by_event: tuple[
        tuple[str, tuple[str, ...], tuple[str, ...]],
        ...
    ]
    accumulator: PhaseCSignalAccumulatorV1
    hysteresis: PhaseCHysteresisV1
    seen_evidence_refs: tuple[str, ...]
    seen_independence_keys: tuple[str, ...]
    retired_independence_keys: tuple[str, ...]
    contributing_evidence_refs: tuple[str, ...]
    accepted_turn_count: int
    last_emitted_selected_signal: str | None
    last_emitted_selected_support: int | None


@dataclass(frozen=True)
class PhaseCReplayV1:
    final_state: PhaseCTemporalSessionStateV1
    states: tuple[PhaseCTemporalSessionStateV1, ...]
    outputs: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class PhaseCScenarioOutcomeV1:
    case_id: str
    family: str
    signal_family: str
    modality_family: str
    passed: bool
    failed_invariants: tuple[str, ...]
    rejection_count: int
    abstention_reason_counts: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class PhaseCScenarioEvaluationV1:
    total_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    outcomes: tuple[PhaseCScenarioOutcomeV1, ...]
    counts_by_family: tuple[tuple[str, int], ...]
    counts_by_signal: tuple[tuple[str, int], ...]
    counts_by_modality: tuple[tuple[str, int], ...]
    counts_by_abstention_reason: tuple[tuple[str, int], ...]
    invariant_counts: tuple[tuple[str, int], ...]
    deterministic_replay_passed: bool
    privacy_boundary_passed: bool
```

The shared test module defines this base after Task 3:

```python
class PhaseCTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw_policy = load_json_strict(POLICY_PATH)
        cls.policy = validate_phase_c_policy(cls.raw_policy)
        cls.raw_scenarios = load_json_strict(SCENARIO_PATH)
        cls.scenarios = load_and_validate_phase_c_scenarios(
            SCENARIO_PATH,
            cls.policy,
        )
        cls.scenario_by_id = {
            scenario.case_id: scenario for scenario in cls.scenarios
        }

    def case(self, case_id: str) -> PhaseCScenarioV1:
        return self.scenario_by_id[case_id]
```

Tracker test classes introduced from Task 4 onward inherit
`PhaseCTestCase`. Each such class sets:

```python
@classmethod
def setUpClass(cls) -> None:
    super().setUpClass()
    from scripts import emotion_state_phase_c_temporal_tracker

    cls.tracker = emotion_state_phase_c_temporal_tracker
```

---

### Task 1: Freeze The Protocol And Exact Policy Contract

**Files:**
- Create: `.gitattributes`
- Create:
  `research/experiments/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics.md`
- Create:
  `research/experiments/cases/emotion-state-003-phase-c0-policy.json`
- Create: `scripts/emotion_state_phase_c_contracts.py`
- Create: `scripts/test_emotion_state_003_phase_c0.py`

**Interfaces:**
- Consumes: the approved design and Frozen Policy Authority in this plan.
- Produces:
  `PhaseCContractError`,
  `canonical_json_bytes(payload: Any) -> bytes`,
  `sha256_bytes(payload: bytes) -> str`,
  `load_json_strict(path: Path) -> dict[str, Any]`, and
  `validate_phase_c_policy(payload: dict[str, Any]) -> dict[str, Any]`.

- [ ] **Step 1: Write the failing exact-policy tests**

Create the test module with imports that do not yet exist:

```python
from __future__ import annotations

import copy
import dataclasses
import inspect
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

from scripts.emotion_state_phase_c_contracts import (
    PhaseCContractError,
    canonical_json_bytes,
    load_json_strict,
    sha256_bytes,
    validate_phase_c_policy,
)

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = (
    ROOT
    / "research"
    / "experiments"
    / "cases"
    / "emotion-state-003-phase-c0-policy.json"
)


class PhaseCPolicyContractTests(unittest.TestCase):
    def test_frozen_policy_is_exact_and_canonical(self) -> None:
        payload = load_json_strict(POLICY_PATH)
        validated = validate_phase_c_policy(payload)
        self.assertEqual(validated["policy_id"], "emotion-state-phase-c0-synthetic-v1")
        self.assertEqual(validated["evidence_policy_version"], "emotion-state-evidence-v2")
        self.assertEqual(validated["base_support_units"]["unsolicited_explicit_statement"], 700)
        self.assertEqual(validated["contradiction_cap"], 350)
        self.assertEqual(validated["acoustic_only_cap"], 400)
        canonical = canonical_json_bytes(validated)
        self.assertEqual(
            json.loads(canonical.decode("utf-8")),
            json.loads(POLICY_PATH.read_text(encoding="utf-8")),
        )
        self.assertRegex(sha256_bytes(canonical), r"^[0-9A-F]{64}$")

    def test_every_top_level_policy_mutation_fails_closed(self) -> None:
        payload = load_json_strict(POLICY_PATH)
        for key in tuple(payload):
            mutated = copy.deepcopy(payload)
            mutated.pop(key)
            with self.subTest(missing=key):
                with self.assertRaises(PhaseCContractError):
                    validate_phase_c_policy(mutated)
        extra = copy.deepcopy(payload)
        extra["future"] = True
        with self.assertRaises(PhaseCContractError):
            validate_phase_c_policy(extra)

    def test_every_policy_leaf_mutation_fails_closed(self) -> None:
        payload = load_json_strict(POLICY_PATH)
        for name, mutated in build_policy_leaf_mutations(payload):
            with self.subTest(mutation=name):
                with self.assertRaises(PhaseCContractError):
                    validate_phase_c_policy(mutated)

    def test_nonfinite_and_bool_numeric_values_fail_closed(self) -> None:
        payload = load_json_strict(POLICY_PATH)
        for invalid in (True, float("nan"), float("inf"), -1):
            mutated = copy.deepcopy(payload)
            mutated["entry_threshold"] = invalid
            with self.subTest(invalid=repr(invalid)):
                with self.assertRaises(PhaseCContractError):
                    validate_phase_c_policy(mutated)

    def test_exact_output_eol_attributes_are_narrow(self) -> None:
        self.assertEqual(
            (ROOT / ".gitattributes").read_text(
                encoding="utf-8",
            ).splitlines(),
            [
                "/research/experiments/generated/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics/result.json text eol=lf",
                "/research/experiments/generated/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics/report.md text eol=lf",
            ],
        )
```

`build_policy_leaf_mutations` walks every dictionary/list leaf in deterministic
path order, changes exactly one value (`bool` flips, `int` adds one, and
`str` appends `-mutated`), and never imports the production policy constant.

- [ ] **Step 2: Run RED**

Run:

```powershell
python -m unittest scripts.test_emotion_state_003_phase_c0.PhaseCPolicyContractTests -v
```

Expected: import failure for
`scripts.emotion_state_phase_c_contracts`.

- [ ] **Step 3: Add the strict loader and exact policy validator**

Implement these foundations:

```python
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any


class PhaseCContractError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def canonical_json_bytes(payload: Any) -> bytes:
    try:
        text = json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise PhaseCContractError("payload is not canonical JSON") from exc
    return (text + "\n").encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def _reject_constant(value: str) -> None:
    raise PhaseCContractError(f"non-finite JSON constant is forbidden: {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PhaseCContractError(f"duplicate_json_key:{key}")
        result[key] = value
    return result


def load_json_strict(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=_reject_constant,
            object_pairs_hook=_unique_object,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PhaseCContractError(f"invalid JSON: {path.name}") from exc
    if type(value) is not dict:
        raise PhaseCContractError("top-level JSON value must be an object")
    return value
```

Define the authority as one immutable
`FROZEN_POLICY_CANONICAL_JSON: Final[str]` constant; do not store a module-level
nested dictionary/list or load a file at import time. The validator parses a
fresh expected object from that string and compares field sets, types, array
order, mapping keys, and every scalar against the Frozen Policy Authority
above. Numeric validation must use `type(value) is int`, never `isinstance`,
so booleans fail.

- [ ] **Step 4: Add the protocol and exact canonical policy JSON**

Create `.gitattributes` with exactly:

```gitattributes
/research/experiments/generated/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics/result.json text eol=lf
/research/experiments/generated/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics/report.md text eol=lf
```

Reject any wildcard or additional attribute line in the focused test.

The protocol document must state:

```markdown
## Status

Task 1 policy-contract implementation complete. Reducer implementation
pending. No candidate, canonical, push, runtime, provider, data, call, or
Phase D gate is open.

## Question

Can a frozen, fixed-point, pure reducer reproduce the approved synthetic
temporal mechanics and fail-closed invariants deterministically?

## Claim Boundary

This tests synthetic mechanics only. It does not test emotion accuracy,
customer internal state, policy enforcement, sales effectiveness, real-call
behavior, or production readiness.
```

Write the policy JSON exactly as the Frozen Policy Authority. Generate no
policy value from tests or reducer output.

- [ ] **Step 5: Run GREEN and repository checks**

Run:

```powershell
python -m unittest scripts.test_emotion_state_003_phase_c0.PhaseCPolicyContractTests -v
python -m py_compile scripts/emotion_state_phase_c_contracts.py scripts/test_emotion_state_003_phase_c0.py
python scripts/check_thesis_reference_registry.py
python scripts/validate_project_drift_guard.py
python scripts/validate_context_reading_policy.py
python scripts/validate_check_setup.py
git check-attr text eol -- research/experiments/generated/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics/result.json research/experiments/generated/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics/report.md
git diff --check
```

Then run the exact common post-GREEN ledger. Expected: all commands exit `0`;
five policy/attribute tests pass.

- [ ] **Step 6: Independently review and commit**

Review must verify no reducer function exists and the policy bytes are frozen
before scenario or reducer work.

```powershell
git add -- .gitattributes research/experiments/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics.md research/experiments/cases/emotion-state-003-phase-c0-policy.json scripts/emotion_state_phase_c_contracts.py scripts/test_emotion_state_003_phase_c0.py
git diff --cached --check
git commit -m "Freeze Phase C0 synthetic policy contract"
```

### Task 2: Implement Synthetic Input And Event-Identity Contracts

**Files:**
- Modify: `scripts/emotion_state_phase_c_contracts.py`
- Modify: `scripts/test_emotion_state_003_phase_c0.py`

**Interfaces:**
- Consumes: `validate_phase_c_policy`.
- Produces:
  `PhaseCEventRejected(PhaseCContractError)`,
  `PhaseCSyntheticEvidenceAtomV1`,
  `PhaseCSyntheticEvidenceFrameV1`,
  `PhaseCEventWatermarkV1`,
  `parse_phase_c_atom(payload, policy)`,
  `validate_phase_c_atom(atom, policy)`,
  `parse_phase_c_frame(payload, policy)`,
  `validate_phase_c_frame(frame, policy)`,
  `phase_c_frame_to_payload(frame)`,
  `atom_sort_key(atom, policy)`,
  `initial_phase_c_watermark(frame)`, and
  `validate_phase_c_event_watermark(watermark)`, and
  `validate_phase_c_event_identity(frame, watermark)`.

- [ ] **Step 1: Write failing atom/frame tests**

Add helpers and focused tests:

```python
def _atom(
    *,
    counter: int,
    signal: str = "confusion",
    direction: str = "supports",
    modality: str = "text",
    evidence_class: str = "transcript_meaning",
    quality: str = "high",
    independence_key: str | None = None,
) -> dict[str, object]:
    return {
        "schema_version": "PhaseCSyntheticEvidenceAtomV1",
        "evidence_ref": (
            "evidence:uuid:00000000-0000-4000-8000-"
            f"{counter:012d}"
        ),
        "independence_key": independence_key or f"ind:fixture:1:{counter}",
        "operational_signal": signal,
        "direction": direction,
        "modality": modality,
        "evidence_class": evidence_class,
        "quality_bucket": quality,
    }


def _frame(
    *,
    event_id: str = "event-1",
    turn_id: str = "turn-1",
    turn_sequence: int = 0,
    input_revision: int = 0,
    atoms: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": "PhaseCSyntheticEvidenceFrameV1",
        "fixture_only": True,
        "call_session_id": "session-a",
        "campaign_profile_id": "campaign-a",
        "campaign_profile_version": "campaign-v1",
        "turn_id": turn_id,
        "turn_sequence": turn_sequence,
        "event_id": event_id,
        "input_revision": input_revision,
        "evidence_atoms": atoms or [],
    }


class PhaseCInputContractTests(unittest.TestCase):
    def test_valid_frame_parses_to_immutable_types(self) -> None:
        policy = validate_phase_c_policy(load_json_strict(POLICY_PATH))
        frame = parse_phase_c_frame(_frame(atoms=[_atom(counter=1)]), policy)
        self.assertEqual(frame.turn_sequence, 0)
        self.assertIsInstance(frame.evidence_atoms, tuple)
        self.assertEqual(frame.evidence_atoms[0].operational_signal, "confusion")

    def test_raw_phase_b_surfaces_and_unknown_fields_reject(self) -> None:
        policy = validate_phase_c_policy(load_json_strict(POLICY_PATH))
        for key in ("acoustic_features", "probabilities", "model_id", "dataset_id"):
            payload = _frame(atoms=[_atom(counter=1)])
            payload[key] = {}
            with self.subTest(key=key):
                with self.assertRaisesRegex(PhaseCContractError, "forbidden_field"):
                    parse_phase_c_frame(payload, policy)

    def test_noncanonical_atom_order_rejects(self) -> None:
        policy = validate_phase_c_policy(load_json_strict(POLICY_PATH))
        atoms = [
            _atom(counter=1, signal="confusion"),
            _atom(counter=2, signal="interest"),
        ]
        with self.assertRaisesRegex(PhaseCContractError, "noncanonical_atom_order"):
            parse_phase_c_frame(_frame(atoms=list(reversed(atoms))), policy)
```

Before RED, also add stable-order atom/frame mutation tests for every
missing/extra field, wrong exact type (including bool-for-int), unknown enum,
malformed reference, forbidden key fragment at every nesting depth, duplicate
reference, duplicate independence key within one frame, invalid
evidence-class/modality pairing, noncanonical atom order,
`fixture_only=False`, negative sequence/revision, and
dataclass-to-payload round-trip. The mutation builder is test-owned and does
not import production field sets.

- [ ] **Step 2: Run RED**

```powershell
python -m unittest scripts.test_emotion_state_003_phase_c0.PhaseCInputContractTests -v
```

Expected: import/name failures for the new dataclasses and parsers.

- [ ] **Step 3: Implement immutable input types and exact parsing**

Use frozen dataclasses:

```python
@dataclass(frozen=True)
class PhaseCSyntheticEvidenceAtomV1:
    schema_version: str
    evidence_ref: str
    independence_key: str
    operational_signal: str
    direction: str
    modality: str
    evidence_class: str
    quality_bucket: str


@dataclass(frozen=True)
class PhaseCSyntheticEvidenceFrameV1:
    schema_version: str
    fixture_only: bool
    call_session_id: str
    campaign_profile_id: str
    campaign_profile_version: str
    turn_id: str
    turn_sequence: int
    event_id: str
    input_revision: int
    evidence_atoms: tuple[PhaseCSyntheticEvidenceAtomV1, ...]


@dataclass(frozen=True)
class PhaseCEventWatermarkV1:
    expected_session_id: str
    expected_campaign_profile_id: str
    expected_campaign_profile_version: str
    last_turn_sequence: int
    turn_sequence_by_id: tuple[tuple[str, int], ...]
    turn_id_by_sequence: tuple[tuple[int, str], ...]
    last_input_revision_by_turn: tuple[tuple[str, int], ...]
    seen_event_ids: frozenset[str]
    event_history_by_id: tuple[tuple[str, str, int], ...]
```

Use these exact parser authorities:

```python
ATOM_FIELDS = frozenset({
    "schema_version", "evidence_ref", "independence_key",
    "operational_signal", "direction", "modality", "evidence_class",
    "quality_bucket",
})
FRAME_FIELDS = frozenset({
    "schema_version", "fixture_only", "call_session_id",
    "campaign_profile_id", "campaign_profile_version", "turn_id",
    "turn_sequence", "event_id", "input_revision", "evidence_atoms",
})
OPAQUE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,159}$")
EVIDENCE_REF_PATTERN = re.compile(
    r"^evidence:uuid:[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
FORBIDDEN_PHASE_C_KEY_FRAGMENTS = (
    "acoustic_features", "probabilities", "model_id", "dataset_id",
    "audio_bytes", "raw_audio", "transcript_text", "raw_transcript",
    "customer_name", "customer_phone", "customer_email",
    "speaker_embedding", "voiceprint", "provider_payload", "api_key",
    "access_token", "auth_token", "password", "secret", "private_key",
    "hidden_reasoning",
)
CLASS_MODALITY = MappingProxyType({
    "unsolicited_explicit_statement": "text",
    "transcript_meaning": "text",
    "dialogue_context": "dialogue",
    "synthetic_acoustic_symbol": "acoustic",
    "weak_behavioral_proxy": "dialogue",
})
```

The recursive forbidden scanner visits mapping keys in insertion order and
list elements by index. It lowercases each key and raises
`PhaseCContractError("forbidden_field")` on the first fragment match before
missing/unknown-field checks. Parser error precedence after that is:

| Condition | Exact code |
| --- | --- |
| non-dict atom/frame | `atom_not_object` / `frame_not_object` |
| missing field | `atom_missing_fields` / `frame_missing_fields` |
| unknown field | `atom_unknown_fields` / `frame_unknown_fields` |
| wrong schema | `atom_schema` / `frame_schema` |
| `fixture_only is not True` | `fixture_only_required` |
| wrong exact scalar/container type | `atom_field_type` / `frame_field_type` |
| malformed evidence reference | `invalid_evidence_reference` |
| malformed opaque identifier/key | `invalid_opaque_identifier` |
| unknown signal/direction/modality/class/quality | `unknown_atom_enum` |
| class/modality mismatch | `class_modality_mismatch` |
| duplicate reference in one frame | `duplicate_evidence_reference` |
| duplicate independence key in one frame | `duplicate_independence_key` |
| noncanonical atom order | `noncanonical_atom_order` |
| negative sequence or revision | `invalid_event_counter` |

`parse_phase_c_atom` performs those checks in table order, constructs the
frozen atom, and calls `validate_phase_c_atom`. `parse_phase_c_frame` performs
the frame checks, parses atoms in their supplied order, rejects duplicate
references/keys, and compares the atom tuple to `sorted(atoms,
key=atom_sort_key)` without reordering it. `atom_sort_key` is exactly:

```python
(
    signal_order.index(atom.operational_signal),
    direction_order.index(atom.direction),
    modality_order.index(atom.modality),
    evidence_class_order.index(atom.evidence_class),
    quality_order.index(atom.quality_bucket),
    atom.independence_key,
    atom.evidence_ref,
)
```

`validate_phase_c_atom` and `validate_phase_c_frame` serialize the frozen
dataclass to fresh mappings and route through the same private scalar checks;
they never call the public parser recursively. `phase_c_frame_to_payload`
creates a new dict/list tree in exact field-list order and proves
`parse_phase_c_frame(result, policy) == frame` before returning it.
`validate_phase_c_frame` revalidates an already constructed frozen dataclass so
direct dataclass construction cannot bypass the parser. `phase_c_frame_to_payload`
returns a fresh JSON-compatible mapping and round-trips through
`parse_phase_c_frame` byte-equivalently.
`initial_phase_c_watermark(frame)` copies only the expected
session/campaign/version identities and initializes `last_turn_sequence=-1`,
all tuple maps empty, `seen_event_ids=frozenset()`, and
`event_history_by_id=()`. The first frame still passes through
`validate_phase_c_event_identity`.

- [ ] **Step 4: Write failing event-identity and parity tests**

Test these exact rejection codes:

```python
EXPECTED_IDENTITY_REJECTIONS = (
    "cross_session",
    "cross_campaign",
    "wrong_campaign_version",
    "duplicate_event",
    "turn_id_rebound",
    "turn_sequence_rebound",
    "stale_turn",
    "invalid_revision",
)
```

Create `_runtime_identity_projection(frame)` with this complete mapping:

```python
{
    "call_session_id": frame.call_session_id,
    "campaign_profile_id": frame.campaign_profile_id,
    "campaign_profile_version": frame.campaign_profile_version,
    "turn_id": frame.turn_id,
    "turn_sequence": frame.turn_sequence,
    "event_id": frame.event_id,
    "input_revision": frame.input_revision,
    "event_timestamp": "2026-07-24T00:00:00Z",
    "call_scoped_speaker_id": f"{frame.call_session_id}:speaker",
    "start_time_ms": frame.turn_sequence * 1000,
    "end_time_ms": (frame.turn_sequence + 1) * 1000,
    "audio_quality_status": "unavailable",
    "audio_quality_reasons": ["phase_a_no_audio"],
    "acoustic_features": {},
    "acoustic_feature_confidence": {},
    "transcript_signals": [],
    "explicit_customer_statements": [],
    "dialogue_context_refs": [],
    "speaker_baseline_status": "not_started",
    "extraction_status": "offline_fixture_only",
    "source_timestamps": {},
    "persistence_allowed": False,
}
```

This helper exists only in tests. Feed identical
identity sequences to Phase C0 and existing `validate_event_identity`; assert
both accept the same new-turn/correction sequence and reject each corresponding
identity mutation. Compare all watermark maps, including
`event_history_by_id`, after every accepted event.

Run the focused identity class before adding identity-validation behavior:

```powershell
python -m unittest scripts.test_emotion_state_003_phase_c0.PhaseCEventIdentityTests -v
```

Expected: nonzero because the new event-identity validator and watermark
self-consistency behavior are not implemented. Record the intended failure
caused by missing behavior; stop if the failure instead comes from fixture,
syntax, or unrelated contract code.

- [ ] **Step 5: Implement identity validation and run GREEN**

`validate_phase_c_event_identity` first calls the independent watermark
self-consistency validator. That validator requires the frozen watermark
type; unique tuple-map keys; exact inverse turn maps; nonnegative integer
sequences/revisions; `last_turn_sequence == max(turn sequences, default=-1)`;
event-history IDs exactly equal `seen_event_ids`; one event per
`(turn_id, revision)`; contiguous revisions `0..last_revision` for every
known turn; and matching coverage across turn, revision, and event maps.

After copying tuple maps to new dicts, event validation runs in this exact
order and raises the listed `PhaseCEventRejected` code:

```python
if frame.call_session_id != watermark.expected_session_id:
    reject("cross_session")
if frame.campaign_profile_id != watermark.expected_campaign_profile_id:
    reject("cross_campaign")
if frame.campaign_profile_version != watermark.expected_campaign_profile_version:
    reject("wrong_campaign_version")
if frame.event_id in watermark.seen_event_ids:
    reject("duplicate_event")
if known_turn_id_has_other_sequence:
    reject("turn_id_rebound")
if known_sequence_has_other_turn_id:
    reject("turn_sequence_rebound")
if frame.turn_sequence < watermark.last_turn_sequence:
    reject("stale_turn")
if frame.turn_id in sequence_by_id:
    if frame.input_revision != revision_by_turn[frame.turn_id] + 1:
        reject("invalid_revision")
else:
    if frame.turn_sequence <= watermark.last_turn_sequence:
        reject("stale_turn")
    if frame.input_revision != 0:
        reject("invalid_revision")
    add_turn_maps()
set_latest_revision()
append_event_history()
return_new_sorted_watermark()
```

`append_event_history` inserts `(event_id, turn_id, input_revision)` and the
returned watermark sorts all tuple maps lexically/numerically exactly as their
tuple key dictates. The function never mutates its input and never calls the
existing runtime identity validator. Policy, atom, frame, and watermark-shape
failures remain plain `PhaseCContractError`.

```powershell
python -m unittest scripts.test_emotion_state_003_phase_c0.PhaseCInputContractTests -v
python -m unittest scripts.test_emotion_state_003_phase_c0.PhaseCEventIdentityTests -v
python scripts/validate_emotion_state_001_phase_a_contracts.py --section contracts
python -m py_compile scripts/emotion_state_phase_c_contracts.py scripts/test_emotion_state_003_phase_c0.py
git diff --check
```

Then run the exact common post-GREEN ledger. Expected: all focused and
existing contract tests pass.

- [ ] **Step 6: Independently review and commit**

The reviewer must prove production code calls only the Phase C0 identity
validator and runtime identity is used only by parity tests.

```powershell
git add -- scripts/emotion_state_phase_c_contracts.py scripts/test_emotion_state_003_phase_c0.py
git diff --cached --check
git commit -m "Add Phase C0 synthetic input contracts"
```

### Task 3: Freeze The Complete Scenario Matrix Before Reducer Code

**Files:**
- Create:
  `research/experiments/cases/emotion-state-003-phase-c0-scenarios.json`
- Modify: `scripts/emotion_state_phase_c_contracts.py`
- Modify: `scripts/test_emotion_state_003_phase_c0.py`
- Modify:
  `research/experiments/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics.md`

**Interfaces:**
- Consumes: policy and frame parsers.
- Produces:
  `PhaseCScenarioV1`,
  `PhaseCExpectedAcceptedStepV1`,
  `PhaseCExpectedRejectedStepV1`,
  `validate_phase_c_scenario_payload(payload, policy)`,
  `load_and_validate_phase_c_scenarios(path, policy)`,
  `materialize_phase_c_scenario_attempt_payload(scenario, attempt)`, and the
  exact 30-case frozen matrix.

- [ ] **Step 1: Write failing scenario-contract tests**

```python
SCENARIO_PATH = (
    ROOT
    / "research"
    / "experiments"
    / "cases"
    / "emotion-state-003-phase-c0-scenarios.json"
)


class PhaseCScenarioContractTests(unittest.TestCase):
    def test_scenario_ids_order_and_count_are_frozen(self) -> None:
        policy = validate_phase_c_policy(load_json_strict(POLICY_PATH))
        scenarios = load_and_validate_phase_c_scenarios(SCENARIO_PATH, policy)
        self.assertEqual(tuple(item.case_id for item in scenarios), EXPECTED_SCENARIO_IDS)
        self.assertEqual(len(scenarios), 30)
        self.assertEqual(
            {
                item.case_id: (
                    item.family,
                    item.signal_family,
                    item.modality_family,
                )
                for item in scenarios
            },
            EXPECTED_SCENARIO_CLASSIFICATIONS,
        )

    def test_forbidden_surfaces_exist_only_as_negative_mutation_parameters(self) -> None:
        raw = load_json_strict(SCENARIO_PATH)
        allowed = {
            "acoustic_features",
            "probabilities",
            "model_id",
            "dataset_id",
        }
        observed = []
        for scenario in raw["scenarios"]:
            serialized_frames = canonical_json_bytes(
                {"sessions": scenario["sessions"]}
            ).decode("utf-8").lower()
            for forbidden in allowed | {
                "audio_bytes",
                "transcript_text",
                "customer_name",
            }:
                self.assertNotIn(forbidden, serialized_frames)
            for attempt in scenario["attempt_order"]:
                if attempt["mutation_kind"] == "add_forbidden_field":
                    observed.append(attempt["mutation_parameter"])
        self.assertEqual(set(observed), allowed)

    def test_scenario_canonical_identity_is_checkout_eol_independent(self) -> None:
        payload = load_json_strict(SCENARIO_PATH)
        canonical = canonical_json_bytes(payload)
        self.assertEqual(
            json.loads(canonical.decode("utf-8")),
            json.loads(SCENARIO_PATH.read_text(encoding="utf-8")),
        )
```

- [ ] **Step 2: Run RED**

```powershell
python -m unittest scripts.test_emotion_state_003_phase_c0.PhaseCScenarioContractTests -v
```

Expected: missing scenario file and loader failures.

- [ ] **Step 3: Implement exact scenario/expectation contracts**

Use frozen dataclasses. Accepted expectations require every field shown in the
Frozen Scenario Authority. Rejected expectations require exactly
`disposition`, `rejection_code`, and `prior_state_bytes_unchanged`.

The loader must:

- require root schema `PhaseCScenarioMatrixV1`;
- require policy ID `emotion-state-phase-c0-synthetic-v1`;
- require exactly the 30 ordered IDs;
- require every exact family/signal/modality classification above;
- parse every stored base frame through `parse_phase_c_frame`;
- require unique session aliases and case IDs;
- require aliases to be exactly `A`, or `A`,`B`, in that order, and require
  every attempt's state/frame alias to exist;
- require expected-step count equal attempted-frame count;
- validate every attempt index and exact mutation descriptor;
- canonicalize every accepted expectation's exact 22-field output object to
  `expected_output_bytes`, validate it with the existing
  `validate_perceived_customer_state`, and require `runtime_approved=false`
  plus all three estimates equal `not_inferable`;
- require every accepted `expected_internal` object to have exactly the 18
  fields in the Frozen Scenario Authority, dense canonical signal maps, exact
  scalar types, canonical references/keys, and no unknown field;
- allow the four forbidden field names only as
  `add_forbidden_field` negative-test parameters paired with an expected
  `forbidden_field` rejection;
- require `reverse_atom_order` to be paired with an expected
  `noncanonical_atom_order` rejection;
- reject forbidden fields recursively in all stored base frames; and
- hash and compare the canonical serialization of the strictly parsed JSON
  object, never the checkout's raw line-ending-dependent bytes.

- [ ] **Step 4: Hand-author the complete matrix**

Expand every row from the exact fixture-recipe table mechanically. Store only
valid base frames; encode parser-negative inputs with the exact attempt
mutation descriptors above. Hand-calculate and store the complete output and
internal projection for every accepted attempt from the frozen policy. Do not
use a script, reducer, renderer, or production helper to generate an expected
value. `materialize_phase_c_scenario_attempt_payload` deep-copies
`phase_c_frame_to_payload(base_frame)`, applies only the allowlisted mutation,
and returns the candidate mapping for normal parsing. It never reads the
expected step. Do not import or call tracker code; it does not yet exist.

Add a focused test that expands each stored frame back to the recipe token
sequence and proves exact equality to all 30 table rows. Add another test that
iterates every accepted step and proves its output field set equals
`PERCEIVED_STATE_FIELDS`, its internal field set equals the 18-field authority,
and its stored canonical output bytes are stable. The independent Task 3
review manually recalculates every numeric sequence, confirmation key,
reference, confidence, provenance map, release/switch state, and output field
before accepting the scenario commit.

The protocol status becomes:

```markdown
Policy and 30-case scenario authority frozen. Reducer implementation pending.
No candidate, canonical, push, runtime, provider, data, call, or Phase D gate
is open.
```

- [ ] **Step 5: Run GREEN and prove no reducer exists**

```powershell
python -m unittest scripts.test_emotion_state_003_phase_c0.PhaseCScenarioContractTests -v
if (Test-Path -LiteralPath scripts/emotion_state_phase_c_temporal_tracker.py) { throw 'reducer existed before scenario freeze' }
python -m py_compile scripts/emotion_state_phase_c_contracts.py scripts/test_emotion_state_003_phase_c0.py
python scripts/check_thesis_reference_registry.py
python scripts/validate_project_drift_guard.py
python scripts/validate_context_reading_policy.py
python scripts/validate_check_setup.py
git diff --check
```

Then run the exact common post-GREEN ledger. Expected: tests/gates pass;
reducer path remains absent.

- [ ] **Step 6: Independently review and commit**

Review every expected numeric projection without executing a reducer.

```powershell
git add -- research/experiments/cases/emotion-state-003-phase-c0-scenarios.json research/experiments/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics.md scripts/emotion_state_phase_c_contracts.py scripts/test_emotion_state_003_phase_c0.py
git diff --cached --check
git commit -m "Freeze Phase C0 synthetic scenarios"
```

### Task 4: Implement Fixed-Point Folding, Decay, Caps, And Contradiction

**Files:**
- Create: `scripts/emotion_state_phase_c_temporal_tracker.py`
- Modify: `scripts/emotion_state_phase_c_contracts.py`
- Modify: `scripts/test_emotion_state_003_phase_c0.py`

**Interfaces:**
- Consumes: parsed policy, atoms, and frames.
- Produces:
  `PhaseCSignalAccumulatorV1`,
  `PhaseCFrameFoldV1`,
  `atom_support_units(atom, policy) -> int`,
  `decay_units(units, policy) -> int`, and
  `fold_frame_support(previous: PhaseCSignalAccumulatorV1 | None,
  frame: PhaseCSyntheticEvidenceFrameV1, policy: Mapping[str, Any],
  seen_independence_keys: frozenset[str]) -> PhaseCFrameFoldV1`.

- [ ] **Step 1: Write failing arithmetic tests**

```python
class PhaseCFixedPointFoldTests(PhaseCTestCase):
    def setUp(self) -> None:
        self.explicit_high = parse_phase_c_atom(
            _atom(
                counter=9001,
                evidence_class="unsolicited_explicit_statement",
            ),
            self.policy,
        )
        self.transcript_medium = parse_phase_c_atom(
            _atom(
                counter=9002,
                evidence_class="transcript_meaning",
                quality="medium",
            ),
            self.policy,
        )
        self.acoustic_low = parse_phase_c_atom(
            _atom(
                counter=9003,
                modality="acoustic",
                evidence_class="synthetic_acoustic_symbol",
                quality="low",
            ),
            self.policy,
        )
        self.unusable_proxy = parse_phase_c_atom(
            _atom(
                counter=9004,
                modality="dialogue",
                evidence_class="weak_behavioral_proxy",
                quality="unusable",
            ),
            self.policy,
        )

    def fold_case(self, case_id: str, attempted_step: int) -> PhaseCFrameFoldV1:
        scenario = self.case(case_id)
        previous = None
        seen_keys: frozenset[str] = frozenset()
        fold = None
        for index, attempt in enumerate(scenario.attempt_order):
            session = next(
                item
                for item in scenario.sessions
                if item.session_alias == attempt.frame_session_alias
            )
            frame = session.frames[attempt.frame_index]
            fold = self.tracker.fold_frame_support(
                previous,
                frame,
                self.policy,
                seen_keys,
            )
            previous = fold.accumulator
            seen_keys = seen_keys | frozenset(fold.accepted_independence_keys)
            if index == attempted_step:
                return fold
        self.fail(f"attempted step is outside case: {attempted_step}")

    def test_atom_units_round_down_exactly(self) -> None:
        self.assertEqual(self.tracker.atom_support_units(self.explicit_high, self.policy), 700)
        self.assertEqual(self.tracker.atom_support_units(self.transcript_medium, self.policy), 337)
        self.assertEqual(self.tracker.atom_support_units(self.acoustic_low, self.policy), 72)
        self.assertEqual(self.tracker.atom_support_units(self.unusable_proxy, self.policy), 0)

    def test_decay_agreement_saturation_and_caps_are_exact(self) -> None:
        self.assertEqual(self.tracker.decay_units(700, self.policy), 560)
        fold = self.fold_case("multimodal_two_turn_entry", attempted_step=0)
        self.assertEqual(
            dict(fold.accumulator.capped_net_support)["frustration"],
            730,
        )
        saturation = self.fold_case("support_saturation", attempted_step=0)
        self.assertEqual(
            dict(saturation.accumulator.gross_supporting_units)["confusion"],
            1000,
        )
        self.assertEqual(
            dict(saturation.accumulator.capped_net_support)["confusion"],
            1000,
        )

    def test_quality_acoustic_and_contradiction_caps_are_exact(self) -> None:
        contradiction = self.fold_case("same_signal_contradiction", attempted_step=0)
        accumulator = contradiction.accumulator
        self.assertEqual(dict(accumulator.gross_supporting_units)["confusion"], 1000)
        self.assertEqual(dict(accumulator.gross_opposing_units)["confusion"], 300)
        self.assertEqual(dict(accumulator.uncapped_net_support)["confusion"], 700)
        self.assertEqual(dict(accumulator.capped_net_support)["confusion"], 350)
        acoustic = self.fold_case("acoustic_only_capped", attempted_step=2)
        self.assertEqual(
            dict(acoustic.accumulator.capped_net_support)["hesitation"],
            400,
        )
```

Before RED, add four more focused tests:

1. initialize high weak supporting units `100` and low explicit opposing units
   `280`, then fold empty accepted turns until the supporting side decays to
   `0` while opposition remains positive; assert only support quality/
   provenance clears and the live cap changes from `1000` to `400`;
2. combine one new positive supporting atom with one fresh-reference atom
   whose independence key is already seen; assert no agreement bonus;
3. prove total-quality caps independently of the acoustic cap: three
   medium-quality transcript contributions have pre-cap gross support above
   `750` and capped net exactly `750`; two low-quality explicit contributions
   have pre-cap gross support `504` and capped net exactly `400`.
4. fold two newly contributing high transcript atoms for the same signal with
   distinct references and independence keys but the same `text` modality;
   assert gross support is exactly `900`, not `1000`, proving that two atoms
   from one modality cannot trigger the `100` multimodal agreement bonus.

- [ ] **Step 2: Run RED**

```powershell
python -m unittest scripts.test_emotion_state_003_phase_c0.PhaseCFixedPointFoldTests -v
```

Expected: missing tracker module/functions.

- [ ] **Step 3: Implement immutable fold types and pure arithmetic**

Use tuple-backed maps and pure helpers:

```python
def atom_support_units(
    atom: PhaseCSyntheticEvidenceAtomV1,
    policy: Mapping[str, Any],
) -> int:
    base = policy["base_support_units"][atom.evidence_class]
    multiplier = policy["quality_multipliers"][atom.quality_bucket]
    return (base * multiplier) // policy["scale"]


def decay_units(units: int, policy: Mapping[str, Any]) -> int:
    return (units * policy["retained_support_milli"]) // policy["scale"]
```

`fold_frame_support` must:

1. decay gross supporting and opposing units on a new turn;
2. add zero for a repeated independence key;
3. add one agreement bonus only for two newly contributing positive-unit
   supporting atoms with distinct modalities, references, and keys;
4. saturate gross sides at 1000;
5. detect same-signal contradiction at `300/300`;
6. compute uncapped net as `max(0, supporting - opposing)`; and
7. apply total-quality, acoustic-only, and contradiction caps with `min`.

Implement it from this exact map algorithm:

```python
signals = policy["canonical_signal_order"]
directions = policy["canonical_direction_order"]
modalities = policy["canonical_modality_order"]

# 1. Start with dense mutable work maps.
for each signal/direction:
    prior_gross = 0 if previous is None else previous_gross[signal][direction]
    gross[signal][direction] = decay_units(prior_gross, policy)
    if gross[signal][direction] == 0:
        quality[signal][direction] = None
        provenance[signal][direction] = {modality: set() for modality in modalities}
    else:
        quality/provenance = deep mutable copies of the previous side

# 2. Process the already-canonical frame atom sequence once.
local_seen = set(seen_independence_keys)
accepted_refs = []
accepted_new_keys = []
new_contributors_by_signal = {signal: [] for signal in signals}
for atom in frame.evidence_atoms:
    signal = atom.operational_signal
    direction = atom.direction
    modality = atom.modality
    accepted_refs.append(atom.evidence_ref)
    is_fresh = atom.independence_key not in local_seen
    local_seen.add(atom.independence_key)  # even unusable/zero-unit atoms retire the key
    if is_fresh:
        accepted_new_keys.append(atom.independence_key)
    units = atom_support_units(atom, policy)
    if not is_fresh or units == 0:
        continue
    gross[signal][direction] += units
    provenance[signal][direction][modality].add(atom.evidence_ref)
    quality[signal][direction] = better_quality(
        quality[signal][direction],
        atom.quality_bucket,
        policy["canonical_quality_order"],
    )
    new_contributors_by_signal[signal].append(atom)

# 3. Add at most one supporting agreement bonus per signal.
for signal in signals:
    eligible = [
        atom for atom in new_contributors_by_signal[signal]
        if atom.direction == "supports"
    ]
    if (
        len({atom.evidence_ref for atom in eligible}) >= 2
        and len({atom.independence_key for atom in eligible}) >= 2
        and len({atom.modality for atom in eligible}) >= 2
    ):
        gross[signal]["supports"] += policy["agreement_bonus"]

# 4. Saturate each side before net/caps, then derive dense projections.
for each signal/direction:
    gross[signal][direction] = min(
        gross[signal][direction],
        policy["support_saturation"],
    )
for each signal:
    contradictory = (
        gross[signal]["supports"] >= gross_support_threshold
        and gross[signal]["opposes"] >= gross_opposition_threshold
    )
    uncapped = max(0, gross_support - gross_opposition)
    live_qualities = non-None qualities from both nonzero sides
    quality_cap = total_quality_caps[best live quality] if any else 0
    live_modalities = modalities with any live provenance on either side
    signal_acoustic_only = live_modalities == {"acoustic"}
    caps = [uncapped, quality_cap]
    if signal_acoustic_only:
        caps.append(policy["acoustic_only_cap"])
    if contradictory:
        caps.append(policy["contradiction_cap"])
    capped[signal] = min(caps)
```

`better_quality` selects the smaller index in
`canonical_quality_order`; `None` loses to any real bucket. Agreement creates
units but no synthetic reference, key, modality, or quality metadata.
`accepted_evidence_refs` is every current-frame atom reference in ordinal
order. `accepted_independence_keys` is only the fresh current-frame key tuple,
including fresh zero-unit atoms, in ordinal order. `contributing_evidence_refs`
is the ordinal union of every live provenance reference after decay/addition.
For each signal, `confirming_keys_by_signal` is empty or the one-element tuple
containing the first canonical key among newly contributing, positive-unit,
supporting atoms; opposing, repeated, retired, and unusable atoms never
confirm.

Fold booleans are exact: `missing_input` iff the frame has zero atoms;
`acoustic_only` iff at least one live provenance reference exists and its live
modality union is exactly `{"acoustic"}`; `low_audio_quality_only` iff the
current frame is nonempty and every raw validated atom is acoustic with
quality in `{"low", "unusable"}`. Repeated and zero-unit unusable acoustic
atoms therefore remain low-audio evidence even though they do not contribute
support. Construct tuple maps only after all calculation, in canonical
signal/direction/modality order. Assert the produced accumulator validates
before returning the fold.

Track gross units, live highest quality, and modality/reference provenance
separately for `supports` and `opposes`, then derive each signal's cap from the
highest-quality side whose decayed gross units remain nonzero. Return every map
in canonical signal/direction/modality order. When one side decays to zero,
clear only that side's quality and provenance; the other side remains live.

Accumulator representation is dense: every numeric tuple-map contains all five
signals in canonical order; each signal's quality map contains both directions
with `None` for a zero side; and each direction's provenance map contains all
three modalities with empty tuples where absent. `contradictory_signals` is the
only sparse accumulator signal tuple. Golden `expected_internal` numeric maps
use the same dense five-signal representation; only emitted output confidence
and provenance maps are sparse.

It must not select a signal or construct a runtime-contract output.

- [ ] **Step 4: Run GREEN and mutation checks**

```powershell
python -m unittest scripts.test_emotion_state_003_phase_c0.PhaseCFixedPointFoldTests -v
python -m unittest scripts.test_emotion_state_003_phase_c0.PhaseCPolicyContractTests scripts.test_emotion_state_003_phase_c0.PhaseCInputContractTests scripts.test_emotion_state_003_phase_c0.PhaseCScenarioContractTests -v
python -m py_compile scripts/emotion_state_phase_c_contracts.py scripts/emotion_state_phase_c_temporal_tracker.py scripts/test_emotion_state_003_phase_c0.py
git diff --check
```

Then run the exact common post-GREEN ledger. Expected: all focused and
predecessor tests pass, including all pre-implementation RED cases.

- [ ] **Step 5: Independently review and commit**

The reviewer must recompute every tested integer manually and verify no float,
clock, randomness, I/O, or global state exists.

```powershell
git add -- scripts/emotion_state_phase_c_contracts.py scripts/emotion_state_phase_c_temporal_tracker.py scripts/test_emotion_state_003_phase_c0.py
git diff --cached --check
git commit -m "Implement Phase C0 fixed-point fold"
```

### Task 5: Implement Hysteresis, Output Projection, And Semantic Validation

**Files:**
- Modify: `scripts/emotion_state_phase_c_contracts.py`
- Modify: `scripts/emotion_state_phase_c_temporal_tracker.py`
- Modify: `scripts/test_emotion_state_003_phase_c0.py`

**Interfaces:**
- Consumes: `PhaseCFrameFoldV1`.
- Produces:
  `PhaseCOutputSemanticError(PhaseCContractError)`,
  `PhaseCTemporalSessionStateV1`,
  `PhaseCProjectionContextV1`,
  `PhaseCHysteresisV1`,
  `update_hysteresis(previous_state: PhaseCTemporalSessionStateV1 | None,
  fold: PhaseCFrameFoldV1, frame: PhaseCSyntheticEvidenceFrameV1,
  policy: Mapping[str, Any]) -> PhaseCHysteresisV1`,
  `project_perceived_customer_state(session_state:
  PhaseCTemporalSessionStateV1, context: PhaseCProjectionContextV1,
  policy: Mapping[str, Any])
  -> dict[str, Any]`, and
  `replay_validated_frames(frames:
  tuple[PhaseCSyntheticEvidenceFrameV1, ...], policy: Mapping[str, Any])
  -> PhaseCReplayV1`, and
  `validate_phase_c_perceived_state(payload: object,
  session_state: PhaseCTemporalSessionStateV1,
  context: PhaseCProjectionContextV1,
  policy: Mapping[str, Any]) -> dict[str, Any]`.

- [ ] **Step 1: Write failing hysteresis and output tests**

```python
class PhaseCHysteresisAndOutputTests(PhaseCTestCase):
    def run_case(self, case_id: str) -> PhaseCReplayV1:
        scenario = self.case(case_id)
        self.assertEqual(len(scenario.sessions), 1)
        return self.tracker.replay_validated_frames(
            scenario.sessions[0].frames,
            self.policy,
        )

    def test_explicit_entry_and_three_turn_transcript_entry(self) -> None:
        explicit = self.run_case("explicit_confusion_entry")
        self.assertEqual(explicit.outputs[-1]["selected_policy_signal"], "confusion")
        transcript = self.run_case("transcript_three_turn_entry")
        self.assertEqual(
            [step.hysteresis.internal_incumbent for step in transcript.states],
            [None, None, "confusion"],
        )

    def test_release_and_switch_are_exact(self) -> None:
        release = self.run_case("release_after_two_below_threshold")
        self.assertEqual(
            [step.hysteresis.internal_incumbent for step in release.states],
            ["frustration", "frustration", "frustration", "frustration", "frustration", None],
        )
        switch = self.run_case("switch_after_two_confirmations")
        self.assertEqual(
            [step.hysteresis.internal_incumbent for step in switch.states],
            ["frustration", "frustration", "frustration", "confusion"],
        )

    def test_output_is_unapproved_not_inferable_and_monotonic_vocabulary_only(self) -> None:
        result = self.run_case("explicit_frustration_entry").outputs[-1]
        self.assertFalse(result["runtime_approved"])
        self.assertEqual(result["valence_estimate"], "not_inferable")
        self.assertEqual(result["activation_estimate"], "not_inferable")
        self.assertEqual(result["engagement_estimate"], "not_inferable")
        self.assertEqual(set(result["blocked_policy_effects"]), REQUIRED_BLOCKED_POLICY_EFFECTS)
```

Before RED, add stable-order mutations for every output field
missing/extra/wrong exact type plus: selected signal absent from operational
signals; `none` coexisting with a signal; confidence key/value mismatch;
provenance/reference-union mismatch; noncanonical signal/reference/effect/
reason order; abstention without a reason; nonabstention with a reason; wrong
confidence bucket; acoustic or abstained effect expansion; missing blocked
effect; inferable valence/activation/engagement; `stale_input` or
`phase_a_no_audio` emission; and `runtime_approved=True`. The mutation builder
is test-owned and imports no semantic rule table. Add exact assertions for
entry-key maps, switch challenger/key sequence, release streak, incumbent
tenure, emitted confidence/provenance, quality, trajectory, and abstention
reason list for every applicable frozen case.
Also pass each top-level non-object value `None`, `[]`, `""`, `0`, and `False`
directly and require
`PhaseCOutputSemanticError("perceived_not_object")` before any field access.
Add direct trajectory boundary fixtures not delegated to the 30-case matrix:
interest delta `+100/-100` yields `improving/worsening`; a non-interest delta
`+100/-100` yields `worsening/improving`; and both `+99` and `-99` yield
`stable`.

Also add test-owned dense fold/state/context builders that bypass preceding
support arithmetic and isolate these exact branch boundaries before RED:

- visibility includes a signal at net `200` and excludes it at `199`;
- an explicit qualifying top signal enters at net `550` and not at `549`;
- an incumbent at net `350` does not increment release, while net `349` with
  prior release streak `1` releases on the second below-threshold turn;
- a challenger at net `650` with incumbent net `499`, a prior one-key switch
  streak, and a fresh second confirming key switches, while challenger `649`
  over the same incumbent has exact advantage `150` and fails only the `650`
  switch threshold;
- challenger `700` over incumbent `550` qualifies at exact advantage `150`,
  while challenger `700` over incumbent `551` fails at advantage `149`;
- selected confidence is `low` at `549`, `medium` at `550` and `749`, and
  `high` at `750`; and
- two non-incumbent challengers tied at or above the switch threshold block
  switching and clear the switch streak.

The builders populate every dense map, provenance tuple, quality slot, and
projection-context field with contract-valid canonical values. These are
direct unit fixtures for `update_hysteresis` and
`project_perceived_customer_state`; they do not call the fold arithmetic under
test and therefore cannot mask `>`/`>=`, bucket, or tie defects.

- [ ] **Step 2: Run RED**

```powershell
python -m unittest scripts.test_emotion_state_003_phase_c0.PhaseCHysteresisAndOutputTests -v
```

Expected: missing state/hysteresis/projection functions.

- [ ] **Step 3: Implement exact hysteresis**

Use no-incumbent entry, incumbent release, and challenger switch as separate
pure branches:

```python
if incumbent is None:
    if exact_top_tie:
        next_incumbent = None
    elif top_signal_meets_entry_and_confirmation:
        next_incumbent = top_signal
elif incumbent_below_release:
    next_incumbent = None if release_streak >= 2 else incumbent
elif challenger_meets_threshold_advantage_and_confirmation:
    next_incumbent = challenger
else:
    next_incumbent = incumbent
```

Entry/switch confirmations require distinct confirming independence keys.
Release counts accepted new logical turns below `350` even with empty atoms.
Explicit-statement entry requires one accepted turn; it does not shorten switch
confirmation.

Confirmation is turn-based. For each qualifying signal, one accepted turn may
append at most the first canonical newly contributing supporting independence
key. If that key already occurs in the current streak, restart the streak with
that one key; if the turn has no qualifying key, clear the streak. Multiple
atoms in one frame can never satisfy a two-turn entry or switch requirement.
`incumbent_tenure` is `0` with no internal incumbent, becomes `1` on entry or
switch, and increments once per accepted new logical turn while that same
incumbent persists. Correction replay recomputes tenure from the canonical
replacement sequence and never adds a separate correction turn.

Use this exact hysteresis algorithm. All maps begin dense and canonically
ordered. `nets` is the dense capped-net map. `new_key(signal)` is the first
tuple member from `fold.confirming_keys_by_signal[signal]`, or `None`.

```python
ranked = sorted(signals, key=lambda s: (-nets[s], signal_index[s]))
top = ranked[0]
top_tied = len(signals) > 1 and nets[ranked[1]] == nets[top]
previous_h = empty_hysteresis() if previous_state is None else previous_state.hysteresis

if previous_h.internal_incumbent is None:
    clear switch state and release_streak
    if top_tied or nets[top] < entry_threshold:
        clear every entry streak
        next_incumbent = None
    else:
        clear every entry streak except top
        key = new_key(top)
        entry[top] = append_or_clear(entry[top], key)
        explicit_now = any(
            newly contributing positive supporting atom for top has
            evidence_class == explicit_entry_evidence_class
        )
        required = explicit_statement_entry_count if explicit_now else entry_count
        if len(entry[top]) >= required:
            next_incumbent = top
            clear every entry streak
        else:
            next_incumbent = None
elif nets[previous_incumbent] < release_threshold:
    clear every entry and switch streak
    release_streak = previous_release_streak + 1
    if release_streak >= release_count:
        next_incumbent = None
        release_streak = 0
    else:
        next_incumbent = previous_incumbent
else:
    clear every entry streak
    release_streak = 0
    challengers = signals excluding previous_incumbent
    challenger ranking is (-net, canonical signal index)
    tied = top two challengers have equal net
    qualified = (
        not tied
        and nets[challenger] >= switch_threshold
        and nets[challenger] - nets[previous_incumbent] >= minimum_switch_advantage
    )
    if not qualified:
        clear switch challenger and keys
        next_incumbent = previous_incumbent
    else:
        key = new_key(challenger)
        if previous_switch_challenger != challenger:
            switch_keys = ()
        switch_keys = append_or_clear(switch_keys, key)
        if len(switch_keys) >= switch_count:
            next_incumbent = challenger
            clear switch challenger and keys
        else:
            next_incumbent = previous_incumbent
            switch_challenger = challenger
```

`append_or_clear(streak, None)` returns `()`. With a key, it appends when the
key is absent and otherwise returns `(key,)`; keys are already canonical and
only one can arrive per signal/turn. `explicit_now` is computed by matching the
fold's current-frame contributing refs/keys back to the frame; repeated,
retired, opposing, or zero-unit explicit atoms do not qualify. An exact top
tie blocks entry. An exact challenger tie blocks switching. Incumbent release
is evaluated before challenger switching.

Tenure is `0` if `next_incumbent is None`; `1` on entry/switch; otherwise
`previous_tenure + 1`. Entry maps are empty whenever an incumbent exists.
Switch fields are empty whenever no incumbent exists, on release, and after a
completed switch. Every returned hysteresis object is revalidated for those
cross-field rules.

- [ ] **Step 4: Implement exact projection and independent semantic checks**

Projection must:

- suppress the internal incumbent on missing, low-audio-only, contradiction, or
  other abstained output;
- map nonselected visible signals to `possible_*`;
- compute confidence as `capped_net / 1000.0`;
- emit only contributing references and exact modality provenance;
- use exact allowed-effect mappings and blocked order;
- derive quality and trajectory exactly from the design; and
- call existing `validate_perceived_customer_state`.

Projection uses this exact derivation:

```python
visible = [signal in canonical order if capped_net[signal] >= 200]
reasons = []
if contradictory_signals:
    reasons += ["contradictory_evidence"]
if fold.low_audio_quality_only:
    reasons += ["low_audio_quality"]
if fold.missing_input:
    reasons += ["missing_input"]

candidate = session_state.hysteresis.internal_incumbent
candidate_visible = candidate is not None and candidate in visible
if candidate is None or not candidate_visible:
    reasons += ["insufficient_evidence"]
reasons = unique reasons sorted by abstention_reason_order
abstained = bool(reasons)
selected = "none" if abstained else candidate

if selected != "none":
    emitted = [selected] + [
        f"possible_{signal}" for signal in visible if signal != selected
    ]
else:
    emitted = [f"possible_{signal}" for signal in visible] or ["none"]
```

`abstention_primary_priority` fixes predicate-evaluation precedence only; it
does not define a separate persisted or aggregate primary count. The output
retains every applicable reason in canonical reason order, and
`counts_by_abstention_reason` increments every emitted reason occurrence.
`insufficient_evidence` is appended only when selection cannot be emitted; it
is not added merely because another reason already forces abstention while a
visible incumbent exists.

For each emitted base/`possible_*` signal, use the underlying base signal:
confidence is `capped_net / 1000.0`; provenance is the canonical nonempty
modality map formed from both live directions; and evidence refs are the
ordinal union of emitted provenance. `["none"]` has empty confidence,
provenance, and refs. The selected bucket is `high` at `>=750`, `medium` at
`>=550`, otherwise `low`; `none` is always `low`.

Quality uses emitted provenance except for the explicit low-audio abstention:
no emitted refs plus `fold.low_audio_quality_only` -> `low_quality`; other no
refs -> `insufficient`; if every live quality attached to emitted references
is `low`/`unusable` -> `low_quality`; otherwise modality union `{"text"}` ->
`text_only`, `{"acoustic"}` -> `acoustic_only`, `{"dialogue"}` ->
`low_quality`, and two or more modalities -> `multimodal`. High-quality
acoustic evidence below visibility therefore remains `insufficient`.
Contradiction trajectory is `contradictory`. Any abstention without
contradiction, no prior emitted selection, or changed emitted selection is
`insufficient_history`. Otherwise require the selected signal to equal
`context.prior_emitted_selected_signal` and compare current selected support
to `context.prior_emitted_selected_support`: absolute delta
`<100` -> `stable`; for interest positive/negative delta -> improving/
worsening; for every other signal positive/negative delta -> worsening/
improving.

Allowed effects are `["preserve"]` for abstention or acoustic-only output;
otherwise the exact policy list for the selected base signal. Blocked effects
are the full policy order. Identities come from the accepted frame; all three
estimates are `not_inferable`; version is `emotion-state-evidence-v2`; runtime
approval is false.

The Phase C0 semantic validator must independently recompute:

- abstention cross-fields;
- confidence buckets;
- visible/selected signal mapping;
- provenance/ref union;
- acoustic-only preserve-only rule;
- effect mapping/order;
- all `not_inferable` values; and
- `runtime_approved=False`.

Every failure in this validator, including normalization of a failure from the
existing base perceived-state validator, raises
`PhaseCOutputSemanticError(<exact-code>)`; it never degrades an output-semantic
defect to a generic mechanical mismatch. The subclass retains the stable
`.code` field and is not caught or wrapped by `advance`.

It does not call `project_perceived_customer_state`. It independently derives
the expected mapping from session state, immutable projection context, and
policy using the rules above, compares fields in this error precedence, then
calls the existing base contract validator last. The context owns the prior
emitted signal/support plus current fold/frame; the final state owns the new
last-emission fields. Validation asserts those final fields equal the payload
while trajectory uses only prior values from context:

```text
perceived_not_object
perceived_field_set
perceived_field_type
perceived_identity
inferable_estimate
runtime_approved
forbidden_abstention_reason
signal_projection
confidence_projection
confidence_bucket
provenance_projection
evidence_ref_union
evidence_quality
trajectory
allowed_effects
blocked_effects
abstention_semantics
noncanonical_output_order
base_perceived_state_contract
```

The first validator branch is exact and precedes every lookup, iteration,
copy, or serialization of the supplied payload:

```python
if type(payload) is not dict:
    raise PhaseCOutputSemanticError("perceived_not_object")
```

`replay_validated_frames` folds one already parsed, single-session,
new-turn-only sequence from an empty state and returns every immutable state
snapshot and output. It requires nonempty input; exact session/campaign/version
identity across frames; strictly increasing turn sequence; unique turn/event/
reference identities; and revision zero. For each frame it folds against the
previous accumulator/seen keys, updates hysteresis, builds a provisional
immutable state and a `PhaseCProjectionContextV1` from prior emission plus the
current fold/frame, projects output, then replaces only
`last_emitted_selected_signal/support` with the emitted base selection/support
or `None/None` on abstention. It semantically validates output against the
final state plus the unchanged context. The final state is revalidated and
appended.
It rejects corrections; Task 6 adds correction-aware `advance`.

- [ ] **Step 5: Run GREEN and existing contract suite**

```powershell
python -m unittest scripts.test_emotion_state_003_phase_c0.PhaseCHysteresisAndOutputTests -v
python -m py_compile scripts/emotion_state_phase_c_contracts.py scripts/emotion_state_phase_c_temporal_tracker.py scripts/test_emotion_state_003_phase_c0.py
git diff --check
```

Then run the exact common post-GREEN ledger. Expected: focused tests, the
complete Phase C0 module, and all 16 Phase B contract tests pass.

- [ ] **Step 6: Independently review and commit**

Review must distinguish internal incumbent from emitted selection and confirm
that effect output is declared vocabulary, not adapter enforcement.

```powershell
git add -- scripts/emotion_state_phase_c_contracts.py scripts/emotion_state_phase_c_temporal_tracker.py scripts/test_emotion_state_003_phase_c0.py
git diff --cached --check
git commit -m "Add Phase C0 hysteresis and projection"
```

### Task 6: Implement Advance, Correction Replay, Rejection No-Mutation, And Isolation

**Files:**
- Modify: `scripts/emotion_state_phase_c_contracts.py`
- Modify: `scripts/emotion_state_phase_c_temporal_tracker.py`
- Modify: `scripts/test_emotion_state_003_phase_c0.py`

**Interfaces:**
- Consumes: all contract/fold/hysteresis/projection functions.
- Produces:
  `advance(previous_state, frame, policy) -> tuple[PhaseCTemporalSessionStateV1, dict[str, Any]]`,
  `canonical_session_state_bytes(state: PhaseCTemporalSessionStateV1 | None)
  -> bytes`,
  `canonical_semantic_replay_bytes(state: PhaseCTemporalSessionStateV1,
  output: dict[str, Any]) -> bytes`,
  contracts-owned `validate_phase_c_session_state(
  state: PhaseCTemporalSessionStateV1,
  policy: Mapping[str, Any]) -> PhaseCTemporalSessionStateV1`,
  tracker-owned `validate_phase_c_state_replay(state, policy) -> None`,
  tracker-owned `validate_phase_c_replayed_output(
  payload: object, state: PhaseCTemporalSessionStateV1,
  policy: Mapping[str, Any]) -> dict[str, Any]`, and
  cross-frame evidence-reference collision rejection using the existing
  `PhaseCEventRejected` type.

- [ ] **Step 1: Write failing correction/rejection/isolation tests**

```python
class PhaseCAdvanceTests(PhaseCTestCase):
    def execute_attempt(self, state, scenario, attempt):
        payload = materialize_phase_c_scenario_attempt_payload(
            scenario,
            attempt,
        )
        frame = parse_phase_c_frame(payload, self.policy)
        return self.tracker.advance(state, frame, self.policy)

    def advance(self, state, frame):
        return self.tracker.advance(state, frame, self.policy)

    def fold_frames(self, frames):
        state = None
        output = None
        for frame in frames:
            state, output = self.advance(state, frame)
        return state, output

    def test_latest_revision_replaces_and_replays(self) -> None:
        scenario = self.case("latest_turn_correction_replay")
        frames = scenario.sessions[0].frames
        first_state, first_output = self.advance(None, frames[0])
        corrected_state, corrected_output = self.advance(first_state, frames[1])
        normalized = dataclasses.replace(
            frames[1],
            event_id="event-normalized-fresh",
            input_revision=0,
        )
        fresh_state, fresh_output = self.fold_frames([normalized])
        self.assertEqual(
            self.tracker.canonical_semantic_replay_bytes(
                corrected_state,
                corrected_output,
            ),
            self.tracker.canonical_semantic_replay_bytes(
                fresh_state,
                fresh_output,
            ),
        )
        self.assertEqual(
            len(corrected_state.watermark.event_history_by_id),
            2,
        )
        self.assertNotEqual(
            canonical_session_state_bytes(corrected_state),
            canonical_session_state_bytes(fresh_state),
        )
        self.assertEqual(corrected_output["selected_policy_signal"], "interest")

    def test_every_rejection_preserves_prior_state_bytes(self) -> None:
        for case_id in REJECTION_CASE_IDS:
            scenario = self.case(case_id)
            state = None
            for attempt, expected in zip(
                scenario.attempt_order,
                scenario.expected_steps,
                strict=True,
            ):
                if expected.disposition == "accepted":
                    state, _output = self.execute_attempt(
                        state,
                        scenario,
                        attempt,
                    )
                    continue
                before = canonical_session_state_bytes(state)
                with self.subTest(
                    case_id=case_id,
                    rejection_code=expected.rejection_code,
                ):
                    with self.assertRaises(PhaseCContractError) as caught:
                        self.execute_attempt(state, scenario, attempt)
                    self.assertEqual(
                        caught.exception.code,
                        expected.rejection_code,
                    )
                    self.assertEqual(
                        before,
                        canonical_session_state_bytes(state),
                    )

    def test_interleaved_sessions_equal_separate_folds(self) -> None:
        scenario = self.case("simultaneous_sessions_isolated")
        sessions = {item.session_alias: item for item in scenario.sessions}
        interleaved_states = {alias: None for alias in sessions}
        for attempt in scenario.attempt_order:
            state, _output = self.execute_attempt(
                interleaved_states[attempt.state_session_alias],
                scenario,
                attempt,
            )
            interleaved_states[attempt.state_session_alias] = state
        separate_states = {
            alias: self.fold_frames(session.frames)[0]
            for alias, session in sessions.items()
        }
        self.assertEqual(
            {
                alias: canonical_session_state_bytes(state)
                for alias, state in interleaved_states.items()
            },
            {
                alias: canonical_session_state_bytes(state)
                for alias, state in separate_states.items()
            },
        )

    def test_cross_feeding_interleaved_session_frames_rejects(self) -> None:
        scenario = self.case("simultaneous_sessions_isolated")
        sessions = {item.session_alias: item for item in scenario.sessions}
        aliases = tuple(sessions)
        left_state, _ = self.advance(None, sessions[aliases[0]].frames[0])
        right_state, _ = self.advance(None, sessions[aliases[1]].frames[0])
        with self.assertRaisesRegex(PhaseCEventRejected, "cross_session"):
            self.advance(left_state, sessions[aliases[1]].frames[1])
        with self.assertRaisesRegex(PhaseCEventRejected, "cross_session"):
            self.advance(right_state, sessions[aliases[0]].frames[1])
```

Before RED, add every mutation/metamorphic case below:

- identical replay;
- rejected call leaves the input object and canonical bytes unchanged;
- correction equals normalized fresh semantic projection while retaining its
  two-event watermark/history;
- multi-revision correction equals normalized replay with the same retired-key
  seed, and an older retired key contributes zero;
- a correction that drops a repeated key from one turn does not retire it
  while another retained current turn still contains that key;
- a later new turn that reintroduces an older retired key records zero
  addition, and one more accepted turn/replay proves it remains retired;
- dropped correction references/keys cannot be recycled;
- wrong prior-state schema, policy ID/hash, identity maps, evidence history,
  accepted-frame ordering, accumulator, hysteresis, provenance, accepted-turn
  count, or last-emitted fields reject before frame use;
- interleaved sessions equal independent folds;
- post-parse list/dict mutation cannot alter frozen dataclasses; and
- neither new module exposes a user-defined mutable module-level container.

Also replay `explicit_confusion_entry`, prove
`validate_phase_c_replayed_output(valid_output, state, policy)` succeeds, then
set only `runtime_approved=True` in a copied output and require
`PhaseCOutputSemanticError("runtime_approved")`. This RED proves the
independent replayed-output check exists before the evaluator relies on it.

- [ ] **Step 2: Run RED**

```powershell
python -m unittest scripts.test_emotion_state_003_phase_c0.PhaseCAdvanceTests -v
```

Expected: missing `advance`, replay, and rejection types.

- [ ] **Step 3: Implement advance as validate-then-rebuild**

Use this exact control flow:

```python
def advance(previous_state, frame, policy):
    validated_policy = validate_phase_c_policy(policy)
    if previous_state is not None:
        validate_phase_c_session_state(
            previous_state,
            validated_policy,
        )
        validate_phase_c_state_replay(
            previous_state,
            validated_policy,
        )
    validated_frame = validate_phase_c_frame(frame, validated_policy)
    next_watermark = validate_phase_c_event_identity(
        validated_frame,
        watermark_for(previous_state, validated_frame),
    )
    replaced_frame = replaced_frame_for(previous_state, validated_frame)
    candidate_frames = candidate_frame_sequence(
        previous_state,
        validated_frame,
    )
    validate_candidate_reference_uniqueness(
        previous_state,
        candidate_frames,
        replaced_frame,
    )
    prior_current_keys = frame_independence_keys(
        accepted_frames_for(previous_state)
    )
    candidate_current_keys = frame_independence_keys(candidate_frames)
    retired_keys = retired_independence_keys(previous_state) | (
        prior_current_keys - candidate_current_keys
    )
    next_evidence_history = append_evidence_history_event(
        previous_state,
        validated_frame,
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
```

No candidate object becomes observable before every validation succeeds.
Correction replaces only the latest frame and replays with no extra decay.
Historical references and independence keys are monotonic. A correction may
retain a reference/key from its replaced frame or introduce a genuinely new
one; a dropped identity becomes retired and cannot be recycled later.
Semantic replay pre-seeds the monotonic `retired_independence_keys` set plus
keys newly dropped by the candidate. Reintroducing a key retired by an older
correction therefore still adds zero on that turn and every later replay,
while keys retained from the immediately replaced frame preserve their
contribution eligibility.
`append_evidence_history_event` appends the new event's exact synthetic
reference/key tuples without discarding older correction events; historical
sets are derived from that history, never guessed from the current frames. A
fresh reference with a repeated key is accepted, recorded as seen, contributes
zero, and stays out of provenance.
All `previous_state=None` history/current-key helpers return immutable empty
tuples or frozensets.

The helpers in that control flow are exact:

- `watermark_for(None, frame)` returns `initial_phase_c_watermark(frame)`;
  otherwise it returns the already validated state watermark.
- `replaced_frame_for` returns `None` for a new turn and otherwise the final
  accepted frame, requiring its turn ID/sequence to match the correction.
- `candidate_frame_sequence` appends a new turn or replaces exactly the final
  frame for a correction; it never sorts.
- `frame_independence_keys` and its reference analogue return ordinal sets over
  current frames.
- incoming references must be unique within candidate current frames. A
  historical reference may reappear only in the immediately replaced frame;
  every other historical collision raises
  `PhaseCEventRejected("duplicate_evidence_reference")`.
- `append_evidence_history_event` appends exactly
  `(event_id, sorted atom refs, sorted atom keys)` and stores entries sorted by
  event ID. It requires one entry for every watermark event and no other entry.
- historical seen refs/keys are the ordinal union of all event-history
  entries. Current semantic replay begins its key set with retired keys only,
  then adds current-frame accepted keys in frame order; historical keys are a
  monotonic audit ledger, not a blanket zeroing seed.
- `replay_frame_semantics` runs the Task 5 new-turn fold/update/project sequence
  over `candidate_frames`, builds final state with the supplied watermark and
  event history, stores monotonic seen ledgers from history, and stores the
  supplied retired set. It returns the final immutable projection context
  alongside state/output. It does not call `advance`.

`validate_phase_c_session_state` checks in this exact order:

1. frozen dataclass type, schema `PhaseCTemporalSessionStateV1`, and exact
   scalar/tuple/frozenset types;
2. exact policy ID and SHA-256 of canonical validated policy;
3. state session/campaign/version equal watermark expected identities;
4. watermark self-consistency under Task 2 rules;
5. nonempty accepted frames, strictly increasing turn sequences, one current
   frame per known turn, all identities equal state identity, and each current
   revision equal the watermark's latest revision;
6. evidence-history event IDs exactly equal watermark events; every stored
   ref/key tuple is structurally canonical and unique, and the latest history
   entry for each turn exactly equals that turn's current accepted frame atom
   identities; older event bodies are not available for direct comparison;
7. `seen_evidence_refs`/`seen_independence_keys` equal the ordinal historical
   unions;
8. derive retired keys by visiting events in
   `(turn_sequence, input_revision, event_id)` order while maintaining the
   latest key tuple for every turn. Before and after each correction, compute
   the global union across all latest turns and add only
   `global_keys_before - global_keys_after`; require exact equality to
   `retired_independence_keys`;
9. validate dense accumulator and hysteresis shapes/order/cross-fields;
10. current contributing refs equal the ordinal union of live accumulator
    provenance, accepted-turn count equals current frame count, and
    last-emitted signal/support are both `None` or a valid base signal plus its
    exact capped support.

Evidence-history validation obtains turn/revision from
`watermark.event_history_by_id`; no duplicate `(turn, revision)` can exist.
To validate historical frame identities, state
`evidence_history_by_event` is the authority for refs/keys while the watermark
is the authority for event/turn/revision; current accepted frames must match
the latest history entry for each turn. Older bodies are intentionally not
stored.

`validate_phase_c_state_replay` calls the lower-level semantic replay once over
current accepted frames with the state's retired-key seed. It compares the
recomputed accumulator, hysteresis, current contributing refs, accepted-turn
count, last-emitted fields, and recomputed final output semantics. It does not
accept or validate a caller-supplied output, compare watermark/history/seen
ledgers, or call `advance`.

Both replay validators share one private lower-level recomputation that returns
the recomputed state projection, deterministic expected output, and immutable
final `PhaseCProjectionContextV1`. `validate_phase_c_replayed_output` performs
the same state-replay comparisons, then passes the caller's actual payload to
`validate_phase_c_perceived_state(payload, state, context, policy)` and
requires the canonical bytes of the returned validated mapping to equal the
independently replayed expected output. It never serializes, copies, indexes,
or otherwise consumes the caller's payload before the semantic validator
returns that exact dictionary. A semantic difference raises the exact
`PhaseCOutputSemanticError` code from Task 5, or
`PhaseCOutputSemanticError("replayed_output_mismatch")` if only the final byte
comparison differs. It never calls `advance` or trusts the caller's output to
construct expected values.

`canonical_session_state_bytes` recursively converts frozen dataclasses and
tuples to canonical JSON values, sorts frozensets, and serializes `None` as
JSON `null`. `canonical_semantic_replay_bytes` serializes exactly:

- accepted frames with `event_id` and `input_revision` removed;
- accumulator and hysteresis;
- current contributing references;
- accepted-turn count;
- last emitted selected signal/support; and
- the emitted output.

It excludes the watermark, event-scoped evidence history, and historical
seen-reference/key ledgers. That projection proves reducer semantics without
falsely equating a real correction history to a one-event normalized history.
The expected normalized replay receives the same retired-independence-key seed
as the actual correction; only a first correction is equivalent to
`advance(None, normalized_frame)`.

`validate_phase_c_session_state` fail-closes exact schema/type/order,
policy ID/hash, session/campaign identities, watermark consistency, canonical
frame sequence, and event-history/seen/retired-ledger algebra. It derives the
retired set by replaying event history in canonical
`(turn_sequence, input_revision, event_id)` order and comparing each correction
revision with the prior latest revision for that turn.
`validate_phase_c_state_replay` uses the lower-level semantic fold, never
`advance`, to recompute accumulator, hysteresis, current provenance,
accepted-turn count, and last-emitted fields. This avoids recursive validation.
`advance` does not blanket-wrap exceptions: policy/frame/prior-state contract
failures remain `PhaseCContractError`; identity and cross-frame
evidence-reference failures are `PhaseCEventRejected`; output-semantic failures
remain `PhaseCOutputSemanticError`. All expose the stable `.code` field
inherited from `PhaseCContractError`.

- [ ] **Step 4: Run GREEN and metamorphic tests**

```powershell
python -m unittest scripts.test_emotion_state_003_phase_c0.PhaseCAdvanceTests -v
python -m unittest scripts.test_emotion_state_003_phase_c0 -v
python -m py_compile scripts/emotion_state_phase_c_contracts.py scripts/emotion_state_phase_c_temporal_tracker.py scripts/test_emotion_state_003_phase_c0.py
git diff --check
```

Then run the exact common post-GREEN ledger. Expected: the complete Phase C0
module passes, including every pre-implementation mutation/metamorphic RED
case.

- [ ] **Step 5: Independently review and commit**

```powershell
git add -- scripts/emotion_state_phase_c_contracts.py scripts/emotion_state_phase_c_temporal_tracker.py scripts/test_emotion_state_003_phase_c0.py
git diff --cached --check
git commit -m "Add Phase C0 deterministic advance"
```

### Task 7: Evaluate Frozen Golden And Metamorphic Scenarios In Memory

**Files:**
- Modify: `scripts/emotion_state_phase_c_contracts.py`
- Modify: `scripts/emotion_state_phase_c_temporal_tracker.py`
- Modify: `scripts/test_emotion_state_003_phase_c0.py`

**Interfaces:**
- Consumes: frozen scenario matrix and `advance`.
- Produces:
  `PhaseCScenarioOutcomeV1`,
  `PhaseCScenarioEvaluationV1`, and
  `evaluate_phase_c_scenarios(policy, scenarios)`.

- [ ] **Step 1: Write failing complete-matrix tests**

```python
class PhaseCScenarioEvaluationTests(PhaseCTestCase):
    def test_all_30_frozen_scenarios_match_golden_expectations(self) -> None:
        evaluation = self.tracker.evaluate_phase_c_scenarios(
            self.policy,
            self.scenarios,
        )
        self.assertEqual(evaluation.total_scenarios, 30)
        self.assertEqual(evaluation.passed_scenarios, 30)
        self.assertEqual(evaluation.failed_scenarios, 0)
        self.assertEqual(tuple(item.case_id for item in evaluation.outcomes), EXPECTED_SCENARIO_IDS)

    def test_expected_outputs_are_not_built_by_the_reducer_renderer(self) -> None:
        source = inspect.getsource(
            self.tracker.evaluate_phase_c_scenarios
        )
        self.assertNotIn("render_phase_c_report", source)
        self.assertNotIn("build_phase_c_result", source)

    def test_golden_mutation_is_detected(self) -> None:
        mutated = copy.deepcopy(self.raw_scenarios)
        mutated["scenarios"][0]["expected_steps"][0]["expected_internal"]["capped_net_support"]["confusion"] = 699
        scenarios = validate_phase_c_scenario_payload(
            mutated,
            self.policy,
        )
        evaluation = self.tracker.evaluate_phase_c_scenarios(
            self.policy,
            scenarios,
        )
        self.assertEqual(evaluation.failed_scenarios, 1)

    def test_every_unexpected_rejection_acceptance_maps_to_safety_invariant(self) -> None:
        fixture = self.tracker.replay_validated_frames(
            self.case("explicit_confusion_entry").sessions[0].frames,
            self.policy,
        )
        accepted = (fixture.final_state, fixture.outputs[-1])
        original = self.tracker._execute_scenario_attempt
        for case_id, safety_invariant in (
            UNEXPECTED_ACCEPTANCE_SAFETY_INVARIANT_BY_CASE.items()
        ):
            def injected(prior, scenario, attempt, policy):
                index = scenario.attempt_order.index(attempt)
                expected = scenario.expected_steps[index]
                if scenario.case_id == case_id and expected.disposition == "rejected":
                    return accepted
                return original(prior, scenario, attempt, policy)

            with self.subTest(case_id=case_id):
                with mock.patch.object(
                    self.tracker,
                    "_execute_scenario_attempt",
                    side_effect=injected,
                ):
                    evaluation = self.tracker.evaluate_phase_c_scenarios(
                        self.policy,
                        self.scenarios,
                    )
                outcome = next(
                    item for item in evaluation.outcomes
                    if item.case_id == case_id
                )
                self.assertIn("golden_projection", outcome.failed_invariants)
                self.assertIn(safety_invariant, outcome.failed_invariants)
                self.assertEqual(evaluation.failed_scenarios, 1)
```

Before RED, add the shared test-owned helper
`_mechanical_negative_evaluation(test_case)`. It replays the valid
`empty_frame_missing_input` fixture once, then patches only
`_execute_scenario_attempt` for the sole accepted step of
`explicit_confusion_entry` to return that replacement state/output; every
other attempt calls the original wrapper. It invokes the evaluator while the
patch is active and returns the resulting aggregate. This creates exactly one
non-safety `golden_projection` failure while changing actual emitted-reason
counts by `+1` for `missing_input` and `insufficient_evidence`.

Add `test_negative_evaluation_keeps_actual_abstention_counts` using that
helper. Assert:

- `passed_scenarios == 29`, `failed_scenarios == 1`;
- `golden_projection == 1` and every `SAFETY_INVARIANT_NAMES` count is zero;
- actual `missing_input` and `insufficient_evidence` counts each equal their
  frozen golden total plus one;
- the other two reason counts equal their frozen golden totals; and
- the evaluator returns normally rather than rejecting the negative aggregate.

Later runner and validator tests reuse only this test helper; production code
does not expose a fault-injection interface.

Add a second shared test-owned helper
`_semantic_negative_evaluation(test_case)`. It replays the valid
`explicit_confusion_entry` fixture, copies its valid output, changes only
`runtime_approved` to `True`, and patches `_execute_scenario_attempt` for that
one accepted step to return the original valid successor plus the invalid
output. The evaluator must independently inspect the actual returned payload,
not trust `advance` or state replay alone.

Add two more focused tests:

- the semantic-negative helper returns `29/1`, records
  `golden_projection == 1` and `semantic_output == 1`, sets
  `privacy_boundary_passed == False`, and changes no other safety invariant;
- patch the same accepted step to raise
  `PhaseCOutputSemanticError("runtime_approved")` directly and require the
  same `golden_projection` plus `semantic_output` classification.

The first proves the successful-return defense against an injected invalid
payload; the second proves that the real typed exception propagated by
`advance` cannot be misclassified as a mechanical-only failure.

Add `_structural_semantic_negative_evaluation(test_case)` as a third
test-owned helper. It returns the same valid explicit-confusion successor but
uses a fresh `object()` as the injected output, so the value is neither a
mapping nor JSON serializable. Its focused RED must prove evaluation still
returns `29/1`, records `golden_projection == 1` and
`semantic_output == 1`, sets `privacy_boundary_passed == False`, and raises no
`TypeError`, `KeyError`, or serialization error. This fixture proves
validation precedes every canonical comparison, field lookup, state install,
and abstention count.

- [ ] **Step 2: Run RED**

```powershell
python -m unittest scripts.test_emotion_state_003_phase_c0.PhaseCScenarioEvaluationTests -v
```

Expected: missing evaluation types/functions.

- [ ] **Step 3: Implement evaluation without persistence**

For each case:

- create an independent state per session alias;
- execute the exact `attempt_order`, materializing any allowlisted negative
  mutation and parsing it before calling `advance`;
- compare accepted projections field-by-field;
- compare rejection code and prior-state bytes;
- run correction/session isolation assertions;
- record only case ID, family, modality/signal family, passed boolean, and
  invariant names in the in-memory outcome; and
- never retain frames, atom bodies, state bodies, references, or identifiers in
  aggregate serialization.

Use this exact execution/comparison algorithm:

```python
states = {session.session_alias: None for session in scenario.sessions}
failed = set()
rejection_count = 0
abstention_counts = zero dense emitted-reason map

for attempt, expected in zip(attempt_order, expected_steps, strict=True):
    prior = states[attempt.state_session_alias]
    prior_bytes = canonical_session_state_bytes(prior)
    try:
        successor, output = _execute_scenario_attempt(
            prior,
            scenario,
            attempt,
            policy,
        )
    except PhaseCOutputSemanticError:
        failed.add("golden_projection")
        failed.add("semantic_output")
        if canonical_session_state_bytes(prior) != prior_bytes:
            failed.add("rejection_no_mutation")
        continue
    except PhaseCContractError as exc:
        if expected.disposition != "rejected" or exc.code != expected.rejection_code:
            failed.add("golden_projection")
        else:
            rejection_count += 1
        if canonical_session_state_bytes(prior) != prior_bytes:
            failed.add("rejection_no_mutation")
        continue

    if expected.disposition == "rejected":
        failed.add("golden_projection")
        failed.add(UNEXPECTED_ACCEPTANCE_SAFETY_INVARIANT_BY_CASE[case_id])
        # Never install an unexpectedly accepted rejection successor.
        continue

    try:
        validated_output = validate_phase_c_replayed_output(
            output,
            successor,
            policy,
        )
    except PhaseCContractError:
        failed.add("golden_projection")
        failed.add("semantic_output")
        # Never serialize, index, install, or count an invalid returned output.
        continue

    actual_internal = exact_internal_projection(successor)
    if canonical_json_bytes(validated_output) != expected.expected_output_bytes:
        failed.add("golden_projection")
    if actual_internal != expected.expected_internal:
        failed.add("golden_projection")
    states[attempt.state_session_alias] = successor
    for reason in validated_output["abstention_reasons"]:
        abstention_counts[reason] += 1
```

`_execute_scenario_attempt` is a four-line private wrapper that materializes,
parses, and calls `advance`; it contains no branch and returns the successor/
output tuple. It exists so the pre-implementation mutation test can force the
otherwise impossible unsafe-acceptance path, including parser-negative cases,
without weakening a production parser or public function signature.

`exact_internal_projection` copies exactly the 18 scenario-authority fields
from the validated state/accumulator/hysteresis, converting dense tuple maps
to dense JSON objects and no other value. For accepted corrections it compares
the replacement successor, not an intermediate append state.

After the attempt loop, special invariant checks run only for their named
authority cases: deterministic case folds twice and compares every state/
output canonical byte; correction case compares the normalized semantic
projection while retaining real watermark/history checks; simultaneous
sessions compares interleaved and separate bytes and runs cross-feed rejection;
every rejection case reasserts unchanged prior bytes; and every accepted
output runs semantic validation. Each check adds only its exact named
invariant. `failed_invariants` is the tuple of present names in
`INVARIANT_NAMES` order; `passed = not failed_invariants`.

Counts by family, signal, and modality count scenarios using the frozen
classification mapping. Abstention-reason counts count accepted attempted
steps containing each of the four emitted reasons. `invariant_counts` has
exactly `INVARIANT_NAMES` as keys and stores failure counts; every value is
zero for a `keep` result. `rejection_count` counts rejected attempts inside a
scenario, while the later `scenario_counts.rejection_cases` counts scenarios
with at least one expected rejection.

All count tuple-maps are dense and use `FAMILY_COUNT_ORDER`,
`SIGNAL_FAMILY_COUNT_ORDER`, `MODALITY_FAMILY_COUNT_ORDER`,
`EMITTED_ABSTENTION_COUNT_ORDER`, and `INVARIANT_NAMES`, respectively.
Classification totals must always equal the three frozen
`EXPECTED_COUNTS_*` mappings because classifications are immutable scenario
authority. Abstention-reason totals always retain the actual emitted counts.
They must equal `EXPECTED_COUNTS_BY_ABSTENTION_REASON` only when
`failed_scenarios == 0`; a negative evaluation may differ and remains valid
aggregate evidence. `passed_scenarios` counts outcomes with `passed=True`;
`failed_scenarios = total_scenarios - passed_scenarios`.
For each invariant,
`invariant_counts[name] = sum(name in outcome.failed_invariants for outcome in
outcomes)`; multiple mismatches inside one scenario therefore count once for
that invariant.

Failure-to-invariant mapping is exact:

- every expected-vs-actual mismatch adds `golden_projection`;
- an expected rejection that instead accepts also adds the case-specific
  invariant from `UNEXPECTED_ACCEPTANCE_SAFETY_INVARIANT_BY_CASE`;
- any rejected attempt whose prior-state bytes change adds
  `rejection_no_mutation`;
- simultaneous-session separate/interleaved mismatch or cross-feed acceptance
  adds `session_isolation`;
- byte replay mismatch adds `deterministic_replay`;
- correction semantic mismatch adds `correction_semantic_replay`;
- output semantic validation failure adds `semantic_output`; and
- aggregate forbidden-key/value leakage adds `privacy_boundary`.

`deterministic_replay_passed` is true exactly when its invariant count is zero.
`privacy_boundary_passed` is true exactly when
`rejection_no_mutation`, `session_isolation`, `semantic_output`, and
`privacy_boundary` all have zero failures. Thus unexpected acceptance of
forbidden or cross-session input can never degrade to a mere `revise`.

Before returning, serialize a privacy-inspection projection containing only
the count maps and booleans (not outcomes) and recursively reject forbidden
key fragments, evidence-reference patterns, recipe identity prefixes, or any
scenario ID. A hit adds `privacy_boundary` exactly once to the first outcome
(`explicit_confusion_entry`), then rebuilds outcome/pass/invariant-count
algebra once before returning. The evaluator performs no file I/O and never
imports the runner or validator.

- [ ] **Step 4: Run GREEN and privacy introspection**

```powershell
python -m unittest scripts.test_emotion_state_003_phase_c0.PhaseCScenarioEvaluationTests -v
python -m unittest scripts.test_emotion_state_003_phase_c0 -v
python -m py_compile scripts/emotion_state_phase_c_contracts.py scripts/emotion_state_phase_c_temporal_tracker.py scripts/test_emotion_state_003_phase_c0.py
python scripts/validate_project_drift_guard.py
git diff --check
```

Then run the exact common post-GREEN ledger. Expected: all 30 scenarios pass
with zero failures; privacy introspection finds no row/state field in the
aggregate dataclass.

- [ ] **Step 5: Independently review and commit**

```powershell
git add -- scripts/emotion_state_phase_c_contracts.py scripts/emotion_state_phase_c_temporal_tracker.py scripts/test_emotion_state_003_phase_c0.py
git diff --cached --check
git commit -m "Evaluate Phase C0 frozen scenarios"
```

### Task 8: Build Aggregate Result, Deterministic Report, And Allowlisted Runner

**Files:**
- Create: `scripts/run_emotion_state_003_phase_c0.py`
- Modify: `scripts/emotion_state_phase_c_contracts.py`
- Modify: `scripts/test_emotion_state_003_phase_c0.py`
- Modify: `docs/thesis/METHODOLOGY_LOG.md`
- Modify:
  `research/experiments/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics.md`

**Interfaces:**
- Consumes: `PhaseCScenarioEvaluationV1`.
- Produces:
  `decide_phase_c_checkpoint(*, failed_scenarios: int,
  invariant_counts: Mapping[str, int],
  deterministic_replay_passed: bool, privacy_boundary_passed: bool,
  claim_or_consumption_flags: Mapping[str, bool]) -> str`,
  `build_phase_c_result(evaluation: PhaseCScenarioEvaluationV1,
  policy_bytes: bytes, scenario_bytes: bytes) -> dict[str, Any]`,
  `validate_phase_c_result_payload(payload: dict[str, Any]) ->
  dict[str, Any]`,
  `render_phase_c_report(result) -> str`,
  `write_phase_c_pair(output_root, result_bytes, report_bytes)`, and CLI modes
  `candidate` and `canonical`.

- [ ] **Step 1: Write failing aggregate/privacy/renderer tests**

```python
class PhaseCAggregateRunnerTests(PhaseCTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        from scripts import emotion_state_phase_c_temporal_tracker
        from scripts import run_emotion_state_003_phase_c0

        cls.tracker = emotion_state_phase_c_temporal_tracker
        cls.runner = run_emotion_state_003_phase_c0
        cls.evaluation = cls.tracker.evaluate_phase_c_scenarios(
            cls.policy,
            cls.scenarios,
        )
        cls.policy_bytes = canonical_json_bytes(cls.raw_policy)
        cls.scenario_bytes = canonical_json_bytes(cls.raw_scenarios)

    def test_result_is_aggregate_only_and_decision_is_keep(self) -> None:
        result = self.runner.build_phase_c_result(self.evaluation, self.policy_bytes, self.scenario_bytes)
        self.assertEqual(result["decision"], "keep")
        self.assertEqual(result["scenario_counts"]["total"], 30)
        self.assertEqual(result["scenario_counts"]["failed"], 0)
        self.assertEqual(result["scenario_counts"]["rejection_cases"], 8)
        self.assertEqual(
            result["complexity"]["numeric_policy_parameter_count"],
            36,
        )
        serialized = canonical_json_bytes(result).decode("utf-8").lower()
        for forbidden in (
            "evidence:uuid:",
            "session:",
            "turn:",
            "event:",
            "campaign:",
            "version:",
            "ind:",
            "case_id",
            "evidence_atoms",
            "accepted_frames",
            "confidence_by_signal",
            "transcript_text",
            "audio_bytes",
        ):
            self.assertNotIn(forbidden, serialized)
        for case_id in EXPECTED_SCENARIO_IDS:
            self.assertNotIn(case_id, serialized)

    def test_report_is_deterministic_and_hash_binds_result(self) -> None:
        result = self.runner.build_phase_c_result(self.evaluation, self.policy_bytes, self.scenario_bytes)
        first = self.runner.render_phase_c_report(result)
        second = self.runner.render_phase_c_report(copy.deepcopy(result))
        self.assertEqual(first, second)
        digest = sha256_bytes(canonical_json_bytes(result))
        self.assertIn(f"result.json sha256:{digest}", first)
        for required in (
            "Scope: synthetic mechanics only; no customer emotion inference or runtime policy enforcement is proven.",
            "Runtime status: not approved and not activated.",
            "Boundary status: no Phase B input, public/private data, provider, call, conversation simulation, or source adaptation was used.",
            "Readiness: production readiness is not proven.",
        ):
            self.assertIn(required, first)

    def test_output_root_is_exactly_allowlisted(self) -> None:
        with self.assertRaisesRegex(self.runner.RunnerError, "output root is not allowlisted"):
            self.runner.resolve_output_root("candidate", ROOT / "outside")

    def test_safety_failure_discards_and_mechanical_failure_revises(self) -> None:
        zero = {name: 0 for name in INVARIANT_NAMES}
        safe_flags = {
            name: False
            for name in CLAIM_OR_CONSUMPTION_FLAG_NAMES
        }
        unsafe = dict(zero)
        unsafe["privacy_boundary"] = 1
        self.assertEqual(
            self.runner.decide_phase_c_checkpoint(
                failed_scenarios=1,
                invariant_counts=unsafe,
                deterministic_replay_passed=True,
                privacy_boundary_passed=False,
                claim_or_consumption_flags=safe_flags,
            ),
            "discard",
        )
        mechanical = dict(zero)
        mechanical["golden_projection"] = 1
        self.assertEqual(
            self.runner.decide_phase_c_checkpoint(
                failed_scenarios=1,
                invariant_counts=mechanical,
                deterministic_replay_passed=True,
                privacy_boundary_passed=True,
                claim_or_consumption_flags=safe_flags,
            ),
            "revise",
        )

    def test_mechanical_negative_evaluation_builds_coherent_revise_pair(self) -> None:
        evaluation = _mechanical_negative_evaluation(self)
        result = self.runner.build_phase_c_result(
            evaluation,
            self.policy_bytes,
            self.scenario_bytes,
        )
        self.runner.validate_phase_c_result_payload(result)
        self.assertEqual(result["scenario_counts"]["failed"], 1)
        self.assertEqual(result["decision"], "revise")
        self.assertEqual(
            result["counts_by_abstention_reason"]["missing_input"],
            EXPECTED_COUNTS_BY_ABSTENTION_REASON["missing_input"] + 1,
        )
        report = self.runner.render_phase_c_report(result)
        self.assertIn("Decision: revise", report)

    def test_semantic_negative_evaluation_builds_coherent_discard_pair(self) -> None:
        evaluation = _semantic_negative_evaluation(self)
        result = self.runner.build_phase_c_result(
            evaluation,
            self.policy_bytes,
            self.scenario_bytes,
        )
        self.runner.validate_phase_c_result_payload(result)
        self.assertEqual(result["invariant_counts"]["semantic_output"], 1)
        self.assertFalse(result["privacy_boundary_passed"])
        self.assertEqual(result["decision"], "discard")
        report = self.runner.render_phase_c_report(result)
        self.assertIn("Decision: discard", report)

    def test_non_json_output_still_builds_coherent_discard_pair(self) -> None:
        evaluation = _structural_semantic_negative_evaluation(self)
        result = self.runner.build_phase_c_result(
            evaluation,
            self.policy_bytes,
            self.scenario_bytes,
        )
        self.runner.validate_phase_c_result_payload(result)
        self.assertEqual(result["scenario_counts"]["failed"], 1)
        self.assertEqual(result["invariant_counts"]["semantic_output"], 1)
        self.assertEqual(result["decision"], "discard")
```

Atomic-writer tests create `TemporaryDirectory(dir=ROOT / ".tmp")`, patch only
the module's `CANDIDATE_ROOT` constant to a fresh child inside that directory,
and remove the test directory on exit; production code has no caller-supplied
allowlist. They prove:

- the final root is created with exactly two LF files and the stage root is
  absent afterward;
- an absent fixed candidate parent is securely created, while a reparse or
  unexpected-child parent rejects;
- an existing final root or stage root fails before a write;
- unexpected, symlinked, junction, or reparse-point parents/children reject
  (mock `lstat` attributes; do not require privileged link creation);
- injected failure before rename cleans only the verified stage root and leaves
  the final root absent; and
- a second call cannot overwrite the first pair.

- [ ] **Step 2: Run RED**

```powershell
python -m unittest scripts.test_emotion_state_003_phase_c0.PhaseCAggregateRunnerTests -v
```

Expected: missing runner module/functions.

- [ ] **Step 3: Implement exact result schema and decision**

`policy_bytes` is
`canonical_json_bytes(validate_phase_c_policy(load_json_strict(POLICY_PATH)))`.
For scenarios, load `raw_scenarios`, call
`validate_phase_c_scenario_payload(raw_scenarios, policy)`, then hash
`canonical_json_bytes(raw_scenarios)`. Neither identity uses
`Path.read_bytes()`, so both remain stable across checkout EOL conversion.

The result top-level fields are exactly:

```python
PHASE_C_RESULT_FIELDS = frozenset({
    "schema_version",
    "checkpoint_id",
    "policy_id",
    "evidence_policy_version",
    "policy_sha256",
    "scenario_sha256",
    "aggregate_output_sha256",
    "scenario_counts",
    "counts_by_family",
    "counts_by_signal",
    "counts_by_modality",
    "counts_by_abstention_reason",
    "invariant_counts",
    "deterministic_replay_passed",
    "privacy_boundary_passed",
    "phase_b_inputs_consumed",
    "public_or_private_data_consumed",
    "runtime_modified_or_activated",
    "provider_or_call_used",
    "policy_enforcement_proven",
    "emotion_accuracy_proven",
    "production_readiness_proven",
    "complexity",
    "decision",
})
```

Exact identities are:

```python
schema_version = "EmotionStatePhaseC0AggregateResultV1"
checkpoint_id = "EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics"
policy_id = "emotion-state-phase-c0-synthetic-v1"
evidence_policy_version = "emotion-state-evidence-v2"
```

Nested shapes are exact:

```python
scenario_counts = {
    "total": 30,
    "passed": evaluation.passed_scenarios,
    "failed": evaluation.failed_scenarios,
    "rejection_cases": len(REJECTION_CASE_IDS),
}

complexity = {
    "numeric_policy_parameter_count": 36,
    "scenario_count": 30,
    "operational_signal_count": 5,
    "synthetic_evidence_class_count": 5,
    "runtime_files_modified": 0,
}
```

`numeric_policy_parameter_count` recursively counts only leaves for which
`type(value) is int`; booleans do not count.
The four `counts_by_*` objects use every frozen category key, including
zero-valued categories, in canonical JSON key order. `invariant_counts` uses
exactly `INVARIANT_NAMES`; no arbitrary metric key is accepted.
Family/signal/modality counts always equal their frozen classification totals.
Abstention-reason values are exact nonnegative integers copied from the actual
evaluation. They equal `EXPECTED_COUNTS_BY_ABSTENTION_REASON` only when
`evaluation.failed_scenarios == 0`; negative evaluations keep their actual
reason counts and remain serializable as `revise`/`discard` evidence.

`build_phase_c_result` first validates all evaluation scalar types, tuple-map
orders, count algebra, outcome order/classifications, and the two replay/
privacy booleans. It parses `policy_bytes` and `scenario_bytes` with the strict
duplicate-key/nonfinite loader from in-memory text, validates them, and
requires their canonical reserialization to equal the supplied bytes. It then
constructs this mapping in memory:

```python
decision = decide_phase_c_checkpoint(
    failed_scenarios=evaluation.failed_scenarios,
    invariant_counts=dict(evaluation.invariant_counts),
    deterministic_replay_passed=evaluation.deterministic_replay_passed,
    privacy_boundary_passed=evaluation.privacy_boundary_passed,
    claim_or_consumption_flags={
        name: False for name in CLAIM_OR_CONSUMPTION_FLAG_NAMES
    },
)
result_without_aggregate_digest = {
    "schema_version": "EmotionStatePhaseC0AggregateResultV1",
    "checkpoint_id": "EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics",
    "policy_id": "emotion-state-phase-c0-synthetic-v1",
    "evidence_policy_version": "emotion-state-evidence-v2",
    "policy_sha256": sha256_bytes(policy_bytes),
    "scenario_sha256": sha256_bytes(scenario_bytes),
    "scenario_counts": scenario_counts,
    "counts_by_family": dict(evaluation.counts_by_family),
    "counts_by_signal": dict(evaluation.counts_by_signal),
    "counts_by_modality": dict(evaluation.counts_by_modality),
    "counts_by_abstention_reason": dict(
        evaluation.counts_by_abstention_reason
    ),
    "invariant_counts": dict(evaluation.invariant_counts),
    "deterministic_replay_passed": evaluation.deterministic_replay_passed,
    "privacy_boundary_passed": evaluation.privacy_boundary_passed,
    "phase_b_inputs_consumed": False,
    "public_or_private_data_consumed": False,
    "runtime_modified_or_activated": False,
    "provider_or_call_used": False,
    "policy_enforcement_proven": False,
    "emotion_accuracy_proven": False,
    "production_readiness_proven": False,
    "complexity": complexity,
    "decision": decision,
}
result = {
    **result_without_aggregate_digest,
    "aggregate_output_sha256": sha256_bytes(
        canonical_json_bytes(result_without_aggregate_digest)
    ),
}
```

The illustrative construction shows values, not Python insertion order;
canonical JSON sorting is the byte authority.

Decision logic:

```python
claim_or_consumption_boundary_failed = any(
    claim_or_consumption_flags[field]
    for field in (
        "phase_b_inputs_consumed",
        "public_or_private_data_consumed",
        "runtime_modified_or_activated",
        "provider_or_call_used",
        "policy_enforcement_proven",
        "emotion_accuracy_proven",
        "production_readiness_proven",
    )
)
safety_invariant_failed = any(
    invariant_counts[name] > 0
    for name in SAFETY_INVARIANT_NAMES
)
if (
    claim_or_consumption_boundary_failed
    or safety_invariant_failed
    or not deterministic_replay_passed
    or not privacy_boundary_passed
):
    decision = "discard"
elif failed_scenarios:
    decision = "revise"
else:
    decision = "keep"
```

Before branching, `decide_phase_c_checkpoint` requires
`type(failed_scenarios) is int >= 0`; exact `INVARIANT_NAMES` keys with
nonnegative exact-int values; exact bool replay/privacy flags; and exact
`CLAIM_OR_CONSUMPTION_FLAG_NAMES` keys with exact bool values. Shape/type
failure raises `RunnerError("decision_inputs")`.

All seven claim/consumption booleans in the result are `false`.
Separately, `deterministic_replay_passed` and `privacy_boundary_passed` must be
`true` for `keep`.

`aggregate_output_sha256` is the SHA-256 of canonical JSON for the complete
result mapping with only `aggregate_output_sha256` omitted. The report's
`result.json sha256:` marker is the SHA-256 of the final canonical result bytes
including that aggregate digest.

The producer-side `validate_phase_c_result_payload` checks the exact field/
nested schemas, scalar types, count and replay/privacy algebra, decision,
forbidden aggregate content, complexity, and selfless digest before
`build_phase_c_result` returns and before rendering/writing. It is not the
Task 9 independent validator and Task 9 may not import it.

- [ ] **Step 4: Implement deterministic report and allowlisted writes**

The renderer validates the result contract, computes the final canonical
result-byte SHA-256, and returns exactly this LF-joined template with one final
LF. Compact mappings use
`json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
allow_nan=False)` and booleans use lowercase JSON spelling:

```text
# EMOTION-STATE-003 Phase C0 Synthetic Temporal Mechanics

- Checkpoint: EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics
- Decision: <decision>
- Result schema: EmotionStatePhaseC0AggregateResultV1
- Policy SHA-256: <policy_sha256>
- Scenario SHA-256: <scenario_sha256>
- Aggregate-output SHA-256: <aggregate_output_sha256>
- result.json sha256:<final_result_bytes_sha256>

## Aggregate

- Scenario counts: <compact scenario_counts>
- Counts by family: <compact counts_by_family>
- Counts by signal family: <compact counts_by_signal>
- Counts by modality family: <compact counts_by_modality>
- Counts by abstention reason: <compact counts_by_abstention_reason>
- Invariant counts: <compact invariant_counts>
- Deterministic replay passed: <true|false>
- Privacy boundary passed: <true|false>

## Complexity

- Numeric policy parameters: <numeric_policy_parameter_count>
- Scenarios: <scenario_count>
- Operational signals: <operational_signal_count>
- Synthetic evidence classes: <synthetic_evidence_class_count>
- Runtime files modified: <runtime_files_modified>

## Interpretation

Scope: synthetic mechanics only; no customer emotion inference or runtime policy enforcement is proven.
Runtime status: not approved and not activated.
Boundary status: no Phase B input, public/private data, provider, call, conversation simulation, or source adaptation was used.
Readiness: production readiness is not proven.
```

No blank line follows the final readiness line except the single terminal LF.
No case ID, fixture identity, reference, state, row, or transcript appears.

Candidate root is exactly:

```text
.tmp/emotion-state-003-phase-c0/candidate
```

Canonical root is exactly:

```text
research/experiments/generated/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics
```

Before writing, require both the final root and its one exact `.stage` sibling
to be absent. For candidate mode only, securely create the one fixed Phase C0
parent if absent; for canonical mode, its tracked
`research/experiments/generated` parent must already exist. Reject any
symlink, junction, or reparse point in the allowlisted parent chain and reject
unexpected children in the Phase C0 parent. Create the stage directory, write
exactly `result.json` and `report.md` as LF bytes, verify their exact
bytes/hashes and child set, then rename the complete directory to the final
root in one same-volume operation. On handled failure, remove only the
verified exact stage root and leave the final root absent. An empty Phase C0
parent created by the failed run may remain. Never overwrite or repair an
existing candidate/canonical root. Do not copy Phase B's publication state
machine or touch its `.tmp` root.

`resolve_output_root(mode, requested_root=None)` accepts only exact strings
`candidate` and `canonical`. It selects the module constant; a non-`None`
test-only requested root must be byte-for-byte equal after separator
normalization to that constant and must contain no `.` or `..` path segment.
It uses lexical `abspath/normpath`, never `Path.resolve`, and requires the
result to remain under the fixed project root.

The no-follow checker walks the project root and every target ancestor with
`os.lstat`; it rejects a symlink, non-directory ancestor, or Windows
`FILE_ATTRIBUTE_REPARSE_POINT`. Candidate mode creates only the absent fixed
`.tmp/emotion-state-003-phase-c0` parent after its existing ancestors pass,
then re-`lstat`s it. That candidate parent must otherwise be empty before a
run. Canonical mode does not enumerate the shared generated parent; it checks
only the fixed final/stage names and their ancestor metadata.

`write_phase_c_pair` requires exact canonical result bytes and UTF-8 LF report
bytes, verifies the report marker against result bytes, creates the stage with
an exclusive single-directory `mkdir`, writes each file with exclusive create,
flush, and `fsync`, then `lstat`s/re-reads both regular non-reparse files and
requires exact child set/bytes. It calls `os.rename(stage, final)` only while
final is absent, then repeats exact metadata/child/byte verification. It never
uses a recursive filesystem helper. On a handled failure before rename, it
revalidates the exact stage identity and exact allowlisted child names, unlinks
only those regular files, and removes only the empty stage directory. Failure
codes are:

```text
runner_mode
output_root_not_allowlisted
output_path_escape
output_reparse_or_link
output_ancestor_type
output_parent_children
output_exists
stage_exists
result_bytes_invalid
report_bytes_invalid
stage_write_failed
stage_readback_failed
atomic_rename_failed
final_readback_failed
```

The CLI accepts exactly one positional mode and no optional output root. It
strict-loads and validates policy/scenarios, evaluates all scenarios in
memory, builds result/report bytes twice and requires equality, then calls the
writer once. It prints only mode, decision, and the two final SHA-256 values;
no state/case/reference data.

- [ ] **Step 5: Run GREEN and complete module**

```powershell
python -m unittest scripts.test_emotion_state_003_phase_c0.PhaseCAggregateRunnerTests -v
python -m unittest scripts.test_emotion_state_003_phase_c0 -v
python -m py_compile scripts/emotion_state_phase_c_contracts.py scripts/emotion_state_phase_c_temporal_tracker.py scripts/run_emotion_state_003_phase_c0.py scripts/test_emotion_state_003_phase_c0.py
python scripts/check_thesis_reference_registry.py
python scripts/validate_project_drift_guard.py
python scripts/validate_context_reading_policy.py
python scripts/validate_check_setup.py
git diff --check
```

Then run the exact common post-GREEN ledger. Expected: complete Phase C0
module passes; no output pair is produced by tests outside temporary test
directories.

- [ ] **Step 6: Independently review and commit**

Before review, add a working-draft methodology entry that records Tasks 1-8
implementation as complete, independent review as pending, candidate as not
created, and every current claim/boundary restriction. The reviewer inspects
the complete Task 8 code, tests, protocol, and methodology diff and must return
`C0/I0/M0`.

After that verdict, set the protocol status to exactly:

```markdown
Tasks 1-8 implementation complete and independently reviewed. Candidate not
created. Candidate, canonical, push, runtime, provider, data, call, and Phase D
gates remain closed pending separate explicit authorization.
```

Replace only the methodology entry's pending-review statement with the real
review verdict. The same reviewer rechecks those final protocol/methodology
bytes before commit. Then run:

```powershell
python scripts/check_thesis_update_gate.py
python scripts/check_thesis_reference_registry.py
python scripts/validate_project_drift_guard.py
python scripts/validate_context_reading_policy.py
python scripts/validate_check_setup.py
git diff --check
```

```powershell
git add -- docs/thesis/METHODOLOGY_LOG.md research/experiments/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics.md scripts/emotion_state_phase_c_contracts.py scripts/run_emotion_state_003_phase_c0.py scripts/test_emotion_state_003_phase_c0.py
git diff --cached --check
git commit -m "Build Phase C0 aggregate runner"
```

### Task 9: Add Independent Validator And Produce One Ignored Candidate

**Files:**
- Create: `scripts/validate_emotion_state_003_phase_c0.py`
- Modify: `scripts/test_emotion_state_003_phase_c0.py`
- Modify: `docs/thesis/METHODOLOGY_LOG.md`
- Modify:
  `research/experiments/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics.md`
- Create ignored:
  `.tmp/emotion-state-003-phase-c0/candidate/result.json`
- Create ignored:
  `.tmp/emotion-state-003-phase-c0/candidate/report.md`

**Interfaces:**
- Consumes: tracked policy/scenarios and candidate aggregate pair.
- Produces validator sections:
  `contracts`, `scenarios`, `synthetic`, `candidate --root`, and `checkpoint`,
  `build_fresh_evaluation_projection(policy, scenarios) -> dict[str, Any]`,
  `validate_candidate_payload(payload, fresh_evaluation_projection)`,
  `validate_pair_bytes(result_bytes, report_bytes,
  fresh_evaluation_projection)`,
  plus `read_allowlisted_pair(section, requested_root=None) ->
  tuple[bytes, bytes]`.

- [ ] **Step 1: Write failing validator and mutation tests**

```python
class PhaseCIndependentValidatorTests(PhaseCTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        from scripts import emotion_state_phase_c_temporal_tracker
        from scripts import run_emotion_state_003_phase_c0
        from scripts import validate_emotion_state_003_phase_c0

        cls.tracker = emotion_state_phase_c_temporal_tracker
        cls.runner = run_emotion_state_003_phase_c0
        cls.validator = validate_emotion_state_003_phase_c0
        evaluation = cls.tracker.evaluate_phase_c_scenarios(
            cls.policy,
            cls.scenarios,
        )
        cls.valid_result_payload = cls.runner.build_phase_c_result(
            evaluation,
            canonical_json_bytes(cls.raw_policy),
            canonical_json_bytes(cls.raw_scenarios),
        )
        cls.fresh_evaluation_projection = (
            cls.validator.build_fresh_evaluation_projection(
                cls.policy,
                cls.scenarios,
            )
        )

    def run_validator(self, section: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "validate_emotion_state_003_phase_c0.py"),
                section,
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def valid_result(self) -> dict[str, Any]:
        return copy.deepcopy(self.valid_result_payload)

    def result_mutations(
        self,
        result: dict[str, Any],
    ) -> list[tuple[str, dict[str, Any], str]]:
        return build_result_contract_mutations(result)

    def test_validator_sections_pass_on_fixtures(self) -> None:
        for section in ("contracts", "scenarios", "synthetic"):
            completed = self.run_validator(section)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_every_result_scalar_and_mapping_shape_mutation_rejects(self) -> None:
        result = self.valid_result()
        for name, payload, expected_code in self.result_mutations(result):
            with self.subTest(mutation=name):
                with self.assertRaisesRegex(
                    self.validator.ValidationError,
                    expected_code,
                ):
                    self.validator.validate_candidate_payload(
                        payload,
                        self.fresh_evaluation_projection,
                    )

    def test_renderer_equality_cannot_mask_semantic_contradiction(self) -> None:
        result = self.valid_result()
        result["decision"] = "keep"
        result["scenario_counts"]["passed"] = 29
        result["scenario_counts"]["failed"] = 1
        result["invariant_counts"]["golden_projection"] = 1
        aggregate_core = {
            key: value
            for key, value in result.items()
            if key != "aggregate_output_sha256"
        }
        result["aggregate_output_sha256"] = sha256_bytes(
            canonical_json_bytes(aggregate_core)
        )
        report = render_report_fixture_without_semantic_validation(result)
        with self.assertRaisesRegex(
            self.validator.ValidationError,
            "result_decision_semantics",
        ):
            self.validator.validate_pair_bytes(
                canonical_json_bytes(result),
                report.encode("utf-8"),
                self.fresh_evaluation_projection,
            )

    def test_coherent_pair_mutation_cannot_diverge_from_fresh_evaluation(self) -> None:
        result = self.valid_result()
        result["scenario_counts"]["passed"] = 29
        result["scenario_counts"]["failed"] = 1
        result["invariant_counts"]["golden_projection"] = 1
        result["decision"] = "revise"
        aggregate_core = {
            key: value
            for key, value in result.items()
            if key != "aggregate_output_sha256"
        }
        result["aggregate_output_sha256"] = sha256_bytes(
            canonical_json_bytes(aggregate_core)
        )
        report = render_report_fixture_without_semantic_validation(result)
        with self.assertRaisesRegex(
            self.validator.ValidationError,
            "result_evaluation_binding",
        ):
            self.validator.validate_pair_bytes(
                canonical_json_bytes(result),
                report.encode("utf-8"),
                self.fresh_evaluation_projection,
            )

    def test_actual_negative_evaluation_pair_validates_as_revise(self) -> None:
        evaluation = _mechanical_negative_evaluation(self)
        result = self.runner.build_phase_c_result(
            evaluation,
            canonical_json_bytes(self.raw_policy),
            canonical_json_bytes(self.raw_scenarios),
        )
        report = self.runner.render_phase_c_report(result).encode("utf-8")
        with mock.patch.object(
            self.tracker,
            "evaluate_phase_c_scenarios",
            return_value=evaluation,
        ):
            fresh = self.validator.build_fresh_evaluation_projection(
                self.policy,
                self.scenarios,
            )
        self.validator.validate_pair_bytes(
            canonical_json_bytes(result),
            report,
            fresh,
        )
        self.assertEqual(result["decision"], "revise")
        self.assertEqual(result["scenario_counts"]["failed"], 1)

    def test_actual_semantic_negative_pair_validates_as_discard(self) -> None:
        evaluation = _semantic_negative_evaluation(self)
        result = self.runner.build_phase_c_result(
            evaluation,
            canonical_json_bytes(self.raw_policy),
            canonical_json_bytes(self.raw_scenarios),
        )
        report = self.runner.render_phase_c_report(result).encode("utf-8")
        with mock.patch.object(
            self.tracker,
            "evaluate_phase_c_scenarios",
            return_value=evaluation,
        ):
            fresh = self.validator.build_fresh_evaluation_projection(
                self.policy,
                self.scenarios,
            )
        self.validator.validate_pair_bytes(
            canonical_json_bytes(result),
            report,
            fresh,
        )
        self.assertEqual(result["invariant_counts"]["semantic_output"], 1)
        self.assertEqual(result["decision"], "discard")
```

Before RED, add:

- report mutations that delete/alter each scope line, corrupt the result-hash
  marker, introduce CRLF, remove/add terminal LFs, and change every rendered
  aggregate/complexity value;
- root-reader tests for outside root, `.`/`..` lexical alias, missing root,
  mocked reparse ancestor/root/file, wrong file type, unexpected child, and
  metadata change across read; every case asserts neither pair file content is
  opened before path/child validation completes;
- CLI arity/section/root tests; and
- an AST independence test that rejects any import of
  `run_emotion_state_003_phase_c0` and any validator load/call of
  `PHASE_C_RESULT_FIELDS`, `decide_phase_c_checkpoint`,
  `build_phase_c_result`, `validate_phase_c_result_payload`,
  `compute_aggregate_output_sha256`,
  `render_phase_c_report`, or `write_phase_c_pair`.
  The AST walk checks imported module/name origins before aliasing and all
  `Name`/`Attribute` loads/calls, so `as` aliases cannot bypass it.

`build_result_contract_mutations` returns, in stable name order:

- one missing-top-level-field mutation for every exact result field;
- one extra-top-level-field mutation;
- one wrong-exact-type mutation for every scalar/boolean field;
- for every aggregate mapping, one missing-key, one extra-key, one wrong-value,
  and one wrong-container-type mutation;
- one wrong policy hash, scenario hash, and aggregate-output hash mutation;
- every decision/failed-count/safety-boolean contradiction; and
- one forbidden nested key and one forbidden nested value mutation.

The mutation helper is test code only and never imports the validator's field
sets or decision function. Each tuple includes the expected semantic validation
code. After every mutation except missing/wrong
`aggregate_output_sha256`, the helper recomputes the selfless aggregate digest;
therefore field, type, algebra, boundary, and decision mutations cannot pass
merely because the digest is stale. Pair-level mutations also regenerate
deterministic report bytes with the test-owned literal
`render_report_fixture_without_semantic_validation` unless report/hash binding
is the target. That helper duplicates the Task 8 template but imports neither
producer nor validator render/field/decision helpers, allowing it to construct
a byte-consistent semantically invalid pair for negative testing.

- [ ] **Step 2: Run RED**

```powershell
python -m unittest scripts.test_emotion_state_003_phase_c0.PhaseCIndependentValidatorTests -v
```

Expected: missing validator module/CLI.

- [ ] **Step 3: Implement independent semantic validation**

The validator may import only generic strict JSON/hash helpers, frozen input
parsers/types, and the temporal tracker for the `synthetic` rerun. It must not
import the runner module or any producer result-field, decision, digest,
report, path, or writer helper. It defines its own literal
`VALIDATOR_RESULT_FIELDS`, category orders, exact identities, report template,
decision implementation, and result schemas. The AST test above enforces this
boundary.

It independently recomputes:

- exact result field set and types;
- all aggregate totals/algebra;
- policy and scenario hashes;
- aggregate-output digest;
- decision semantics;
- forbidden key fragments and values recursively;
- all boundary booleans;
- exact result/report hash marker;
- deterministic report equality; and
- the exact four scope/non-claim lines independently of renderer equality;
- exact binding from the pair's evaluation-derived aggregate fields to a
  fresh deterministic synthetic rerun; and
- candidate/canonical root child set.

`build_fresh_evaluation_projection` runs the tracked temporal evaluator twice
over the independently validated policy/scenario objects, projects only these
exact aggregate fields from each run, and requires canonical byte equality:

```python
{
    "scenario_counts": {
        "total": 30,
        "passed": evaluation.passed_scenarios,
        "failed": evaluation.failed_scenarios,
        "rejection_cases": len(REJECTION_CASE_IDS),
    },
    "counts_by_family": dict(evaluation.counts_by_family),
    "counts_by_signal": dict(evaluation.counts_by_signal),
    "counts_by_modality": dict(evaluation.counts_by_modality),
    "counts_by_abstention_reason": dict(
        evaluation.counts_by_abstention_reason
    ),
    "invariant_counts": dict(evaluation.invariant_counts),
    "deterministic_replay_passed": (
        evaluation.deterministic_replay_passed
    ),
    "privacy_boundary_passed": evaluation.privacy_boundary_passed,
    "decision": locally_derive_decision_from_evaluation(evaluation),
}
```

This projection is in-memory and aggregate-only. The builder imports neither
the runner nor producer result/decision helpers. It validates exact shape,
types, count algebra, and outcome count/order before returning; its golden
abstention-total equality check is conditional on zero failed scenarios. A
failing scenario or invariant is a valid deterministic projection whose local
decision may be `revise` or `discard`; the `synthetic` section does not
silently require `keep`. The local decision branch supplies exact `False` for
all seven frozen claim/consumption flags and otherwise uses the same
failed-scenario, safety-invariant, replay, and privacy inputs shown in Task 8.

`validate_candidate_payload` executes this exact precedence:

```text
result_not_object
result_field_set
result_scalar_type
result_identity
result_nested_shape
result_count_algebra
result_policy_hash
result_scenario_hash
result_boundary_flags
result_replay_privacy_algebra
result_decision_semantics
result_evaluation_binding
result_complexity
result_forbidden_content
result_aggregate_digest
```

Its own literal nested schemas require:

- `scenario_counts`: exactly `total`, `passed`, `failed`,
  `rejection_cases`, all exact nonnegative ints, total `30`,
  passed+failed=total, rejection cases `8`;
- family/signal/modality maps: exact frozen category keys and counts derived
  by independently iterating strictly parsed scenario classifications;
- abstention map: exact emitted-reason keys with nonnegative exact-int actual
  evaluation counts; require equality to counts independently derived from
  golden `expected_output_bytes` only when `scenario_counts.failed == 0`, and
  otherwise require exact equality to the fresh-evaluation projection;
- invariant map: exact `INVARIANT_NAMES`, nonnegative exact ints;
- complexity: exactly five frozen keys/values, with policy numeric leaves
  recounted independently and booleans excluded;
- seven claim/consumption fields: exact bool and false;
- deterministic replay/privacy booleans: exact bool and equal their invariant
  algebra; and
- uppercase 64-hex hashes.

The validator hashes canonical validated policy/scenario objects, not checkout
raw bytes. It recomputes decision with a locally written branch identical to
the frozen rule. It recursively scans every key/value and rejects privacy
fragments, evidence UUIDs, scenario IDs, and `session:`/`turn:`/`event:`/
`campaign:`/`version:` identities. It recomputes the selfless aggregate digest
by removing only `aggregate_output_sha256`.

`validate_candidate_payload` requires a fresh-evaluation projection argument;
there is no default or unbound validation path. After local decision semantics
pass, it compares every projection field byte-semantically to the corresponding
result field and raises `ValidationError("result_evaluation_binding")` on the
first mismatch. `validate_pair_bytes` requires and forwards the same projection.

`validate_pair_bytes` strict-decodes result as unique-key finite JSON and
report as UTF-8. It requires LF only and exactly one terminal LF. It validates
result first, then checks the four scope lines in exact order
(`report_scope_boundary`), the exact result marker
(`report_result_hash_binding`), and finally equality to
`render_expected_report_independently(result)` (`report_determinism`). The
independent renderer duplicates the complete Task 8 literal template and
compact-map rules; it does not call or import the producer renderer.

For `candidate --root`, normalize the lexical absolute path without following
links and require equality to the one fixed candidate root before reading any
child. Then `lstat` every parent/root/file, reject symlink/junction/reparse
points, require a real directory plus exactly two regular files, and only then
read the pair. `checkpoint` applies the same no-follow checks to the fixed
canonical root. Focused tests pass an outside root, a lexical alias, a mocked
reparse parent/root/file, and an unexpected child; each must reject before
`result.json` or `report.md` content is opened.

The reader rejects any raw `.`/`..` segment before normalization. It lexical
`abspath/normpath`s and case-normalizes only for equality; it never resolves
links. It `lstat`s project root through target root, checks real
non-reparse directories, enumerates the root once, requires exact child names,
then `lstat`s both regular non-reparse files. It opens each with read-only
binary handles, compares `fstat` identity/type to the pre-open metadata, reads
bounded bytes (result `<=65536`, report `<=65536`), and repeats `fstat` after
read. Any identity/size/mtime change is `root_changed_during_read`. This is a
stable-workspace fail-closed check, not descriptor-bound hostile-filesystem
isolation.

CLI sections are exact:

- `contracts`: strict-validate canonical policy and print `contracts:pass`;
- `scenarios`: strict-validate the 30 recipe/expectation matrix and print
  `scenarios:pass`;
- `synthetic`: independently validate inputs, build the byte-identical
  two-run fresh-evaluation projection, validate its shape/algebra, and print
  `synthetic:pass` regardless of whether its derived decision is `keep`,
  `revise`, or `discard`;
- `candidate --root <exact-relative-root>`: run the prior three checks, retain
  the fresh projection from `synthetic`, read the fixed candidate pair,
  validate it against that exact projection, and print `candidate:pass`;
- `checkpoint`: run the prior three checks, retain the fresh projection from
  `synthetic`, read the fixed canonical pair, validate it against that exact
  projection, and print `checkpoint:pass`.

All failures print only `<section>:fail:<stable-code>` to stderr and exit `1`.
Wrong arity/section exits `2`. No success/failure output contains a path,
scenario ID, reference, state, payload, or report content.

It must never read Phase B ignored state, Phase B result internals, datasets,
private data, providers, or runtime state.

- [ ] **Step 4: Run GREEN and commit validator code before candidate**

```powershell
python -m unittest scripts.test_emotion_state_003_phase_c0.PhaseCIndependentValidatorTests -v
python -m unittest scripts.test_emotion_state_003_phase_c0 -v
python scripts/validate_emotion_state_003_phase_c0.py contracts
python scripts/validate_emotion_state_003_phase_c0.py scenarios
python scripts/validate_emotion_state_003_phase_c0.py synthetic
python -m py_compile scripts/emotion_state_phase_c_contracts.py scripts/emotion_state_phase_c_temporal_tracker.py scripts/run_emotion_state_003_phase_c0.py scripts/validate_emotion_state_003_phase_c0.py scripts/test_emotion_state_003_phase_c0.py
python scripts/check_thesis_reference_registry.py
python scripts/validate_project_drift_guard.py
python scripts/validate_context_reading_policy.py
python scripts/validate_check_setup.py
git diff --check
```

Then run the exact common post-GREEN ledger. Expected: every command passes.

Before review, add a working-draft methodology entry that records the
independent validator implementation as complete, validator review as pending,
candidate as not created, and all claim/boundary restrictions. An independent
reviewer must inspect the validator specification, code, tests, AST
independence rule, fresh-evaluation binding, path reader, CLI, protocol, and
methodology diff before any candidate is generated. Require `C0/I0/M0`; any
finding returns to focused RED/GREEN, the common ledger, and re-review.

Only after that verdict, set protocol status to exactly:

```markdown
Tasks 1-8 implementation and independent validator complete and independently
reviewed. Candidate authorization is open; candidate not yet created.
Canonical, push, runtime, provider, data, call, and Phase D gates remain
closed.
```

Replace only the methodology entry's pending-review statement with the real
validator-review verdict. The same reviewer rechecks those final
protocol/methodology bytes. Then run:

```powershell
python scripts/check_thesis_update_gate.py
python scripts/check_thesis_reference_registry.py
python scripts/validate_project_drift_guard.py
python scripts/validate_context_reading_policy.py
python scripts/validate_check_setup.py
git diff --check
```

```powershell
git add -- docs/thesis/METHODOLOGY_LOG.md research/experiments/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics.md scripts/validate_emotion_state_003_phase_c0.py scripts/test_emotion_state_003_phase_c0.py
git diff --cached --check
git commit -m "Validate Phase C0 aggregate checkpoint"
```

- [ ] **Step 5: Produce exactly one ignored candidate**

```powershell
python scripts/run_emotion_state_003_phase_c0.py candidate
python scripts/validate_emotion_state_003_phase_c0.py candidate --root .tmp/emotion-state-003-phase-c0/candidate
```

Expected:

- candidate root contains exactly `result.json` and `report.md`;
- validator exits `0`;
- decision is one of `keep`, `revise`, or `discard`;
- no tracked file changes.

- [ ] **Step 6: Independently review candidate and stop**

The reviewer reads only aggregate candidate bytes, tracked policy/scenario
contracts, and validator code. It independently recomputes counts, hashes,
decision, and non-claims. Require `C0/I0/M0`.

- [ ] **Step 7: Record the accepted candidate transaction**

After and only after the passing review, update the protocol status to exactly:

```markdown
Candidate independently validated and accepted for canonical review. Canonical
publication requires separate explicit authorization; push, runtime, provider,
data, call, and Phase D gates remain closed.
```

In the same status section record the real candidate result SHA-256, report
SHA-256, decision, validator implementation commit ID, and independent
`C0/I0/M0` verdict. Use real values only; no placeholder is permitted.

```powershell
git add -- research/experiments/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics.md
git diff --cached --name-only
git diff --cached --check
git commit -m "Accept Phase C0 candidate checkpoint"
```

Expected cached path set: exactly the protocol document. Candidate bytes
remain ignored and unchanged.

- [ ] **Step 8: Revalidate candidate and stop before canonical**

```powershell
python scripts/validate_emotion_state_003_phase_c0.py candidate --root .tmp/emotion-state-003-phase-c0/candidate
git status -sb
git log -8 --oneline
```

Expected: candidate passes, tracked worktree is clean, ignored pair remains
exactly two files, and local commits are ahead. Stop before canonical
publication unless the canonical gate is separately authorized.

### Task 10: Publish The Exact Canonical Pair And Close The Checkpoint

**Files:**
- Create:
  `research/experiments/generated/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics/result.json`
- Create:
  `research/experiments/generated/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics/report.md`
- Modify: `docs/product/CHECKPOINT_INDEX.md`
- Modify: `docs/product/COMMANDS.md`
- Modify: `docs/thesis/METHODOLOGY_LOG.md`
- Modify: `docs/thesis/ROADMAP.md`
- Modify:
  `research/experiments/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics.md`
- Modify: `scripts/test_emotion_state_003_phase_c0.py`

**Interfaces:**
- Consumes: independently accepted candidate.
- Produces: exact aggregate canonical pair, checkpoint validation, thesis
  traceability, and a clean local branch.

- [ ] **Step 1: Prove candidate and canonical bytes will match**

Add this focused promotion test. `read_allowlisted_pair` is the Task 9
validator's fixed-root/no-follow reader; the runner has no candidate reader.

```python
class PhaseCCandidatePromotionTests(PhaseCTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        from scripts import emotion_state_phase_c_temporal_tracker
        from scripts import run_emotion_state_003_phase_c0
        from scripts import validate_emotion_state_003_phase_c0

        cls.tracker = emotion_state_phase_c_temporal_tracker
        cls.runner = run_emotion_state_003_phase_c0
        cls.validator = validate_emotion_state_003_phase_c0

    def test_accepted_candidate_equals_two_fresh_in_memory_renders(self) -> None:
        candidate_result, candidate_report = (
            self.validator.read_allowlisted_pair(
                section="candidate",
                requested_root=(
                    ROOT / ".tmp" / "emotion-state-003-phase-c0" / "candidate"
                ),
            )
        )
        renders = []
        for _ in range(2):
            evaluation = self.tracker.evaluate_phase_c_scenarios(
                self.policy,
                self.scenarios,
            )
            result = self.runner.build_phase_c_result(
                evaluation,
                canonical_json_bytes(self.raw_policy),
                canonical_json_bytes(self.raw_scenarios),
            )
            result_bytes = canonical_json_bytes(result)
            report_bytes = self.runner.render_phase_c_report(result).encode("utf-8")
            renders.append((result_bytes, report_bytes))
        self.assertEqual(renders[0], renders[1])
        self.assertEqual(
            sha256_bytes(candidate_result),
            sha256_bytes(renders[0][0]),
        )
        self.assertEqual(
            sha256_bytes(candidate_result),
            sha256_bytes(renders[1][0]),
        )
        self.assertEqual(
            sha256_bytes(candidate_report),
            sha256_bytes(renders[0][1]),
        )
        self.assertEqual(
            sha256_bytes(candidate_report),
            sha256_bytes(renders[1][1]),
        )
```

Run:

```powershell
python -m unittest scripts.test_emotion_state_003_phase_c0.PhaseCCandidatePromotionTests -v
```

Do not write canonical files during this step.

Expected: the focused test passes and all four candidate-to-render SHA-256
comparisons match.

- [ ] **Step 2: Write the failing documentation/checkpoint contract test**

The test must require:

- exact protocol status `Canonical Phase C0 synthetic mechanics checkpoint
  accepted.`;
- exact decision and hashes;
- C0 scope/non-claims;
- closed Phase B lockbox;
- no runtime/provider/data/Phase D authority;
- canonical directory exactly two files; and
- no runnable command for Phase B lockbox reuse.

Run:

```powershell
python -m unittest scripts.test_emotion_state_003_phase_c0.PhaseCCloseoutContractTests -v
```

Expected: RED because canonical pair and closeout text do not exist.

- [ ] **Step 3: Publish the exact deterministic pair**

```powershell
python scripts/run_emotion_state_003_phase_c0.py canonical
python scripts/validate_emotion_state_003_phase_c0.py checkpoint
```

Expected: canonical root contains exactly the pair; hashes match the reviewed
candidate; checkpoint validator exits `0`.

- [ ] **Step 4: Update closeout documentation**

Record exact:

- policy/scenario/result/report hashes;
- scenario totals and decision;
- independent C/I/M verdict;
- test and repository gate counts;
- implementation/validator and candidate-acceptance commit IDs that already
  exist;
- synthetic mechanics-only interpretation; and
- unchanged private/provider/call/runtime/Phase D boundaries.

Set the protocol's first status sentence to exactly:

```markdown
Canonical Phase C0 synthetic mechanics checkpoint accepted.
```

Follow it with the real decision/hashes/commit trace and the unchanged
scope/non-claim boundary. The word `accepted` refers only to this offline
synthetic mechanics checkpoint.

Do not claim emotion accuracy, customer internal state, policy enforcement,
conversion improvement, real-call performance, or production readiness.
Do not insert a placeholder pair commit ID; that commit does not exist until
Step 6.

- [ ] **Step 5: Run the complete guarded ledger**

```powershell
python -m unittest scripts.test_emotion_state_003_phase_c0 -v
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe -m unittest scripts.test_emotion_state_002_phase_b.PhaseBContractTests -v
python scripts/validate_emotion_state_003_phase_c0.py contracts
python scripts/validate_emotion_state_003_phase_c0.py scenarios
python scripts/validate_emotion_state_003_phase_c0.py synthetic
python scripts/validate_emotion_state_003_phase_c0.py checkpoint
python scripts/check_thesis_update_gate.py
python scripts/check_thesis_reference_registry.py
python scripts/validate_project_drift_guard.py
python scripts/validate_context_reading_policy.py
python scripts/validate_check_setup.py
git check-attr text eol -- research/experiments/generated/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics/result.json research/experiments/generated/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics/report.md
python -m py_compile scripts/emotion_state_phase_c_contracts.py scripts/emotion_state_phase_c_temporal_tracker.py scripts/run_emotion_state_003_phase_c0.py scripts/validate_emotion_state_003_phase_c0.py scripts/test_emotion_state_003_phase_c0.py
git diff --exit-code bb1c4231e6d4552f215a96bd0a1d862986775c32 -- runtime
git diff --check
```

Expected: every command exits `0`.

- [ ] **Step 6: Commit the exact pair separately**

```powershell
git add -- research/experiments/generated/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics/result.json research/experiments/generated/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics/report.md
git diff --cached --name-only
git diff --cached --check
git commit -m "Record EMOTION-STATE Phase C0 synthetic mechanics"
```

Expected cached path set: exactly the two generated files.

- [ ] **Step 7: Finalize exact commit trace and revalidate**

After Step 6, add its exact pair commit ID alongside the already recorded
Task 9 implementation/validator and candidate-acceptance heads. Then rerun:

```powershell
python -m unittest scripts.test_emotion_state_003_phase_c0.PhaseCCloseoutContractTests -v
python scripts/validate_emotion_state_003_phase_c0.py checkpoint
python scripts/check_thesis_update_gate.py
python scripts/check_thesis_reference_registry.py
python scripts/validate_project_drift_guard.py
python scripts/validate_context_reading_policy.py
python scripts/validate_check_setup.py
git diff --check
```

Expected: every command exits `0`; documentation contains real commit IDs only.

- [ ] **Step 8: Independently review canonical closeout**

An independent reviewer verifies:

- canonical bytes equal the accepted candidate and exact-path LF attributes;
- result/report semantics, decision, hashes, and non-claims;
- pair-only Step 6 commit scope;
- exact implementation/validator, candidate-acceptance, and pair commit IDs in
  every closeout reference;
- Task 10 diff scope and guarded-ledger evidence; and
- unchanged private/data/provider/call/simulation/source-adaptation/runtime/
  lockbox/Phase D boundaries.

Require `C0/I0/M0` before the documentation commit. Documentation/test findings
may be corrected and the Step 7 ledger rerun. Any canonical-pair finding stops
for a new explicit correction gate; do not amend, rewrite, or silently replace
the pair commit.

- [ ] **Step 9: Commit closeout documentation separately**

```powershell
git add -- docs/product/CHECKPOINT_INDEX.md docs/product/COMMANDS.md docs/thesis/METHODOLOGY_LOG.md docs/thesis/ROADMAP.md research/experiments/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics.md scripts/test_emotion_state_003_phase_c0.py
git diff --cached --check
git commit -m "Close EMOTION-STATE Phase C0 checkpoint"
```

- [ ] **Step 10: Verify clean state and stop before push**

```powershell
git status -sb
git log -12 --oneline
```

Expected: clean branch, local commits ahead of upstream. Do not push, merge,
modify runtime, or begin Phase D without a new explicit gate.

## Plan Self-Review Checklist

- [x] Every approved design section maps to at least one task.
- [x] The policy and all 30 golden scenarios commit before reducer code.
- [x] Every numeric policy value, rounding rule, cap, threshold, ordering rule,
  and decision rule is exact.
- [x] Direct pre-RED tests isolate every threshold/bucket boundary, tie branch,
  and same-modality agreement exclusion outside the golden matrix.
- [x] Input contracts reject Phase B/raw/model/data surfaces.
- [x] Duplicate references reject; repeated independence keys decay and add
  zero support.
- [x] Stale identity rejects and never emits `stale_input`.
- [x] Internal incumbent and emitted abstained selection remain distinct.
- [x] Corrections replace only the latest revision and replay deterministically.
- [x] Output estimates remain `not_inferable` and unapproved.
- [x] Declared effects are not represented as runtime enforcement.
- [x] Golden, metamorphic, semantic, mutation, privacy, and repository gates
  are independent and explicit.
- [x] Candidate/checkpoint validation cross-binds every evaluation-derived
  aggregate field and decision to a fresh deterministic two-run projection.
- [x] Negative evaluations preserve actual abstention/invariant counts and
  serialize coherently as `revise` or `discard`; golden reason totals are
  mandatory only for zero-failure results.
- [x] Typed or independently replay-detected output-semantic failures increment
  `semantic_output` and force `discard`, while the semantically valid
  mechanical-negative fixture remains `revise`; wrong-container/non-JSON
  outputs are validated before serialization, indexing, install, or counting.
- [x] Candidate, canonical, push, merge, and Phase D gates remain separate.
- [x] No task reads datasets/private data, uses providers/calls/network, changes
  runtime, or reopens the Phase B lockbox.
