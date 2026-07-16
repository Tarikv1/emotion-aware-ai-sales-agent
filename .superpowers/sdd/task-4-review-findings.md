# Task 4 independent review findings and resume boundary

## Independent review verdict for initial commit `7cc288a`

Needs fixes.

### Critical

1. Per-cell speaker support was caller-asserted instead of derived from the records selected after the per-speaker cap.
2. The release validator accepted identity-bearing or per-speaker structures when placed under allowlisted metric names.
3. Overlap and differencing controls trusted caller-declared window relationships without comparing the candidate against authoritative prior release history.

### Important

1. A record from an ineligible foreign corpus could bypass the all-record dataset-eligibility rule.
2. Boolean and floating-point lookalikes were accepted for task-owned integer constants.
3. The five-speaker/twenty-turn discovery thresholds were not enforced by a production discovery-gate function.
4. Arbitrary suppression reason codes and semantically inconsistent reasons were accepted.

### Minor

1. Unhashable enum-like inputs leaked `TypeError` rather than the contract's deterministic `ValueError`.

## Controller clarification incorporated into the amended Task 4 brief

- Remove caller-provided `output_cell_unique_speaker_counts`.
- Require exact per-record `metric_cell_memberships` for all six metrics.
- Derive every released output cell's unique-speaker support from namespaced speakers remaining after the deterministic cap.
- Enforce strict sparse metric shapes; reject rows, arrays, identity, and per-speaker structures.
- Require the exact complete `authoritative_release_history` and its canonical digest, then compare candidate intervals and replacement metadata against every prior release. Authenticity of an external append-only registry remains explicitly outside Phase A.
- Validate every record's dataset ID before any eligibility filtering.
- Require exact `int` types for task-owned integer constants; reject booleans and floats.
- Add production `evaluate_discovery_gate(records)` behavior.
- Freeze suppression reason codes and enforce semantic consistency.
- Convert invalid/unhashable request and membership values to deterministic `ValueError` before set/dict membership operations.

## Post-restart live RED readback

At HEAD `7cc288a8e69a8504cc8ce7728450698debbcdf32`, the interrupted fix patch remains uncommitted in only:

- `scripts/emotion_state_cohort_release_contracts.py`
- `scripts/test_emotion_state_001_open_dataset_gate.py`

The following focused tests still fail and must be made green without weakening their assertions:

- `test_ineligible_foreign_dataset_record_still_suppresses`: released instead of suppressed.
- `test_task_owned_integer_constants_reject_bool_and_float_lookalikes`: four subcases did not raise `ValueError`.
- `test_five_speaker_twenty_turn_cohort_is_discovery_only`: `evaluate_discovery_gate` is missing from production.
- `test_suppression_reason_codes_are_frozen_and_semantically_consistent`: four subcases did not raise `ValueError`.
- `test_unhashable_request_and_membership_values_raise_value_error`: six subcases leaked `TypeError`.

Previously observed green additions in the same dirty patch cover history/digest/replacement comparison, membership-derived cell support, and strict sparse released-metric shape validation. Re-run them; do not trust that observation without verification.

## Hard boundaries

This task is offline contract/test work only. Do not access ElevenLabs or any provider, place outbound/customer calls, run simulations, download or inspect private data, adapt source code from the friend's repository, activate runtime behavior, push, merge, or claim production readiness.
