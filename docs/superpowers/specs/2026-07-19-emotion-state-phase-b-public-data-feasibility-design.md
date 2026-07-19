# EMOTION-STATE-002 Offline Phase B Public-Data Feasibility Design

## Status

Design approved on `2026-07-19`.

This document authorizes design documentation only. It does not authorize
dependency installation, a public-material read, feature extraction, model
evaluation, canonical result publication, source adaptation, provider access,
calls, simulations, runtime activation, push, or merge.

The implementation base is the accepted Phase A checkpoint commit:

```text
f8ba503c3670fec6e9dee53f03f306798e7b807b
```

The implementation branch is:

```text
codex/emotion-state-phase-b-public-data-feasibility
```

## Goal

Determine whether a frozen, interpretable acoustic feature vector contains
speaker-independent information about CREMA-D's original six audio-perception
labels, while separately proving that AMI manual annotations can produce
deterministic, privacy-minimized conversational-mechanics aggregates.

Phase B is a public-data feasibility study. It does not estimate customer
internal emotion and does not map either dataset to:

```text
hesitation
frustration
confusion
interest
disengagement
```

## Approved Claim Boundary

Phase B may establish:

- deterministic public-material feature extraction;
- speaker-disjoint performance on CREMA-D's original acted-perception labels;
- calibration and abstention behavior for those source labels;
- deterministic AMI turn and timing mechanics;
- a valid negative, revise, or research-only keep decision;
- offline thesis limitations and reproducibility evidence.

Phase B may not establish:

- a customer's true, hidden, or internal emotion;
- accuracy for the five project operational signals;
- natural sales-conversation emotion recognition;
- a `PatternCandidateV1`;
- a populated or runtime-approved `PerceivedCustomerStateV1`;
- fairness across demographic groups;
- collection-site generalization;
- provider, PSTN, ASR, streaming, or latency feasibility;
- live aggregate release;
- safety or commercial effectiveness in customer conversations;
- production readiness;
- source adaptation or runtime activation.

## Approaches Considered

### Classical Interpretable Baseline

Selected.

Use a frozen acoustic feature vector, a class-prior baseline, a
sentence-identity baseline, and one standardized L2 multinomial logistic
regression model. This is the smallest approach that can test a
speaker-independent acoustic-sensitivity hypothesis while remaining
interpretable and thesis-auditable.

### Standard Acoustic Toolkit

Deferred.

A standardized feature family could improve comparison with speech research,
but it would add an external extraction runtime, a wider dependency and
license-review surface, and a greater risk that research-only tooling leaks
into the product path.

### Pretrained Speech Embeddings

Rejected for the first Phase B checkpoint.

Pretrained speech models would require model downloads and more compute, would
be less interpretable, and would make it harder to determine whether a small
classical baseline is already sufficient. Their use would require a later
design and explicit authorization.

## Architecture

Phase B is isolated from `runtime/`:

```text
accepted Phase A evidence and ignored public material
  -> bounded material readers
  -> deterministic local feature/mechanics caches
  -> claim-scoped split and contribution gates
  -> classical offline evaluation
  -> staged aggregate result/report pair
  -> independent validation and explicit acceptance
```

The two data lanes never join at the row level:

1. CREMA-D supplies controlled acoustic-sensitivity evidence with its original
   audio-perception labels.
2. AMI supplies conversational mechanics without an emotion or operational
   label.

The friend project's pinned evidence remains provenance-only. No new read,
copy, translation, adaptation, reimplementation, dependency, or runtime use
of that source is part of Phase B.

## Immutable Phase A Inputs

Phase B binds the accepted Phase A result and report at commit `f8ba503` and
the existing tracked dataset evidence.

### CREMA-D

```text
dataset_id:
  crema-d-v1.0-audio-wav
source_revision:
  f3b8611a309886568dfa957141775b2e05add04a
manifest_sha256:
  6E86F06358E4AD172C72BE1692CFF37291D9D5763DD7F6F5C7CE7405E7E01248
hash_inventory_sha256:
  AD58D8165C683847DF246F923FF466722C7F628FE8D81679F618FA5EB3031C87
quality_inventory_sha256:
  455D6A010855F209B4DC4C67F67E4222FAB81601861745B5B5E79E7942B92682
```

### AMI

