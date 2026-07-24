# EMOTION-STATE-003 Phase C0 Synthetic Temporal Mechanics Design

## Status

Approved for design documentation on 2026-07-24. This document defines an
offline, synthetic, correctness-only checkpoint. It does not authorize
implementation, runtime activation, provider work, data access, or Phase D.

## Goal

Build the smallest executable reference design that can prove deterministic
temporal state mechanics without treating the Phase B acoustic path as
admissible under its accepted `revise` decision.

The checkpoint may test:

- evidence priority;
- quality caps;
- logical-turn decay;
- entry, release, and switch hysteresis;
- contradiction handling;
- abstention;
- deterministic correction replay;
- event identity and session isolation;
- evidence provenance; and
- the declared monotonic constraint vocabulary carried by
  `PerceivedCustomerStateV1`.

Success means the frozen synthetic scenarios produce the expected,
byte-deterministic transitions and satisfy independent semantic invariants.
It does not mean that a model recognizes customer emotion accurately or that
a runtime policy adapter enforces the declared constraints.

## Evidence Boundary

Phase B completed as an accepted offline acted-perception checkpoint with
decision `revise`. Its final acoustic macro-F1 exceeded both baselines, but
eligible slice instability and reversal were true, confidence abstention did
not improve the result, and AMI timing and dialogue-act contributions remained
unavailable.

Phase C0 therefore must not consume:

- Phase B feature vectors;
- Phase B model outputs, probabilities, scores, or fitted parameters;
- Phase B result or report content as tracker input;
- CREMA-D or AMI rows, audio, annotations, manifests, or ignored material;
- public or private customer data;
- raw audio or transcripts; or
- any learned acoustic-to-operational-signal mapping.

The closed Phase B lockbox is immutable and must not be reopened.

## Product Review

### Real Goal

The project eventually needs a bounded way to carry perceived conversational
state across turns without allowing one noisy observation to change sales
behavior. Phase C0 addresses only the deterministic state-mechanics part of
that problem.

### Narrowest Useful Wedge

One research-only, pure reducer processes frozen symbolic evidence and emits a
contract-valid perceived state. It owns no sessions, performs no I/O, and is
not connected to prompts, responses, policy routing, providers, or calls.

### Assumption Most Likely To Be False

Synthetic support values may look like calibrated confidence even though they
are only deterministic fixture semantics. Every contract, report, and thesis
statement must preserve that distinction.

### What Will Break First

The first likely failure is silent semantic expansion: accepting unconstrained
acoustic numbers as frustration, hesitation, confusion, interest, or
disengagement. The input contract prevents this by allowing only typed
synthetic evidence atoms and rejecting feature vectors, probabilities, model
identifiers, dataset identities, and media references.

### Recommendation

Implement Phase C0 as an offline reference reducer under `scripts/`. Do not put
it in `runtime/`, merge it into the stable contract module, or create a mutable
tracker service.

## Approaches Considered

### Contract-Only Transition Oracle

This is the smallest artifact, but it proves only that expected outputs can be
written down. It does not prove an executable transition system. Rejected as
too weak.

### Offline Pure Reducer

The reducer has explicit state input/output, no hidden storage, and no external
effects. It is executable, independently testable, and cannot be activated by
runtime discovery. Selected.

### Mutable Runtime-Shaped Tracker

A service or class with internal session dictionaries would introduce
concurrency, cleanup, lifecycle, and cross-call leakage risks before runtime is
authorized. It would also make research-only mechanics appear product-ready.
Deferred.

## Architecture

```text
frozen Phase C0 policy
          +
explicit prior synthetic session state
          +
validated synthetic evidence frame
          |
          v
pure deterministic reducer
          |
          +--> explicit next synthetic session state
          |
          +--> PerceivedCustomerStateV1
                     |
                     +--> existing contract validation
                     +--> stricter Phase C0 semantic validation

frozen scenarios
    -> runner
    -> hand-authored golden checks
    -> metamorphic invariant checks
    -> aggregate-only result/report
```

