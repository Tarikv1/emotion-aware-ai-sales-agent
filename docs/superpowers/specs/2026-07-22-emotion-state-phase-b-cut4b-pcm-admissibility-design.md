# Phase B Cut 4B PCM Endpoint Admissibility Design

**Date:** 2026-07-22
**Status:** approved design; legacy-seed cross-binding amendment accepted for implementation
**Approved approach:** endpoint-neutral policy v2
**Current implementation base:** `8195ac9f7cbab23c6de4eadced6ed47293f3668b`

## Decision

Phase B must stop treating the mere presence of PCM16 numeric endpoint values
`-32768` or `32767` as proof that a WAV is clipped or unusable. Endpoint
presence is a measurable saturation observation, but it is not by itself a
validated clipping classifier.

The replacement policy is deliberately threshold-free:

- endpoint values remain valid PCM16 samples;
- endpoint presence, rate, or consecutive run length does not independently
  reject a WAV;
- no threshold may be selected from the observed CREMA-D distribution merely
  to make the production experiment pass;
- all existing structural and feature-viability failures remain fail-closed;
- the experiment makes no claim that endpoint-bearing recordings are clean,
  unclipped, perceptually acceptable, or suitable for production use.

This is a correction to an invalid inference, not a new clipping detector.

## Evidence and root cause

The first post-Cut-4A production attempt stopped before transaction
linearization with:

```text
production non-lockbox build failed: WAV contains clipped samples
```

The reader in `scripts/emotion_state_phase_b_features.py` rejects every WAV
containing either PCM16 endpoint. Its regression test labels a single endpoint
sample as clipping. That test proves only numeric endpoint presence, not
flat-topping, audible distortion, acquisition overload, or downstream feature
invalidity.

The separately authorized aggregate-only diagnostic examined the exact 7,441
tracked-included verified CREMA-D WAV identities and found:

- 550 files with at least one endpoint value (`7.3915%`);
- 43,117 endpoint samples among 302,745,136 samples (`0.014242%`);
- maximum consecutive same-endpoint runs distributed as 73 files with one,
  179 with two to three, 269 with four to seven, and 29 with eight or more.

Those aggregates show that the old predicate has broad impact and mixed
patterns. They do not provide perceptual labels or justify a rate/run cutoff.
The diagnostic report is contextual evidence only; it is not a production
input, model feature, label source, or threshold-training surface.

## Goals

1. Correct the false implication `numeric endpoint present => clipped WAV`.
2. Bind the corrected interpretation to an explicit versioned feature schema.
3. Preserve the existing 17-feature definitions, order, and numerical
   semantics.
4. Preserve malformed-input, unsupported-format, empty-stream, digital-silence,
   incomplete-frame, nonsilent-frame, spectral-power, and voiced-frame gates.
5. Rebuild Phase B from a fresh ignored lineage without parsing, reusing,
   deleting, rewriting, or recovering the retired split/preflight/non-lockbox
   lineage. Read-only metadata inventory and hashing are allowed solely to
   prove that lineage remains unchanged.
6. Run at most one newly authorized replacement non-lockbox production attempt
   after strict TDD, independent review, and fresh preflight validation.
7. Preserve the final-lockbox, canonical publication, provider, private-data,
   call, runtime, push, merge, and Phase C boundaries.

## Non-goals

- Detecting audible clipping or waveform flat-topping.
- Declaring endpoint-bearing audio high quality.
- Selecting an endpoint-rate or run-length threshold.
- Excluding or relabeling CREMA-D examples based on this diagnostic.
- Reading or adapting AMI for the policy correction.
- Adding audio, endpoint statistics, identities, paths, labels, rows,
  probabilities, or features to the public review packet.
- Reusing, migrating, repairing, deleting, or mutating the retired Phase B
  lineage.
- Opening the final lockbox, staging canonical output, activating runtime
  behavior, or beginning Phase C.

## Versioned feature contract

Create
`research/sources/emotion_state/emotion_state_phase_b_feature_v2.schema.json`
and retain the existing v1 file unchanged as historical authority.

The v2 document keeps every existing v1 field and exact 17-name feature order,
changes only the root identity to:

```json
{
  "schema_id": "emotion-state-crema-interpretable-acoustic-v2",
  "schema_version": 2
}
```

and adds this exact nested contract:

```json
{
  "pcm_endpoint_admissibility": {
    "policy_id": "emotion-state-pcm16-endpoint-admissibility-v1",
    "endpoint_values": [-32768, 32767],
    "presence_interpretation": "numeric_saturation_observation_not_clipping_proof",
    "reject_on_presence": false,
    "rate_threshold": null,
    "run_length_threshold": null,
    "clipping_classification_implemented": false
  }
}
```