```text
dataset_id:
  ami-manual-annotations-v1.6.2
archive_sha256:
  B56E5BABB2496B8795DEEEDA7E71178D7FBC9963F94276CF2A3F4B56EBBC9F9D
manifest_sha256:
  3904D4A3A9EDF53B06A65354E02FBE1BDD44361B5E196FC6DD4A3882C74911DE
hash_inventory_sha256:
  CE7F837A2A44DFEE44691C4BA8B5B0D7766E46D6616986CF565A6300056DEAEE
quality_inventory_sha256:
  A376A6C0D5F89770525936299717F1595B743489B593DC4E5CE88AB08ACB22C9
```

Any mismatch stops Phase B before a feature, split, model, or canonical output
is created.

## CREMA-D Reference-Label Contract

Only audio-perception rating rows may supply a target label.

The frozen source-label map remains:

```text
A -> anger
D -> disgust
F -> fear
H -> happy
N -> neutral
S -> sad
```

Eligibility requires:

- a Phase A included WAV with an exact verified hash;
- no Phase A exclusion or known-no-audio status;
- structurally valid mono PCM at `16,000 Hz` with a two-byte
  (`16-bit`) sample width;
- at least one usable audio-perception vote;
- one unique maximum in the audio-perception vote distribution;
- a complete actor and sentence dependency identity;
- a finite feature vector.

Tied vote maxima, missing usable votes, malformed material, digital silence,
insufficient voiced frames, and unresolved required dependencies abstain and
remain outside every fit, metric, and claim denominator.

The following are retained only for aggregate diagnostics:

- maximum vote share;
- vote-distribution entropy;
- abstention reason;
- source-label count;
- actor count per output cell.

They cannot enter the acoustic model's feature matrix.

The intended filename emotion code, intended actor prompt, filename, path,
actor ID, sentence ID, vote counts, normalized label, and any label-derived
value are forbidden model features.

## Frozen Acoustic Feature Schema

Schema ID:

```text
emotion-state-crema-interpretable-acoustic-v1
```

Input processing is deterministic:

- no resampling;
- 25 ms Hann windows;
- 10 ms hop;
- silence threshold equal to the greater of `-50 dBFS` and
  `utterance_peak_frame_dbfs - 40 dB`;
- nonsilent frames only for zero-crossing and spectral summaries;
- fundamental-frequency search range `75-400 Hz`;
- normalized autocorrelation voiced threshold `0.30`;
- at least three voiced frames;
- spectral roll-off fraction `0.85`;
- percentile interpolation fixed by the experiment configuration.

The ordered feature vector contains exactly:

```text
duration_seconds
silence_ratio
voiced_fraction
f0_median_hz
f0_iqr_hz
f0_range_hz
rms_dbfs_mean
rms_dbfs_std
rms_dbfs_p90_minus_p10
zero_crossing_rate_mean
zero_crossing_rate_std
spectral_centroid_hz_mean
spectral_centroid_hz_std
spectral_bandwidth_hz_mean
spectral_bandwidth_hz_std
spectral_rolloff_85_hz_mean
spectral_rolloff_85_hz_std
```

Every feature must be finite. No imputation is allowed. An invalid or missing
feature abstains the utterance and records an aggregate reason count.

The first Phase B checkpoint excludes:

- MFCCs;
- learned embeddings;
- pretrained models;
- demographic attributes;
- transcript semantics;
- speaker embeddings or voiceprints;
- per-speaker normalization;
- normalization fitted with calibration, diagnostic, or lockbox data.

## Claim-Scoped Evaluation Split Contract

Phase A `split_manifest_v2` remains unchanged.

It cannot be directly reused for this within-corpus evaluation because
`source_corpus` is a required cross-partition-disjoint key and every CREMA-D
record has the same source-corpus value. Direct reuse would force the entire
dataset into one partition.

Phase B adds:

```text
emotion-state-evaluation-split-v1
```

This contract assigns a dependency role per claim:

```text
exclusion_group
stratification_factor
scope_constant
covered_by_higher_dependency
advisory_unavailable
not_applicable
```

The primary CREMA-D claim uses:

```text
speaker            -> exclusion_group
scripted_scenario  -> stratification_factor
source_corpus      -> scope_constant
call_session       -> covered_by_higher_dependency(speaker), if verified
recording_site     -> advisory_unavailable
meeting_series     -> not_applicable
dialogue_dyad      -> not_applicable
```