The reducer interface is conceptually:

```python
advance(
    previous_state: PhaseCTemporalSessionStateV1 | None,
    frame: PhaseCSyntheticEvidenceFrameV1,
    policy: PhaseCFrozenEvidencePolicyV1,
) -> tuple[PhaseCTemporalSessionStateV1, PerceivedCustomerStateV1]
```

Invalid input raises a typed Phase C0 contract or event-identity error before
mutation. Because state is explicit and immutable from the caller's
perspective, the caller retains byte-identical prior state after rejection.

## Component Placement

The later implementation plan may create only these production-independent
components:

- `scripts/emotion_state_phase_c_contracts.py`
- `scripts/emotion_state_phase_c_temporal_tracker.py`
- `scripts/run_emotion_state_003_phase_c0.py`
- `scripts/validate_emotion_state_003_phase_c0.py`
- `scripts/test_emotion_state_003_phase_c0.py`
- `research/experiments/cases/emotion-state-003-phase-c0-policy.json`
- `research/experiments/cases/emotion-state-003-phase-c0-scenarios.json`
- `research/experiments/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics.md`
- `research/experiments/generated/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics/result.json`
- `research/experiments/generated/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics/report.md`

Existing `runtime/contracts/emotion_state_contracts.py` is imported only to
validate the final `PerceivedCustomerStateV1` in the reducer. Phase C0 does not
modify that file or any other runtime file.

Phase C0 owns `PhaseCEventWatermarkV1` and
`validate_phase_c_event_identity()` inside
`scripts/emotion_state_phase_c_contracts.py` because the research-only frame
is intentionally not a `CustomerTurnEvidenceV1`. The identity rules duplicate
only the existing session/campaign/turn/event/revision semantics. Focused
parity tests project the same synthetic identities into contract-valid empty
`CustomerTurnEvidenceV1` scaffolds and prove matching accept/reject outcomes
and watermark transitions against the existing `validate_event_identity()`.
That existing function is a test oracle only; the Phase C0 reducer does not
call it.

## Synthetic Input Contracts

### `PhaseCSyntheticEvidenceAtomV1`

Each exact-shape atom contains:

- `schema_version`, fixed to `PhaseCSyntheticEvidenceAtomV1`;
- `evidence_ref`, a unique synthetic evidence reference;
- `independence_key`, used to prevent repeated evidence from accumulating
  automatically;
- `operational_signal`, exactly one of `hesitation`, `frustration`,
  `confusion`, `interest`, or `disengagement`;
- `direction`, exactly `supports` or `opposes`;
- `modality`, exactly `text`, `dialogue`, or `acoustic`;
- `evidence_class`, from the frozen evidence-class vocabulary; and
- `quality_bucket`, exactly `high`, `medium`, `low`, or `unusable`.

Atoms contain no free numeric confidence, probability, feature vector,
timestamp, filename, dataset identity, model identity, media identity, text,
or audio.

The evidence-class vocabulary is:

- `unsolicited_explicit_statement`;
- `transcript_meaning`;
- `dialogue_context`;
- `synthetic_acoustic_symbol`; and
- `weak_behavioral_proxy`.

The policy freezes the allowed evidence-class/modality combinations:

- unsolicited explicit statement and transcript meaning are `text`;
- dialogue context and weak behavioral proxy are `dialogue`; and
- synthetic acoustic symbol is `acoustic`.

Cross-signal co-occurrence is not automatically a contradiction. Frustration
and interest, for example, may coexist. Contradiction exists only when
independent evidence both supports and opposes the same operational signal
above the frozen gross-support thresholds.

### `PhaseCSyntheticEvidenceFrameV1`

Each exact-shape frame contains:

- `schema_version`, fixed to `PhaseCSyntheticEvidenceFrameV1`;
- `fixture_only`, exactly `true`;
- `call_session_id`;
- `campaign_profile_id`;
- `campaign_profile_version`;
- `turn_id`;
- `turn_sequence`;
- `event_id`;
- `input_revision`; and
- a canonically ordered list of evidence atoms.

