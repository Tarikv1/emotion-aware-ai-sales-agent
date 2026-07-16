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

## Round 2 independent whole-range review at `a40a46e`

Verdict: not ready for Task 5.

### Critical

1. Count-map values are not reconciled with membership-derived support. A validated aggregate with `{"unavailable": 5, "usable": 5}` and ten selected records claiming only `unavailable` is released as `{"unavailable": 5}` with claimed support `10`. The dual-membership variant releases both five-count cells with claimed support `10`. This defeats the ten-speaker per-cell floor. For count-map metrics, require each cell's aggregate count to equal its membership-derived unique-speaker support after the one-record-per-speaker cap, and reject zero-count/nonzero-membership or any other contradiction.

### Important

1. `evaluate_discovery_gate` pools namespaced speakers across dataset IDs. Phase A's unconditional cross-corpus grouping prohibition must apply before discovery eligibility; mixed-dataset input must be rejected or return ineligible.
2. `validate_cohort_release` omits derivable cross-field invariants. It accepts `source_label="public-only"` with `unique_speaker_basis="synthetic_fixture_speaker_id"`, and accepts impossible suppressed evidence with a null basis but nonzero speakers and a non-null dedup digest. Because authoritative history is validated through this function, impossible entries can contaminate replacement chains. Share source/basis validation and require basis-null evidence to have zero selected/unique speakers and a null dedup digest.

### Required regression groups

- Count-map five/five mismatch and dual-membership inflation must fail before the production fix.
- Mixed-corpus discovery input must not be eligible.
- Direct standalone validation and authoritative-history entry tests must reject the source/basis and basis-null contradictions.

The controller independently reproduced all three issue groups against committed HEAD before accepting the review. Preserve every existing assertion and boundary.

## Round 3 independent whole-range review at `03af343f`

Verdict: not ready for Task 5. This is review pass 3 of a maximum 5-pass deep privacy/security/QA loop.

### Critical

1. The authoritative history model rejects a valid complete append-only `[root, replacement]` chain as an overlap, while accepting a lone entry with arbitrary equal replacement digests. Treat history list order as append order. A root has null replacement digests. Each replacement must reference the canonical digest of exactly one earlier active head with the same window, fixed-window ID, and metric allowlist. Permit same-window overlap only for that valid successor and mark the predecessor superseded. Reject dangling/forward/self references, cycles, forks, stale-head replacements, duplicate entries, reordering, changed window/ID/allowlist, and overlap between distinct window chains. Candidate replacements target the unique active head.
2. Count-map equality still permits balanced dual-plus-empty memberships: some selected records claim two cells while others claim none. Require exactly one membership cell per selected record for every count-map metric, retaining exact per-cell aggregate/support equality. Cover both count maps.

### Important

1. Synthetic/public provenance and identifier basis remain caller asserted. Bind public bases to the exact approved public dataset IDs and their matching actor/participant basis plus conservative dataset-specific non-PII identifier formats. Bind synthetic records to the controlled synthetic fixture dataset and speaker namespaces. Discovery must share the same validator. Verify each canonical record digest against a frozen canonical projection of the exact record evidence rather than trusting an opaque caller digest. Structural validation does not authenticate external material; keep that trust boundary explicit and do not claim it does.
2. Standalone suppressed evidence accepts builder-impossible counts. Enforce `0 <= eligible_record_count <= unique_speaker_count <= input_record_count`; non-null dedup evidence requires eligible equals unique; null dedup evidence requires eligible zero; selection-failure reasons must remain consistent. Apply the same checks to authoritative history entries.

### Minor

1. Strengthen schema/fixture parity so the authoritative validator compares the complete schema descriptor and exact typed scenario parameters, including contract name, source labels, release statuses, thresholds, and expectations. Add mutation-negative tests if this remains a bounded Task 4 change; otherwise record it explicitly for whole-branch review.

### Required pass-4 regressions

- Valid root to replacement to replacement history and an unrelated later release must pass.
- Missing predecessor, arbitrary digest, reordered history, stale-head fork, changed window/ID/allowlist, and distinct-window overlap must fail.
- Balanced dual-plus-empty membership must fail for both count-map metrics.
- Private/arbitrary dataset IDs, email-shaped/public-basis IDs, wrong public dataset-to-basis mappings, uncontrolled synthetic namespaces, and forged canonical record digests must fail in release and discovery paths.
- Impossible standalone suppressed counts and the same entries inside authoritative history must fail.
- Existing sparse omission, current adversarial cases, runtime/v1 immutability, and all hard boundaries must remain green.