No actor crosses:

```text
training_discovery
calibration
balanced_diagnostic
final_lockbox
```

All twelve controlled sentence identities remain represented as
stratification factors. Therefore, the primary experiment may claim
speaker-disjoint behavior only for CREMA-D's fixed controlled-sentence
domain. It may not claim unseen-script or natural-language generalization.

The expected 91 actors are allocated deterministically:

```text
training_discovery: 35
calibration: 13
balanced_diagnostic: 13
final_lockbox: 30
```

If the verified actor count is not exactly 91, allocation stops and requires a
new reviewed design. Partition assignment uses source-label metadata only to
preserve label coverage; no acoustic feature or model result may influence
the allocation.

A future sentence-held-out experiment may assign
`scripted_scenario -> exclusion_group`, but it is not part of this first
checkpoint and cannot reuse the final lockbox.

The local row-level split manifest remains ignored. The tracked experiment
records its deterministic algorithm, configuration digest, aggregate counts,
and SHA-256 digest, but no actor token or per-case assignment.

## Models And Anti-Leakage Controls

The frozen comparisons are:

1. class-prior dummy baseline;
2. sentence-ID-only L2 multinomial logistic-regression baseline;
3. standardized acoustic-only L2 multinomial logistic regression.

The acoustic model uses:

```text
regularization: L2
C: 1.0
class_weight: none
maximum_iterations: 10000
```

The exact solver behavior is bound by the later locked scikit-learn version.
No hyperparameter search occurs.

The acoustic standardizer is fitted on `training_discovery` only. The sentence
baseline uses one-hot sentence identity with unknown values ignored. No model
combines sentence identity and acoustic features in this checkpoint.

The evaluation must prove that the final model matrix contains only the
17 ordered acoustic features. Tests must reject:

- filename columns;
- intended emotion codes;
- labels or vote values;
- actor or sentence identity;
- paths;
- hashes derived from forbidden identity or label fields;
- array-order coupling that reconstructs a forbidden field;
- preprocessing fitted outside `training_discovery`.

No serialized model is tracked or made available to runtime.

## Partition Lifecycle

### Training Discovery

- fit the acoustic standardizer;
- fit the three frozen comparison models;
- expose no final decision.

### Calibration

- compute maximum predicted probability;
- freeze confidence thresholds targeting `100%`, `80%`, and `60%` retained
  coverage;
- record actual achieved coverage when threshold ties occur;
- do not change features, model parameters, labels, slices, or metrics.

### Balanced Diagnostic

- report per-class recall;
- report all twelve sentence slices;
- report vote-agreement slices;
- report silence-ratio quartiles frozen from `training_discovery`;
- make no prevalence or calibration claim.

Vote-agreement bins are:

```text
[0.00, 0.50)
[0.50, 0.75)
[0.75, 1.00]
```

### Final Lockbox

- prevalence representative;
- at least 30 actors;
- opened exactly once;
- opened only after configuration, environment, feature schema, split digest,
  model settings, metrics, bootstrap seed, slices, decision rules, and output
  schema are frozen;
- never reused after a code, configuration, dependency, or data change.

Any invalid lockbox opening makes that experiment version `discard` and
requires a new version with a new untouched lockbox.

## Metrics

Primary metric:

```text
final-lockbox macro-F1 lift of the acoustic model over:
  1. class-prior baseline
  2. sentence-ID-only baseline
```

Secondary metrics:

- balanced accuracy;
- per-class recall;
- multiclass Brier score;
- multiclass log loss;
- ten-bin equal-width expected calibration error;
- coverage and retained macro-F1 at the frozen `100%`, `80%`, and `60%`
  targets;
- actor count and case count for every published cell.

Confidence intervals use 2,000 paired actor-cluster bootstrap resamples. Each
resample draws lockbox actors with replacement and includes all eligible
lockbox cases for each drawn actor. The deterministic seed is derived from the
frozen experiment-configuration digest. The same resample indexes compare all
models.

Every published class, sentence, agreement, quality, and coverage cell
requires at least ten unique actors. Sparse cells are omitted and recorded as
suppressed, not emitted as zero.

No demographic slice is permitted because Phase A deliberately excluded
unnecessary demographic material and Phase B has no separate minimization or
ethics approval for it.

## Decision Contract

Experiment completion depends on valid execution, not a favorable score.

### Keep For Research Only