`pcm_endpoint_admissibility` appears immediately after `channel_count` in the
root insertion order. Its nested keys appear in exactly the order shown above.

The strict independent validator must require the exact key set, built-in JSON
types, values, ordering, and policy text. It must reject v1 when v2 is required,
unknown policy fields, threshold substitution, `true` rejection/classification
flags, numeric type drift, and endpoint-list mutation or reordering.

The production feature-schema path, expected semantic identity, static file
digest, preflight ledger, partition authorities, feature caches, and packet
lineage must all bind the v2 bytes or their existing validated transitive
commitments. No caller flag, environment variable, alternate reader, or
unbound fallback may select the policy.

### Frozen configuration seed lineage and active-schema cross-binding

The tracked Phase B configuration remains byte-identical. Its existing field:

```json
"feature_schema_id": "emotion-state-crema-interpretable-acoustic-v1"
```

is an immutable **legacy seed-lineage token**, not the active feature-schema
selector for Cut 4B. Changing that tracked value would change the configuration
semantic identity that deterministically seeds actor assignment and model
identity, violating this correction's fixed-split/fixed-model boundary.

The only accepted Cut 4B compatibility tuple is therefore exact:

```text
legacy configuration token: emotion-state-crema-interpretable-acoustic-v1
active feature schema:       emotion-state-crema-interpretable-acoustic-v2
active schema semantic SHA:  AEC550285DF6A92B3E86E16F66A2E5B554836BBE47C625106F517EB0CF1375DB
configuration raw SHA:       BBB16BDB1205255B0D1C3F0F33891ECC75C4F074D0E6D7200D09A6B385CFE914
configuration semantic SHA:  24E2186A3ACB19817BF87689F09A2F069AC07B5C1D669364D5FC08BC9AD5FA8F
model seed:                  618797162
```

The fixed v2 path plus its raw and semantic identities are the exclusive active
schema authority. The legacy token cannot select v1, authorize an alternate
path, or weaken v2 validation. An explicit cross-binding validator must require
the exact tuple after separately validating both mappings, and it must run in
the offline contracts validator, production static preflight, direct
non-lockbox builder, committed non-lockbox readback/source-silent replay, and
aggregate-result reconstruction. Either-side drift fails closed.

Any future change to the configuration token or its semantic identity requires
a new experiment version and reviewed re-preregistration because it remints
the split assignment and model identity. Cut 4B does not make that change.

The feature-cache schema and packet schema do not need structural version
bumps. Their existing `feature_schema_sha256` and cache self-commitments already
bind the changed feature authority transitively. Tests must prove that caches
or packets carrying the v1 feature identity are rejected under the v2 run.

## Reader behavior

`_read_pcm16_mono_16khz_bytes()` continues to enforce:

- exact `bytes` input;
- parseable, uncompressed WAV;
- one channel;
- two-byte PCM samples;
- 16,000 Hz sample rate;
- at least one declared frame;
- exact frame-byte length and sample count; and
- finite normalized output.

It removes only the endpoint-presence rejection. Downstream extraction remains
unchanged: a WAV can still fail because it has no complete analysis frame, no
nonsilent analysis frame, no spectral power, fewer than three voiced frames,
or another already-frozen feature-viability failure.

Tests must use otherwise viable deterministic waveforms containing both
endpoint values. At least one case must contain a consecutive endpoint run
greater than the diagnostic's `8_plus` boundary so the test proves no hidden
run threshold was introduced. Separate existing tests must continue to prove
all malformed, unsupported, silent, near-silent, DC, unvoiced, empty, and
incomplete cases fail for their original reason.

## Fresh lineage and fixed paths

The existing production root
`.tmp/emotion-state-002-phase-b` contains the retired split, preflight, and
failed non-lockbox lineage. Its lineage surfaces must remain byte- and
entry-identical throughout Cut 4B. The immutability proof covers `state.json`,
the `inputs`, `split`, `preflight`, and `non-lockbox` trees, and every
preflight/non-lockbox state-control file. It excludes only the separately
pinned dependency directories named below. The proof may inventory metadata
and hash exact bytes in memory, but it may not parse or reuse retired payloads
as inputs and may not persist or print their paths, identities, or contents.

The corrected production state root is exactly:

```text
.tmp/emotion-state-002-phase-b-cut4b
```

`RunnerPaths.production()` must point split, input-ledger, state, preflight,
non-lockbox, control, and recovery paths into that new root. A test must freeze
the new path and prove production execution does not resolve any of those
lineage paths under the retired root.

The already verified dependency environment remains fixed at:

```text
.tmp/emotion-state-002-phase-b/venv
.tmp/emotion-state-002-phase-b/dependencies/wheelhouse
```