The frame has no wall-clock field. New turns advance only by logical turn
sequence. Corrections may target only the most recent accepted logical turn
and must increment its input revision by exactly one.

### `PhaseCFrozenEvidencePolicyV1`

The policy is an exact-shape, canonically serialized, hash-bound JSON object.
It freezes:

- schema and evidence-policy versions;
- signal, modality, evidence-class, direction, and quality vocabularies;
- evidence priority;
- integer base-support units by evidence class;
- integer quality caps;
- multimodal agreement rules;
- per-accepted-turn integer decay;
- support and opposition saturation;
- contradiction thresholds and confidence caps;
- visibility, entry, release, and switch thresholds;
- independent-confirmation counts;
- selected-signal tie priority;
- confidence-bucket thresholds;
- trajectory thresholds;
- declared allowed-effect mappings;
- exact blocked-effect ordering;
- abstention reason mappings;
- correction policy; and
- canonical signal, modality, effect, and reference ordering.

All internal arithmetic is integer or fixed-point integer arithmetic. The
policy contains no fitted, learned, optimized, or calibrated values. Its
numbers are synthetic mechanics parameters.

The initial policy identity and integers are fixed here so they cannot be
selected after observing implementation results:

- `policy_id`: `emotion-state-phase-c0-synthetic-v1`;
- `evidence_policy_version`: `emotion-state-evidence-v2`;
- internal scale and gross/net saturation: `1000`;
- base support units:
  - unsolicited explicit statement: `700`;
  - transcript meaning: `450`;
  - dialogue context: `300`;
  - synthetic acoustic symbol: `180`;
  - weak behavioral proxy: `100`;
- quality multipliers in thousandths:
  - high: `1000`;
  - medium: `750`;
  - low: `400`;
  - unusable: `0`;
- per-signal total quality cap, selected from the highest-quality nonzero
  contributing atom:
  - high: `1000`;
  - medium: `750`;
  - low: `400`;
  - no nonzero atom or unusable only: `0`;
- retained support after each accepted new logical turn: `800/1000`;
- multimodal agreement bonus: `100`, applied once per signal and turn;
- visible-candidate threshold: `200`;
- entry threshold: `550`;
- release threshold: `350`;
- challenger switch threshold: `650`;
- minimum challenger advantage over the selected signal: `150`;
- ordinary entry and switch confirmation count: `2` consecutive accepted new
  logical turns with distinct confirming independence keys;
- release confirmation count: `2` consecutive accepted new logical turns below
  the release threshold, whether or not those turns contain contributing
  atoms;
- unsolicited explicit-statement entry count: `1`;
- contradiction threshold: at least `300` gross support and `300` gross
  opposition for the same signal;
- contradiction net-support cap: `350`, applied to capped net support,
  serialized `confidence_by_signal`, confidence bucket, and selection input,
  while leaving gross supporting/opposing units intact for traceability;
- acoustic-only total support cap: `400`;
- confidence buckets:
  - low: `0..549`;
  - medium: `550..749`;
  - high: `750..1000`;
- trajectory delta threshold: `100`;
- without an incumbent, exact entry ties abstain instead of applying an
  arbitrary label priority;
- with an incumbent, a tie retains the incumbent unless the challenger meets
  every frozen switch condition;
- canonical signal order: `confusion`, `disengagement`, `frustration`,
  `hesitation`, `interest`;
- canonical modality order: `text`, `dialogue`, `acoustic`;
- canonical direction order: `supports`, `opposes`;
- canonical evidence-class order: `unsolicited_explicit_statement`,
  `transcript_meaning`, `dialogue_context`, `synthetic_acoustic_symbol`,
  `weak_behavioral_proxy`;
- canonical quality order: `high`, `medium`, `low`, `unusable`;
- canonical allowed-effect order: `preserve`, `soften`, `shorten`, `clarify`,
  `acknowledge`, `handoff`, `abstain`, `stop`;