`keep_for_research_only` requires:

- positive paired macro-F1 lift over both baselines;
- the lower 95% confidence bound for both lifts is greater than zero;
- acoustic-model Brier score improves over the class-prior baseline;
- no source label has zero recall;
- no leakage, material, split, environment, determinism, or lockbox failure;
- no material result reversal hidden by a suppressed or eligible
  preregistered slice.

This status does not permit runtime use.

### Revise

`revise` applies when execution is valid but:

- a positive point estimate has an interval crossing zero;
- calibration is worse;
- a class has zero recall;
- a preregistered eligible slice is materially unstable;
- confidence-based abstention does not improve retained performance.

Revision requires a new preregistered experiment version and an untouched
lockbox.

### Discard

`discard` applies when:

- the acoustic model does not beat both baselines;
- sentence identity explains the apparent lift;
- leakage is detected;
- deterministic rerun hashes differ;
- the lockbox is reused or opened prematurely;
- material or environment identity is invalid.

A valid negative result remains thesis evidence.

## AMI Conversational-Mechanics Lane

AMI performs no model training, emotion classification, operational-signal
classification, or join with CREMA-D rows.

The extractor may use released transcript boundaries, timing links, dialogue
acts, participant associations, meeting identities, meeting-series
identities, sites, and official partitions. It emits no transcript text.

The frozen aggregate metrics are:

```text
turn_duration_ms_median
turn_duration_ms_p90
inter_turn_gap_ms_median
inter_turn_gap_ms_p90
overlap_ratio
floor_changes_per_minute
speaker_balance_normalized_entropy
backchannels_per_100_turns
dialogue_act_distribution
```

The tracked report may compare only the official:

```text
scenario_only
full_corpus
full_only
```

source partitions.

Unknown participant, meeting-series, site, or scenario dependency values
enter quarantine and cannot contribute to a published cell.

For contribution-limited publication:

1. sort meetings by official source order and canonical meeting digest;
2. include a meeting only when none of its verified participants has already
   contributed to that output cell;
3. permit at most one meeting contribution per participant per cell;
4. require at least ten proven unique participants per scalar, bucket, or
   dialogue-act cell;
5. suppress a cell when deterministic contribution selection or uniqueness
   cannot be proven.

The local row-level mechanics table remains ignored. The tracked result
contains aggregate metrics, eligible/suppressed counts, source-partition
identity, configuration and input digests, and limitations only.

AMI mechanics cannot be relabelled as hesitation, frustration, confusion,
interest, or disengagement.

## Research Environment

Phase B targets Python `3.11`.

The only direct numerical dependencies are:

```text
NumPy
SciPy
scikit-learn
```

Exact versions, distributions, licenses, artifact hashes, and transitive
dependencies must be reviewed and frozen in a research-only lock before a
real-data run.

The current local observation is:

```text
Python: 3.11.15
NumPy: 2.4.3
SciPy: not installed
scikit-learn: not installed
```

This observation is not an approved environment and authorizes no install.

The implementation must:

- keep the environment outside product/runtime dependency manifests;
- require exact version and lockfile identity;
- fail closed when a dependency is missing or differs;
- perform no package, dataset, or model fetch during evaluation;
- scrub provider credentials;
- deny network access;
- deny private and private-restricted paths;
- import no runtime policy, prompt, campaign, provider, voice, or persistence
  module.

Custom reimplementation of the numerical optimizer is out of scope.

## Local And Tracked Data Boundary

Ignored local root:

```text
.tmp/emotion-state-002-phase-b/
```

It may contain:

- row-level feature caches;
- local split assignments;
- fitted preprocessing state;
- fitted research model state;
- bootstrap indexes;
- staged candidate and rollback state.

It may not contain private or private-restricted data.

Tracked artifacts may contain:

- schemas;
- frozen configuration;
- aggregate counts and metrics;
- environment and input digests;
- feature-schema and split-manifest digests;
- model settings;
- aggregate decision evidence;
- known limitations;
- canonical result/report pair.

Tracked artifacts may not contain:

- audio bytes;
- transcript text;
- filenames or local paths;
- actor, participant, speaker, meeting, or per-case rows;
- speaker tokens, embeddings, or voiceprints;
- serialized preprocessing or model objects;
- raw probability rows;
- provider payloads or credentials;
- timestamps or absolute worktree paths;
- customer-state or operational-signal labels.