Those dependency directories are immutable inputs, not retired
split/preflight/non-lockbox lineage. Cut 4B may read their already-pinned
environment and wheel identities but must not install, update, delete, or
rewrite them.

The fresh run sequence is:

1. prove the retired lineage fingerprint and entry inventory before any write;
2. prove the Cut 4B root is absent and the tracked worktree is clean;
3. run one fresh production preflight against the Cut 4B root;
4. independently validate the fresh split/preflight state and v2 schema
   binding;
5. re-prove the retired lineage is byte- and entry-identical;
6. run exactly one sanitized-child `non-lockbox` attempt against the Cut 4B
   root;
7. independently validate only the aggregate packet/caches/state required by
   Task 10, without printing or persisting identifiers, rows, paths,
   probabilities, transcripts, features, or audio; and
8. re-prove retired-lineage immutability and stop.

If the Cut 4B root already exists before first issuance, or the retired lineage
changes, execution stops. No cleanup or retry is implicit.

## State, cache, and packet invariants

- The fresh preflight mints a new split/input lineage bound to the v2 feature
  schema; it must not copy the retired split manifest or input ledger.
- The same deterministic split algorithm, exact configuration seed identity,
  resulting actor assignment, model seed, and public identities remain fixed.
- The three acoustic cache formats retain their accepted exact key sets and
  17-feature order.
- Every cache must carry the v2 feature-schema identity and its existing source,
  partition, environment, and tracked-authority commitments.
- Packet v4 remains aggregate-only and transitively commits the exact cache
  self-identities.
- All five lockbox counters remain exact built-in integer zero.
- Final-lockbox digests, canonical state, publication controls, and runtime
  surfaces remain absent or unset.
- Source-silent semantic replay may read only the newly persisted Cut 4B caches
  and packet; it may not fall back to the retired lineage or public material.

## TDD and review strategy

The correction is one behavior-changing task with one independently reviewable
commit after the design/plan commits.

RED must establish all of the following before implementation:

1. otherwise viable endpoint-bearing WAV bytes currently fail;
2. the current validator does not recognize the required v2 schema;
3. production paths currently resolve to the retired lineage root;
4. production feature-schema paths, expected identities, preflight, and cache
   fixtures are still bound to v1 rather than the required v2 authority; and
5. production split/preflight/non-lockbox paths still resolve under the
   retired state root rather than an isolated Cut 4B root.
6. no explicit validator currently distinguishes the legacy configuration
   seed token from the exclusive active v2 schema authority or enforces their
   exact compatibility tuple across production/replay entry points.

GREEN must make only the endpoint-neutral policy, v2 binding, and new-root
lineage changes necessary to close those failures. Focused tests run first;
the complete Phase B suite, executable validator sections, compilation,
thesis/reference/drift/context/setup gates, and `git diff --check` run once
before commit.

An independent reviewer must return both spec compliance and task-quality
approval with no open Critical or Important findings. Any correction receives
its own focused RED/GREEN evidence and re-review before production execution.

## Experiment discipline

**Hypothesis:** Replacing the invalid endpoint-presence rejection with a
version-bound endpoint-neutral policy will allow structurally valid,
feature-viable CREMA-D material to reach the frozen non-lockbox experiment
without changing features, labels, splits, models, metrics, or evaluation
rules.

**Fixed cases:** Existing malformed/unsupported/quality negatives; new
otherwise viable positive and negative endpoint waveforms; exact verified
public identities; fixed deterministic split/evaluation configuration.

**Baseline:** The first corrected-source production attempt fails before
linearization on any endpoint-bearing WAV.

**Editable surface:** PCM endpoint admissibility plus the mechanically required
v2 schema binding, exact legacy-seed/active-schema compatibility enforcement,
and fresh state-root routing. The configuration bytes and identities are not
editable.

**Decision rule:** Keep only if all fixed negative tests remain negative, all
endpoint-neutral positive tests pass, independent review approves the exact
diff, the retired lineage remains unchanged, and the fresh Task 10 packet
passes both validators and privacy/zero-lockbox gates. Otherwise stop and
classify the new blocker; do not loosen another rule in the same cycle.

## Completion and readiness boundary

Successful Cut 4B execution may establish only an offline, public-dataset,
acted-perception feasibility checkpoint. It does not establish internal emotion
recognition, real-customer performance, production readiness, PSTN/ASR/latency
behavior, manipulation safety, runtime authority, or final-lockbox performance.

After a successful independent Task 10 review and separate aggregate-only
documentation commit, stop before Phase C. Phase C requires a new reviewed
scope based on the accepted non-lockbox evidence; it is not automatically
entered by Cut 4B completion.