- canonical blocked-effect order: `expand_action_set`,
  `increase_persuasion_intensity`, `create_new_close`, `override_refusal`,
  `override_do_not_call`, `rewrite_protected_text`, `exploit_vulnerability`,
  `voice_only_emotional_appeal`, `unsupported_claim`,
  `automatic_close_or_payment`;
- canonical abstention-reason order: `phase_a_no_audio`,
  `insufficient_evidence`, `contradictory_evidence`, `low_audio_quality`,
  `missing_input`, `stale_input`; and
- evidence references and independence keys use ascending ordinal string
  order.

Corrections replay but do not apply another turn-decay step. Duplicate or
rejected input applies no decay. Multimodal agreement requires at least two
distinct nonempty modalities, evidence references, and independence keys
supporting the same signal in the same accepted frame.

Every fixed-point operation rounds down toward zero. Atom units equal
`(base_support_units * quality_multiplier) // 1000`. Logical-turn decay applies
independently to gross supporting and opposing units as
`(prior_units * 800) // 1000`. After the optional agreement bonus, each gross
side saturates at `1000`. Uncapped net support is
`max(0, gross_supporting_units - gross_opposing_units)`. Capped net support is
the minimum of uncapped net support, the per-signal total quality cap, the
`400` acoustic-only cap when applicable, and the `350` contradiction cap when
applicable. Confirmation, hysteresis, visibility, confidence buckets,
trajectory, and serialization all use capped net support.

Atoms must arrive in ascending order by this exact tuple:

1. canonical signal index;
2. canonical direction index;
3. canonical modality index;
4. canonical evidence-class index;
5. canonical quality index;
6. ordinal `independence_key`; and
7. ordinal `evidence_ref`.

Any other raw order is rejected. Evidence and independence references emitted
inside state or output are ordinally sorted.

Phase C0 emits only `insufficient_evidence`, `contradictory_evidence`,
`low_audio_quality`, and `missing_input`. The policy retains
`phase_a_no_audio` and `stale_input` in canonical vocabulary order for
compatibility with the existing output contract, but Phase C0 never emits
them. Stale identity is a typed pre-mutation rejection, not an abstained state.

### `PhaseCTemporalSessionStateV1`

The explicit in-memory state contains:

- schema and policy identity;
- call-session and campaign identity;
- event watermark;
- the canonical accepted frame sequence needed for deterministic replay;
- gross supporting and opposing units by signal;
- net support by signal;
- independent confirmation state;
- prior and current selected signal;
- selected-signal tenure;
- prior emitted support needed for trajectory; and
- the canonical set of every accepted evidence reference; and
- the separate canonical set of references that currently contribute to
  emitted provenance.

Every derived field must equal a replay from the accepted frame sequence.
State is never persisted by the Phase C0 runner. Dropping the state object is
the complete cleanup operation.

## Output Semantics

Every accepted frame emits one `PerceivedCustomerStateV1` that passes the
existing contract plus a stricter Phase C0 semantic validator.

The following fields are fixed:

- `runtime_approved` is `false`;
- `valence_estimate` is `not_inferable`;
- `activation_estimate` is `not_inferable`;
- `engagement_estimate` is `not_inferable`;
- `evidence_policy_version` is exactly `emotion-state-evidence-v2`; and
- `blocked_policy_effects` contains the existing exact ten monotonic safety
  labels in canonical order.

`confidence_by_signal` is a deterministic serialization of fixed-point fixture
support into the existing zero-to-one contract range. It is not a probability,
calibration result, emotion confidence, or expected real-world accuracy.
For each emitted base or `possible_*` signal, Python constructs the number as
`capped_net_support / 1000.0`. The existing canonical JSON form is fixed to
`json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False,
allow_nan=False) + "\n"`, encoded as UTF-8 with LF bytes. Python's shortest
finite float representation is therefore the byte authority; exponent notation
is forbidden for these `0.0..1.0` values. Arithmetic remains integer until
this final contract projection.