## Canonical Publication

Canonical directory:

```text
research/experiments/generated/EMOTION-STATE-002-phase-b-public-data-feasibility/
```

It contains exactly:

```text
result.json
report.md
```

No third canonical file is allowed.

The result binds:

- Phase A checkpoint commit and canonical pair hashes;
- exact dataset evidence digests;
- environment lock digest;
- experiment-configuration digest;
- feature-schema digest;
- local split-manifest digest and aggregate partition counts;
- source-label eligibility and abstention counts;
- model settings;
- exact metric and slice definitions;
- lockbox open count;
- aggregate CREMA-D metrics and confidence intervals;
- aggregate or suppressed AMI mechanics;
- keep/revise/discard decision;
- closed provider, private-data, source-adaptation, runtime, and customer-state
  boundaries.

The report summarizes the same deterministic result and carries an exact
result hash marker.

Publication uses a controller-owned staged transaction with:

- exact previous-pair preservation;
- durable `awaiting_acceptance` state;
- candidate readback;
- independent content review;
- explicit accept or reject;
- restoration on any pre-acceptance failure;
- pair-only commit after acceptance.

The implementation plan must reuse the reviewed transaction design rather
than inventing a weaker direct-write path.

## Failure Handling

Stop before canonical output on:

- Phase A checkpoint or evidence drift;
- public-material hash or quality drift;
- environment or dependency drift;
- unexpected files or classifications;
- malformed, silent, or unsupported WAV input;
- malformed AMI annotation structure;
- non-finite or missing required features;
- unresolved required dependency identity;
- actor or claim-scoped split leakage;
- forbidden label, filename, path, speaker, or prompt metadata in features;
- preprocessing fitted outside `training_discovery`;
- configuration mutation after freeze;
- nondeterministic feature, split, metric, bootstrap, or report hashes;
- a lockbox open count other than the expected transition from zero to one;
- private-path access;
- network or provider access;
- runtime imports or writes;
- a missing, extra, or contradictory canonical output.

No fallback may silently:

- impute a failed feature;
- substitute filename prompt labels for perception labels;
- weaken a dependency requirement;
- reuse a lockbox;
- drop a failed class or slice;
- emit a sparse cell as zero;
- map a source annotation to an operational signal;
- continue after a boundary violation.

## Testing Strategy

All implementation tasks use strict tests-first development.

### Synthetic Acoustic Tests

- exact tones for fundamental-frequency summaries;
- amplitude-scaled copies proving duration and frequency invariance;
- duration-scaled fixtures proving duration sensitivity;
- silence and near-silence abstention;
- mixed voiced/unvoiced fixtures;
- clipping, malformed headers, wrong sample rate, wrong channel count, and
  non-finite feature rejection;
- exact spectral centroid, bandwidth, and roll-off fixtures;
- exact ordered 17-feature schema.

### Label And Leakage Tests

- tied perception votes abstain;
- missing votes abstain;
- intended prompt code cannot become a label;
- filename, label, vote, actor, sentence, path, and derived-proxy columns are
  rejected from the acoustic matrix;
- row-order permutation cannot change results;
- test labels cannot influence partition allocation after freeze.

### Split Tests

- actor overlap across any partition is rejected;
- sentence stratification is complete;
- source corpus is a scope constant, not a false exclusion group;
- site-generalization claims remain blocked;
- expected `35/13/13/30` actor allocation;
- quarantine never enters a fit, metric, slice, or claim denominator;
- local manifest digest changes on any assignment mutation.

### Evaluation Tests

- standardization uses training data only;
- all three model definitions are exact;
- calibration thresholds use calibration data only;
- diagnostic results cannot make calibration claims;
- paired actor-cluster bootstrap is deterministic;
- every output cell enforces the ten-actor floor;
- keep/revise/discard decisions are mutation-tested;
- lockbox open count cannot exceed one.

### AMI Tests

- exact turn, pause, overlap, floor-change, balance, backchannel, and
  dialogue-act calculations on synthetic annotations;
- unknown dependencies quarantine;
- one-meeting-per-participant contribution cap;
- sparse cell suppression;
- no transcript text or participant row in tracked output;
- official source-partition separation.

### Boundary And Publication Tests