Candidate evidence below selection threshold may be exposed only with the
existing `possible_*` vocabulary. A selected base signal must be present in
`operational_signals`. If there is no visible candidate, the list is exactly
`["none"]`.

Derived fields follow these exact rules:

- the selected base signal is emitted first, followed by nonselected visible
  `possible_*` signals in canonical signal order;
- a nonselected signal is visible only when its net support is at least `200`;
- `confidence_by_signal` and `signal_provenance_by_modality` use exactly the
  emitted signal keys;
- provenance contains only references that currently contribute supporting or
  opposing units to an emitted signal; a zero-addition repeated independence
  key is excluded;
- selected confidence bucket comes from the frozen `0..549`, `550..749`, and
  `750..1000` ranges; no selected signal always uses `low`;
- no contributing reference yields `insufficient` evidence quality;
- one contributing modality yields `text_only` for text, `acoustic_only` for
  acoustic, and `low_quality` for dialogue;
- two or more contributing modalities yield `multimodal`;
- if every contributing atom is low quality, `low_quality` takes precedence
  over the modality-derived value;
- contradiction yields trajectory `contradictory`;
- no selected signal, a newly selected signal, or a changed selected signal
  yields trajectory `insufficient_history`;
- for an unchanged selected signal, absolute net-support delta below `100`
  yields `stable`;
- for `interest`, a delta of at least `100` yields `improving` and at most
  `-100` yields `worsening`;
- for hesitation, frustration, confusion, or disengagement, a delta of at
  least `100` yields `worsening` and at most `-100` yields `improving`.

The initial declared allowed-effect policy is conservative:

- every output includes `preserve`;
- abstained or acoustic-only output allows only `preserve`;
- `interest` allows only `preserve`;
- `hesitation` declares `preserve`, `clarify`, and `acknowledge`;
- `frustration` declares `preserve`, `soften`, `shorten`, `acknowledge`, and
  `handoff`;
- `confusion` declares `preserve`, `shorten`, `clarify`, `acknowledge`, and
  `handoff`;
- `disengagement` declares `preserve`, `soften`, `shorten`, `acknowledge`, and
  `handoff`;
- `abstain` remains a vocabulary value but is not emitted as an allowed effect
  in Phase C0;
- `stop` is not selected from an emotion-state estimate; and
- no output may expand an action set, increase persuasion intensity, create a
  close, override refusal or do-not-call, exploit vulnerability, rewrite
  protected text, create unsupported claims, or automate close/payment.

These values are constraint declarations. Phase C0 has no typed text-only
decision or action/intensity lattice and therefore cannot claim that a runtime
adapter enforced monotonicity.

## Transition Algorithm

For an accepted new logical turn, the reducer performs these operations in
order:

1. validate policy identity and exact contract shape;
2. validate session, campaign, turn, event, and revision identity;
3. validate every atom before constructing candidate state;
4. decay existing support once for the accepted logical-turn advance;
5. reject an evidence-reference collision, and give a fresh reference whose
   independence key was already accepted zero new support;
6. translate evidence class and quality through the frozen integer policy;
7. accumulate gross supporting and opposing units;
8. apply the fixed multimodal-agreement rule;
9. saturate both gross sides and derive net support plus same-signal
   contradiction status;
10. apply total-quality, acoustic-only, and contradiction caps;
11. update independent confirmation state;
12. apply entry, release, and switch hysteresis;
13. derive candidate visibility, abstention, evidence quality, trajectory,
    provenance, and declared effects;
14. validate the emitted `PerceivedCustomerStateV1`; and
15. validate the stricter Phase C0 semantic invariants.

More turns do not automatically increase support. Only a new accepted frame
with a new evidence reference and independence key may add support. Saturation
prevents unlimited accumulation.

A frame with a fresh evidence reference but a previously accepted independence
key is still an accepted logical turn: normal decay applies, the new reference
is recorded in the seen-reference set, and the atom contributes zero new
support and does not enter emitted provenance.

Acoustic-only symbolic evidence is always low-capped and cannot select any
allowed effect beyond `preserve`.

## Corrections And Rejections

A correction is valid only when it:

- targets the most recent accepted `turn_id`;
- retains the same turn sequence;
- uses a new event ID;
- increments input revision by exactly one; and
- passes every frame and atom contract.

The reducer replaces that turn's prior frame and replays the entire explicit
synthetic session fold. Corrected replay must equal a fresh fold over the
canonical replacement sequence.

Evidence-reference uniqueness is evaluated against the candidate corrected
sequence. A correction may retain references from the frame it replaces, but
it may not duplicate a reference within the replacement frame or collide with
any other retained frame.

These inputs fail before mutation:

- duplicate event;
- duplicate revision;
- correction of a closed turn;
- skipped correction revision;
- stale or non-monotonic new turn;
- rebound turn ID or sequence;
- cross-session input;
- cross-campaign input;
- wrong campaign version;
- policy-version mismatch;
- malformed or unknown field;
- unknown enum value;
- duplicate evidence reference within a frame or across the candidate accepted
  session sequence;
- forbidden evidence-class/modality combination;
- raw feature, probability, model, dataset, media, transcript, or audio field;
  and
- noncanonical ordering.

The tests must prove the caller's prior-state bytes remain identical after
every rejected case.

## Abstention Semantics

Phase C0 emits exactly these abstention reasons when applicable:

- `insufficient_evidence`;
- `contradictory_evidence`;
- `low_audio_quality`;
- `missing_input`.

Stale, duplicate, or otherwise invalid event identity emits no state. It raises
a typed rejection before mutation.

Abstention reason priority is deterministic:

1. same-signal contradiction;
2. only unusable or low-quality acoustic evidence;
3. empty frame;
4. other evidence below selection/confirmation requirements.

These map respectively to `contradictory_evidence`, `low_audio_quality`,
`missing_input`, and `insufficient_evidence`. Multiple applicable reasons are
retained in canonical reason order, but the first applicable rule determines
the primary scenario-family count.

All abstained outputs:

- select policy signal `none`;
- use confidence bucket `low`;
- allow only `preserve`;
- retain `runtime_approved=false`; and
- carry at least one exact abstention reason.

For insufficient or missing evidence, there is no selected base signal.
Contradictory evidence may remain traceable through `possible_*` candidates
and provenance, but it cannot select a policy signal.

## Frozen Scenario Matrix

The scenario file is frozen and hash-bound before reducer implementation. It
contains hand-authored expected transitions for:

- each of the five operational signals;
- text-only, dialogue-only, synthetic acoustic-only, and multimodal evidence;
- cold start;
- empty, unusable, and insufficient evidence;
- independent repetition;
- duplicate evidence-reference rejection;
- accepted fresh reference with repeated independence key, normal decay, and
  zero added support;
- support saturation;
- logical-turn decay;
- entry and release hysteresis;
- challenger switching;
- deterministic ties;
- same-signal support/opposition contradiction;
- quality caps;
- multimodal agreement;
- acoustic-only capping;
- corrected latest-turn replay;
- duplicate, stale, closed-turn, and malformed input;
- cross-session and cross-campaign rejection;
- simultaneous independent sessions;
- deterministic reference, signal, and effect ordering;
- output-contract failures;
- Phase B/raw-feature/model/probability rejection; and
- byte-identical replay.

The matrix does not contain customer conversations, transcript text, audio,
dataset rows, model predictions, or call simulations.

## Verification Strategy

Verification has three independent layers:

1. **Golden traces:** hand-authored frames and exact expected transitions are
   frozen before reducer implementation.
2. **Metamorphic invariants:** duplicate event and evidence-reference
   rejection preserve prior-state bytes; repeated independence key adds no
   support; correction replay is equivalent to a fresh canonical fold; and
   session isolation, canonical serialization stability, saturation, and
   monotonic logical-turn behavior hold without copying the reducer's
   expected-output renderer.