- no network;
- no provider environment;
- no private or private-restricted path access;
- no runtime import or mutation;
- deterministic repeated-run hashes;
- exact two-file canonical directory;
- candidate tamper rejection;
- accept/reject restoration;
- output scans for paths, timestamps, speaker tokens, rows, audio, transcript,
  model objects, credentials, and operational-signal labels.

Real public material is not needed for unit or state-machine tests. A real
material run remains a separately authorized implementation-plan action.

## Expected Implementation Surface

Planned tracked additions:

```text
research/environments/emotion-state-002/requirements.lock
research/experiments/EMOTION-STATE-002-phase-b-public-data-feasibility.md
research/experiments/cases/emotion-state-002-phase-b-config.json
research/sources/emotion_state/emotion_state_phase_b_feature_v1.schema.json
research/sources/emotion_state/emotion_state_evaluation_split_v1.schema.json
scripts/emotion_state_phase_b_features.py
scripts/emotion_state_phase_b_splits.py
scripts/emotion_state_phase_b_evaluation.py
scripts/emotion_state_phase_b_ami_mechanics.py
scripts/run_emotion_state_002_phase_b.py
scripts/validate_emotion_state_002_phase_b.py
scripts/test_emotion_state_002_phase_b.py
```

Planned documentation updates:

```text
docs/product/COMMANDS.md
docs/product/CHECKPOINT_INDEX.md
docs/thesis/DECISION_LOG.md
docs/thesis/METHODOLOGY_LOG.md
docs/thesis/ROADMAP.md
research/experiments/EMOTION-STATE-001-phase-a.md
```

Planned canonical output:

```text
research/experiments/generated/EMOTION-STATE-002-phase-b-public-data-feasibility/result.json
research/experiments/generated/EMOTION-STATE-002-phase-b-public-data-feasibility/report.md
```

No planned file is under:

```text
runtime/
apps/
services/
packages/prompts/
runtime/providers/
runtime/campaigns/
runtime/voice/
data/private/
data/private-restricted/
```

The implementation plan may reduce this surface after dependency-impact
inspection, but it may not broaden it without a reviewed design change.

## Documentation Correction Prerequisite

Before implementation, correct two stale Phase A statements:

1. `docs/thesis/ROADMAP.md` still says Task 11 is the next operation.
2. `research/experiments/EMOTION-STATE-001-phase-a.md` still describes
   complete canonical publication as deferred.

The correction must record:

- accepted transaction `59324165c56446f7850e9a2abd37e4ff`;
- result SHA-256
  `EED96BADBE916A38107A4289AD951F8953A5A96215E063890E07F054C7A90931`;
- report SHA-256
  `724C81C41C489B9BBAB0896009DE7CAB578F77082F230F78B90B65643586FE8A`;
- output-only commit
  `f8ba503c3670fec6e9dee53f03f306798e7b807b`;
- Phase A's bounded completion scope;
- the fact that Phase B design approval is not model-evaluation execution
  approval.

## Execution Gates

The detailed implementation plan must stop at these gates:

1. documentation correction and design-input validation;
2. dependency provenance, license, version, and artifact-hash review;
3. synthetic feature and split contracts;
4. synthetic evaluation and AMI mechanics;
5. real-material preflight;
6. one frozen non-lockbox experiment;
7. independent review before final-lockbox opening;
8. one-use final-lockbox run;
9. independent candidate review and explicit acceptance;
10. pair-only commit.

No gate implicitly authorizes the next one. The implementation plan must state
which steps are read-only, which may install research dependencies, which may
read ignored public material, and which may open the lockbox.

## Readiness Boundary

A completed Phase B result is an offline public-data research checkpoint.

It can answer:

- whether the chosen acoustic features carry reproducible signal for
  CREMA-D's acted-perception labels under the frozen speaker-disjoint claim;
- whether confidence and abstention are calibrated enough to keep, revise, or
  discard that research lane;
- whether AMI mechanics can be derived and released deterministically under
  the contribution and suppression rules.

It cannot answer:

- how a real customer feels;
- whether a customer is hesitant, frustrated, confused, interested, or
  disengaged;
- whether acoustic adaptation improves sales dialogue;
- whether the approach works on natural calls;
- whether it is fair across demographic groups;
- whether it meets real-time latency or provider requirements;
- whether any model should be deployed;
- whether the friend project's source should be adapted;
- whether runtime, shadow, provider, private-data, or live-customer work is
  authorized.