3. **Independent semantic validator:** validates aggregates, state/output
   cross-fields, abstention semantics, provenance union, exact blocked effects,
   policy/fixture hashes, boundary flags, and non-claims independently of
   deterministic report equality.

Strict TDD applies to every implementation task. Focused RED must fail for the
intended missing behavior before production code is added. GREEN must be
followed by the focused class, the complete Phase C0 module, relevant existing
emotion-state contract tests, thesis/reference/drift/context/setup gates,
compilation, and `git diff --check`.

## Aggregate Checkpoint

The canonical generated directory contains exactly:

- `result.json`; and
- `report.md`.

The result may contain only:

- checkpoint and schema identities;
- policy, scenario, and aggregate-output SHA-256 values;
- total, passed, failed, and rejected-case counts;
- counts by scenario family, modality, signal, abstention reason, and invariant;
- deterministic replay and boundary booleans;
- complexity facts such as policy parameter count and scenario count;
- decision; and
- explicit claim-boundary booleans.

It must not contain frames, atoms, per-turn states, evidence references,
session/campaign/turn/event identities, transcript content, audio, features,
probabilities, model output, filenames, dataset rows, or provider data.

The report is a deterministic rendering of the validated result and must state
that this is a synthetic mechanics checkpoint.

## Decision Rule

The decision applies only to Phase C0 synthetic mechanics:

- `keep`: every mandatory scenario, semantic invariant, deterministic replay,
  privacy boundary, and repository gate passes;
- `revise`: the reducer executes deterministically, but one or more
  non-safety mechanical expectations fail; or
- `discard`: any safety/boundary invariant fails, including state mutation on
  rejected input, cross-session leakage, nondeterminism, acceptance of
  forbidden evidence, runtime activation, or claim expansion.

A negative result remains thesis evidence. No outcome authorizes Phase B model
reuse, a policy adapter, runtime/shadow work, provider access, or Phase D.

## Expansion Gates

### Acoustic Evidence Admission

A new versioned evaluation, not the closed Phase B lockbox, must remove
eligible slice reversal and instability, demonstrate useful abstention,
establish calibration and dependency-disjoint robustness, and retain the
acted-perception/domain limitations.

### Guarded Policy Adapter

A later design must introduce:

- a typed text-only decision;
- an explicit action and persuasion-intensity lattice;
- exhaustive differential tests proving no action expansion or intensity
  increase;
- refusal and do-not-call preservation; and
- a separate approval gate.

### Runtime Or Shadow Work

Runtime or shadow work requires a signed approved package, privacy and
retention review, lifecycle and cleanup proof, shadow evidence, and separate
ASR, PSTN, provider, latency, and call authorization.

### Customer-Emotion Claims

Synthetic and acted-perception evidence cannot establish hidden internal
emotion. The project continues to use `perceived_conversational_state`.

## Explicit Exclusions

Phase C0 design and its later implementation exclude:

- raw public or private data;
- dependency installation or update;
- network access;
- provider access;
- calls;
- provider or conversational simulations;
- source adaptation;
- prompts or response generation;
- BRAIN integration;
- product runtime changes or activation;
- learned or calibrated tracker weights;
- automatic cross-call evolution;
- lockbox access;
- merge or history rewrite;
- Phase D; and
- production, commercial, conversion, true-emotion, or real-customer claims.

Local deterministic fixture execution is an implementation-test surface, not a
conversation simulation.

## Design Approval Record

Tarik approved these sections in sequence on 2026-07-24:

1. offline reference-reducer architecture;
2. synthetic contracts and frozen fixed-point policy;
3. transition and fail-closed behavior;
4. frozen verification and aggregate checkpoint; and
5. exact design-package scope and exclusions.

Independent architecture review recommended the pure reducer under `scripts/`.
Independent red-team review identified two blocking design gaps: no admissible
acoustic-to-operational-signal mapping and no basis for a policy-enforcement
claim. This design closes both by introducing a research-only symbolic input
contract and limiting the result to deterministic mechanics plus declared
constraint vocabulary.
