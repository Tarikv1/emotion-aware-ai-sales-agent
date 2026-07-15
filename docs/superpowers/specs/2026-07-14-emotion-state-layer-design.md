# EMOTION-STATE-001 Temporal Customer-State Analysis Design

Date: 2026-07-14

Status: reviewed and approved design; offline partial Phase A contract foundation implemented; `phase_a_complete=false`; acoustic implementation, private-data work, provider work, and runtime activation remain unstarted and blocked

## Current Offline Checkpoint Boundary

The implemented offline partial Phase A runner serializes startup recovery and publication with an OS-level, non-blocking publication lock under ignored `.tmp/`. The canonical generated-artifact directory still contains exactly two files: `result.json` and `report.md`. New-file staging, file `fsync`, the transaction journal, previous-pair backups, and recovery scratch stay under ignored `.tmp/`, outside that canonical directory.

Publication is result-first/report-last: the runner stages and `fsync`s both new files, backs up the exact prior pair when present, persists the journal, replaces `result.json` first, and publishes `report.md` last. The report carries the exact result SHA-256 commit marker in the form `result.json sha256:<64-uppercase-SHA-256>`. Consumers must require `python scripts\validate_emotion_state_001_phase_a_contracts.py` to pass before treating the pair as committed.

On the next locked startup after an interruption, recovery either finalizes an exact new pair whose report marker and recorded digests match or restores the exact previous pair from verified backups. Cleanup is retry-safe when an exact new or previous pair is already canonical; corrupt or incomplete recovery evidence fails closed and is retained. This is a logical commit-and-recovery protocol, not physical two-file atomicity and not a claim of power-loss durability.

Controlled regression coverage injects 60-second subprocess timeouts at exactly six positions: two EXP-002 validator calls, one Phase A BRAIN validator call, and three Phase A checkpoint calls. Each covered timeout returns the validator's controlled exit-`1` failure message without stderr or a traceback. This is offline failure-reporting coverage only; it opens no acoustic, private-data, public-dataset, provider, runtime, real-customer, or production-readiness gate. Current-checkpoint hard stop: no ElevenLabs read or write occurred; neither an outbound call nor a customer call occurred; no simulation occurred; no source adaptation occurred; and no source-adaptation gate was opened.

## Purpose

EMOTION-STATE-001 defines how the Emotion Aware AI Sales Agent may use selected interpretable speech features from Shehzeb Iftakhar's Creative Analysis Engine to estimate a customer's perceived conversational state over time.

The goal is not to claim access to a customer's internal emotion. The goal is to combine observable audio, transcript, and dialogue evidence into a conservative, confidence-weighted state that can make the agent clearer, less pressuring, and more responsive during a conversation.

This design preserves:

```text
one reusable sales-agent core
  + configurable SalesCampaign profiles
  + explicit guardrails, consent, provider gates, and human escalation paths
```

## Approved Decisions

- Collaboration and code adaptation from Shehzeb's thesis project are authorized by user-attested author and supervisor approval, with attribution required. Permission is not a project blocker.
- Customer self-report prompts are not part of the sales call or the initial EMOTION-STATE labeling workflow.
- The system estimates `perceived_conversational_state`; it does not claim `true_emotion`.
- The live design uses an interpretable weighted temporal evidence tracker.
- End-to-end learned temporal models are deferred until the approved evidence gates are satisfied.
- Within-call state may adapt turn by turn, but no live call may update shared model weights or runtime rules.
- Cross-call evolution is offline, versioned, independently evaluated, human-approved, reversible, and unable to auto-promote itself.
- A recurring pattern across at least five unique speakers and ten independently labelled turns may become a candidate hypothesis, but is not enough evidence for runtime use.
- Raw customer audio, raw transcripts, and persistent individual emotional profiles are excluded from default live persistence.
- The acoustic layer can only reduce pressure, clarify, acknowledge, shorten, or abstain. It cannot intensify persuasion.
- The first research baseline is English-only and offline. German, PSTN, streaming, and provider-hosted integration require later evidence gates.

## Source And Provenance Boundary

The reviewed source archive is:

```text
D:\Codex\z\creative-analysis-engine-dev.zip
SHA-256: E579B966E226F2AF6E4F8F8203C7189FEC94FB448EFC09B4B6640C10A398ECCC
```

Relevant source modules include:

- `src/features/temporal/speech_prosody.py`
- `src/features/temporal/speech_turn_dynamics.py`
- `src/aggregation/speech_call_readiness.py`

The source project is not an emotion classifier. Its useful contribution is interpretable acoustic and turn-level feature extraction. Its `speech_call_readiness` and `emotion_readiness_comparison_score` outputs must not be reused as customer emotion labels.

Before copying or adapting implementation code, the implementation checkpoint must add a project-local source manifest containing:

- the GitHub repository URL;
- the source commit or archive date when available;
- the archive hash above;
- the files or algorithms adapted;
- the permission basis, recorded as project-owner attestation of author and supervisor approval dated 2026-07-14;
- the attribution wording;
- whether each element was copied, translated, or independently reimplemented;
- confirmation that the adapted code remains project-local.

The existing collaboration rationale remains documented in `docs/thesis/COLLABORATION_NOTE.md`. Any concrete code adaptation must update both the detailed immutable project-local source manifest and the canonical `docs/third-party-inspirations.md` index, which links to that manifest.

## Problem Definition

Acoustic behavior is ambiguous:

- rapid speech can indicate activation, urgency, excitement, accent, habit, or ASR segmentation error;
- long pauses can indicate hesitation, formulation, interruption, connection loss, or natural speaking style;
- loudness can indicate emphasis, microphone distance, channel gain, or frustration;
- pitch variation can indicate expressiveness, stress, language prosody, or recording artifacts.

Therefore, no single acoustic feature may produce a high-confidence emotional state. Acoustic evidence is advisory and must be interpreted against signal quality, transcript meaning, dialogue context, and the speaker's developing within-call baseline.

## Terminology

Use these terms in code, reports, and thesis claims:

- `perceived_conversational_state`: a bounded estimate from observable evidence.
- `operational_signal`: a response-relevant cue such as possible hesitation, frustration, confusion, interest, or disengagement.
- `confidence`: support for the estimate under the approved evidence model, not certainty about the customer's mind.
- `abstention`: an explicit decision that the evidence is insufficient or contradictory.
- `speaker_baseline`: a temporary within-call reference for relative acoustic change; it is never assumed emotionally neutral.
- `pattern_candidate`: an offline research hypothesis that cannot affect runtime behavior.
- `approved_pattern_version`: a versioned rule or model package that has passed the required signed shadow-authorization and runtime-activation gates.

Avoid:

- `true_emotion`;
- `emotion detected`;
- `the customer is angry/anxious/vulnerable`;
- biometric identity or personality claims;
- claims that conversion outcome proves an emotional state.

## Approaches Considered

### Rule-Based State Machine

Advantages:

- easy to inspect;
- deterministic;
- inexpensive;
- simple to test.

Weaknesses:

- universal thresholds overfit accents, microphones, languages, and speaking styles;
- state transitions become brittle as evidence conflicts;
- confidence calibration is weak.

Decision: use only for fixtures and explicit safety rules, not as the complete estimator.

### Weighted Temporal Evidence Tracker

Advantages:

- preserves evidence references and uncertainty;
- supports speaker-relative changes;
- combines text, audio, and dialogue without requiring a large neural model;
- supports decay, hysteresis, contradiction, and abstention;
- can begin deterministic and later calibrate approved weights offline.

Weaknesses:

- requires a carefully versioned evidence policy;
- still needs labelled validation data;
- poorly chosen weights can create false confidence.

Decision: recommended initial EMOTION-STATE architecture.

### End-To-End Learned Sequence Model

Advantages:

- may learn nonlinear and long-range relationships;
- may outperform hand-designed fusion with sufficient representative data.

Weaknesses:

- data-hungry;
- harder to interpret and constrain;
- easier to overfit acted or non-sales corpora;
- inappropriate before dependency-independent sales-shaped validation exists.

Decision: deferred. It may become a later experimental comparison, never the first implementation.

## Architecture

```text
transcript + dialogue context
  -> existing text-only buyer state and policy decision ----------------+
                                                                         |
customer audio turn                                                      |
  -> audio quality gate                                                   |
  -> approved acoustic feature adapter                                    |
  -> speaker-relative normalization ----+                                 |
                                         +-> temporal evidence tracker     |
transcript evidence ---------------------+          |                      |
                                                    v                      v
                                      typed de-escalation constraints -> guarded final decision

offline approved research records
  -> candidate registry
  -> frozen evaluation
  -> canonical pattern content + candidate_content_digest
  -> signed human shadow authorization
  -> shadow replay or separately approved shadow run
  -> shadow report
  -> signed human runtime-activation approval
  -> approved pattern version
```

The text-only policy decision is produced before acoustic constraints are applied. Acoustic evidence may narrow or soften that decision, but it may never expand the action set or produce a more persuasive action than the same turn without acoustic evidence.

The live core reads only an integrity-verified `approved_pattern_version`. The offline research lane cannot write directly to the live core.

## Component Boundaries

### Audio Quality Gate

Responsibilities:

- validate that a customer turn has usable audio and timing;
- record non-identifying channel and extraction quality;
- reject or downgrade clipped, silent, overlapping, truncated, or low-confidence input;
- prevent low-quality audio from increasing state confidence.

It does not:

- infer emotion;
- identify a speaker;
- infer age, gender, ethnicity, health, disability, or personality;
- upload audio to a new provider.

### Acoustic Feature Adapter

Initial eligible features:

- median pitch and pitch variability;
- pitch range when quality supports it;
- intensity mean and variability;
- voiced/unvoiced ratio;
- VAD or extraction confidence;
- pause ratio and mean pause duration;
- articulation or speech rate when transcript timing supports it;
- turn count, exchange rate, duration variability, and speaker balance when reliable speaker-labelled spans already exist.

Excluded features or behaviors:

- speaker embeddings or identity matching;
- emotion-class outputs from the source project;
- `speech_call_readiness` as emotion evidence;
- `emotion_readiness_comparison_score` as emotion evidence;
- overlap interpreted automatically as interruption intent;
- diarization claims when the input does not already supply trustworthy speaker spans;
- owner-voice personalization mappings from `VOICE-031` reused as customer-state logic.

The adapter should be project-local. The Creative Analysis Engine must not become a required whole-repository runtime dependency.

### Text And Dialogue Evidence Adapter

Responsibilities:

- detect unsolicited explicit state statements;
- record explicit refusal, stop, do-not-call, confusion, objection, interest, and clarification signals;
- carry the current buyer move and recent dialogue context;
- produce evidence references rather than hidden chain-of-thought.

Explicit refusal and stop intent always override emotional-state estimates.

### Speaker-Relative Normalizer

Responsibilities:

- maintain a temporary robust within-call baseline;
- represent acoustic changes relative to the speaker's earlier valid turns;
- cap confidence during cold start;
- avoid assuming that early turns are neutral;
- reject baseline updates from unusable audio.

The baseline ends with the call and is not reused to recognize or profile the same customer later.

All mutable baseline and tracker state is owned by one call session. Process-global customer state is forbidden. The state owner rejects events with the wrong session, campaign version, stale input revision, duplicate event ID, or non-monotonic turn sequence.

Session cleanup runs on normal end, disconnect, timeout, cancellation, and exception. Cleanup failure disables the acoustic lane and creates a private operational error without retaining the customer-state body.

### Temporal State Tracker

Responsibilities:

- combine evidence using the approved evidence priority;
- apply decay so old state does not dominate indefinitely;
- apply hysteresis so one noisy turn does not flip state immediately;
- lower confidence when modalities contradict each other;
- abstain when evidence is ambiguous;
- expose evidence references, quality, trajectory, evidence-policy version, and runtime-approval status;
- preserve typed modality provenance for every operational signal;
- emit explicit `allowed_policy_effects` and `blocked_policy_effects`.

Evidence priority:

1. unsolicited explicit customer statement;
2. transcript meaning and dialogue context;
3. agreement between text and acoustic evidence;
4. acoustic evidence alone;
5. weak behavioral proxies.

More turns do not automatically increase confidence. Only repeated, sufficiently independent, consistent evidence can increase confidence. Conflicting evidence must be able to reduce confidence.

### Guarded Sales Policy Adapter

The adapter receives the existing text-only policy decision plus typed constraints from the temporal tracker. It is a monotonic safety layer:

```text
final_allowed_actions <= text_only_allowed_actions
final_persuasion_intensity <= text_only_persuasion_intensity
```

Adding acoustic evidence can preserve, soften, shorten, clarify, hand off, or stop the text-only decision. It cannot select a stronger tactic, create a new close, or increase persuasion confidence.

Allowed influence:

- possible frustration -> acknowledge, clarify, reduce pressure, or offer an exit;
- possible confusion -> simplify or check understanding;
- possible hesitation -> ask one relevant, low-pressure question;
- possible disengagement -> shorten the response or offer to stop;
- possible interest -> continue the existing approved discovery path without increasing pressure;
- insufficient evidence -> use the normal text-based policy.

Forbidden influence:

- stronger urgency;
- pressure escalation;
- exploiting vulnerability;
- emotional appeal selected only from voice evidence;
- continuing after refusal or do-not-call;
- protected-text rewrites;
- unsupported product or outcome claims;
- automatic close or payment action.

The state tracker advises the existing sales core. It does not become a second autonomous sales agent.

## Data Contracts

### `CustomerTurnEvidenceV1`

This is a memory-only inference contract and is not serializable to normal logs.

```text
call_session_id
campaign_profile_id
campaign_profile_version
turn_id
turn_sequence
event_id
input_revision
event_timestamp
call_scoped_speaker_id
start_time_ms
end_time_ms
audio_quality_status
audio_quality_reasons
acoustic_features
acoustic_feature_confidence
transcript_signals
explicit_customer_statements
dialogue_context_refs
speaker_baseline_status
extraction_status
source_timestamps
persistence_allowed = false
```

The contract must not contain a reusable speaker identity, customer profile, raw private audio, secret, or hidden reasoning trace.

Arbitrary transcript strings are prohibited from persistable outputs. The in-memory inference path may inspect transcript text already available to the existing call core, but log and serializer boundaries accept only enumerated signal types and redacted, nonreversible evidence references.

### `CustomerTurnAuditV1`

This is a memory-only input to the operational aggregator. It is destroyed with the call and is not a default persistable record:

```text
ephemeral_audit_session_id
turn_sequence
audio_analysis_status
audio_quality_bucket
enumerated_signal_types
abstained
abstention_reason_codes
processing_latency_ms
evidence_policy_version
runtime_approved
contains_raw_audio = false
contains_raw_transcript = false
```

The audit serializer rejects unknown free-text fields.

### `OperationalAggregateV1`

This is the only default persistable live contract. It contains cohort-level counters and percentiles after at least ten eligible calls, with no call, turn, speaker, transcript, signal-label, or acoustic-vector identifier:

```text
aggregation_window
eligible_call_count
audio_analysis_availability_rate
audio_quality_bucket_counts
abstention_rate
processing_latency_percentiles
evidence_policy_version_counts
contains_call_level_rows = false
contains_raw_audio = false
contains_raw_transcript = false
contains_signal_labels = false
```

Per-turn or per-call audit persistence requires the separately approved shadow telemetry lane.

### `PerceivedCustomerStateV1`

```text
call_session_id
campaign_profile_id
campaign_profile_version
turn_id
turn_sequence
valence_estimate
activation_estimate
engagement_estimate
operational_signals
confidence_by_signal
selected_policy_signal
selected_signal_confidence_bucket
overall_evidence_quality
trajectory
evidence_refs
signal_provenance_by_modality
allowed_policy_effects
blocked_policy_effects
abstained
abstention_reasons
evidence_policy_version
runtime_approved
```

Each operational signal has its own calibrated confidence. The selected policy signal maps to the existing `low`, `medium`, and `high` bucket. High confidence still does not authorize a claim about hidden internal emotion.

The outward mapping remains compatible with the existing BRAIN-002 fields:

```text
buyer_state.emotional_signal
buyer_state.emotion_confidence
buyer_state.evidence_refs
```

Before runtime connection, the BRAIN packet contract must also add or carry alongside it:

```text
state_evidence_by_modality
allowed_policy_effects
blocked_policy_effects
text_only_policy_decision_ref
```

Without those typed fields, the acoustic lane remains offline because the existing three BRAIN-002 emotion fields cannot enforce the monotonic de-escalation invariant by themselves.

### `PatternCandidateV1`

```text
candidate_id
hypothesis
feature_definition
target_operational_signal
discovery_dataset_version
unique_speaker_count
independent_turn_count
annotation_agreement
status
runtime_influence_allowed = false
```

### `PatternPackageContentV1`

```text
pattern_version
source_snapshot_hashes
feature_schema_version
label_schema_version
speaker_split_manifest_hash
text_only_baseline
acoustic_only_result
multimodal_result
calibration_result
confidence_intervals
slice_results
known_limits
allowed_runtime_effects
blocked_runtime_effects
rollback_version
minimum_engine_version
maximum_engine_version
compatible_evidence_schema_versions
compatible_state_schema_versions
registry_sequence
```

`candidate_content_digest` is calculated over one documented canonical serialization of `PatternPackageContentV1`. The digest and all approval fields are excluded from the bytes being hashed.

### `DetachedPatternApprovalV1`

```text
approval_stage = shadow_authorization | runtime_activation
candidate_content_digest
decision
reviewer_id
decision_timestamp
approved_constraints
evidence_artifact_digests
signing_key_id
signature_algorithm = Ed25519
approval_record_digest
approval_signature
```

The approval record is detached and binds to `candidate_content_digest`. Runtime activation also binds to the completed `shadow_report_digest` through `evidence_artifact_digests`. Its digest is calculated over a canonical serialization that excludes `approval_record_digest` and `approval_signature`. The approving human signs a domain-separated message containing `approval_stage`, `candidate_content_digest`, and `approval_record_digest`. The signature, not a self-reported `reviewer_id` or recomputable digest, is the evidence of approval authenticity.

### `ApprovedPatternEnvelopeV1`

The runtime envelope contains the canonical pattern content, its candidate-content digest, the detached signed shadow authorization, the `shadow_report_digest`, the detached signed runtime-activation approval, and an `envelope_digest`. The envelope digest covers every envelope field except itself. It is an integrity checksum, not an approval credential. Shadow authorization cannot satisfy runtime activation.

Approval trust is anchored outside the envelope and pattern registry. An access-controlled `approval_trust_store` pins active reviewer public keys and maps each `signing_key_id` to one `reviewer_id`, its authorized approval stages, validity interval, and revocation status. Reviewer private keys remain outside the repository, runtime process, provider, and research pipeline. The pattern-promotion writer cannot modify the trust store.

The research pipeline may write candidates only to a staging registry. Only a separately authorized promotion command or service may write the active project-local registry, and the runtime receives read-only access to that registry. Before shadow use or runtime activation, the loader must verify the canonical content digest, approval-record digest, Ed25519 signature, active key, reviewer binding, stage authorization, constraints, engine/schema compatibility, and monotonically increasing registry sequence. A forged `reviewer_id` with recomputed digests therefore remains invalid without an authorized private-key signature.

Runtime loading is atomic, rejects unsigned, untrusted, corrupt, incomplete, replayed, downgraded, expired, revoked, or schema-incompatible envelopes, retains a last-known-good envelope, and falls back to text-only if verification or rollback fails. Trust-store changes and private-key custody require a separate security procedure and are outside the pattern-promotion path.

## Reference-Label Design

The EMOTION-STATE research workflow does not ask customers how they felt during a sales call. Routine self-report is excluded because it would distort the interaction and is not viable for the intended product experience.

### Direct Evidence

An unsolicited explicit statement such as `this is frustrating`, `I am confused`, or `I am interested but worried about price` is the strongest available conversational evidence.

The agent must not solicit an emotional statement for labeling purposes.

### Independent Observer Labels

Each labelled turn uses three independent trained reviewers.

Reviewers receive:

- the customer audio turn;
- its transcript;
- one or two preceding turns when needed for context.

Reviewers do not receive:

- model predictions;
- conversion or appointment outcomes;
- future turns;
- each other's labels.

Before production annotation, reviewers complete a codebook-calibration exercise on a practice set that is excluded from discovery and evaluation. Codebook changes require the practice set to be rerun before new labels are accepted.

Review fields:

- valence: ordinal negative to positive;
- activation: ordinal low to high;
- engagement: ordinal low to high;
- operational signals: zero or more of hesitation, frustration, confusion, interest, and disengagement;
- reviewer confidence;
- `not_inferable`.

At reviewer level, `not_inferable` is mutually exclusive with dimensional and operational labels. A reviewer either supplies the normal ratings or selects `not_inferable` with a reason code.

Use ordinal Krippendorff's alpha for the dimensional fields. Treat each operational signal as a separate binary label and calculate nominal Krippendorff's alpha per signal. Reviewer disagreement is retained. It must not be forced into a false consensus label.

Aggregation rules:

- dimensional consensus is the median of the three valid ordinal ratings;
- an operational consensus-positive label requires at least two of three reviewers to select that signal;
- `none` means all operational signals are negative and is distinct from `not_inferable`;
- two or more `not_inferable` ratings produce `label_status = not_inferable`;
- one `not_inferable` rating is treated as missing for per-signal alpha and consensus; the two inferable reviewers must agree or the result is `ambiguous`;
- no majority, unusable audio, or insufficient context produces `label_status = ambiguous`;
- `not_inferable` remains a valid label and is not silently converted to `none`;
- `not_inferable` and `ambiguous` turns are excluded from positive/negative supervised-label denominators but retained in end-to-end eligibility, abstention, and coverage metrics;
- model non-abstention on a `not_inferable` reference turn is counted as an abstention-policy error;
- direct explicit evidence is recorded as an evidence class and redacted reference, not as an unrestricted transcript quote.

### Weak Proxies

The following may be features or downstream outcome measures, but are never perceived-state reference labels by themselves:

- pitch, pauses, energy, or speech rate;
- interruption or hangup;
- appointment, purchase, rejection, or conversion;
- an LLM, provider evaluator, or emotion model prediction.

## Evidence And Promotion Gates

### Annotation Pilot

Minimum floor:

- 100 labelled customer turns;
- 20 unique speakers;
- three independent reviewers per turn.

This is an annotation-protocol floor, not proof that the model evaluation is powered. Report speaker-clustered bootstrap confidence intervals for alpha and per-label prevalence.

Per promoted label:

- point `alpha >= 0.80` with a lower 95% confidence bound of at least `0.80`: reliable enough for later shadow consideration;
- `0.667 <= alpha < 0.80`: exploratory thesis evidence only;
- `alpha < 0.667`: redefine or discard the label.

### Candidate Discovery

A recurring relationship may become a candidate when it appears across:

- at least five unique speakers;
- at least ten independently labelled turns;
- no more than two qualifying turns from one speaker.

This gate creates a research hypothesis only. It cannot update runtime behavior.

Before confirmatory evaluation, the candidate record must freeze:

- the feature relationship and direction;
- the target operational signal;
- the null comparator and minimum observed effect;
- the eligible-turn definition;
- the search budget and all candidate hypotheses already tested.

Discovery uses speaker-clustered bootstrap or permutation stability against the null comparator. Unstable candidates are discarded before the confirmatory lockbox is opened.

### Independent Validation

After discovery:

- freeze the hypothesis and feature definition;
- split at the highest dependency unit available: speaker plus call/session, dialogue dyad, source corpus, and scripted scenario;
- create dependency-disjoint training/discovery, prevalence-representative calibration, optional balanced diagnostic, and one-use prevalence-representative final-lockbox partitions;
- fit fusion weights, confidence calibration, abstention thresholds, and high-confidence thresholds only on training and calibration data;
- use a balanced matched diagnostic set only for per-label error analysis, never for runtime precision or probability calibration claims;
- preserve natural label prevalence in the calibration and final-lockbox partitions; if sampling alters prevalence, use documented sampling weights and do not treat unweighted precision or calibration as runtime-representative;
- freeze feature selection, thresholds, calibration, and the candidate family before opening the final lockbox;
- require at least 30 consensus-positive and 30 consensus-negative turns per promoted label as collection floors, while retaining every eligible turn needed to preserve prevalence;
- require at least 30 unique speakers in the final lockbox overall;
- run a mandatory simulation-based power and precision analysis using expected prevalence, speakers, turns per speaker, within-speaker correlation, abstention, and target effect; increase the collection floors to the resulting requirement;
- use paired speaker-and-call-clustered confidence intervals on the untouched final lockbox;
- open the final lockbox once for the frozen candidate family;
- control the frozen family at false-discovery rate `q <= 0.05`, or mark the results exploratory.

Run identical evaluation lanes:

```text
transcript only
acoustic features only
transcript + acoustic features
```

### Thesis Evidence Gate

Retain a candidate only when:

- annotation agreement has point `alpha >= 0.667` and a reported speaker-clustered confidence interval;
- macro-F1 is the unweighted mean across the frozen binary operational-signal labels; dimensional labels use separately preregistered ordinal metrics and do not enter this macro-F1;
- multimodal macro-F1 on the untouched final lockbox improves by at least `0.05` over transcript-only;
- the lower bound of the paired speaker-clustered 95% confidence interval for improvement is above zero;
- the `0.05` macro-F1 requirement is identified as an observed-effect floor; it does not prove the population improvement is at least `0.05` unless the confidence-interval lower bound also exceeds `0.05`;
- per-signal confidence is defined as the estimated probability that the binary observer reference label is positive for an eligible turn;
- Brier score on prevalence-representative data is the primary probabilistic-performance metric; the upper bound of the paired clustered 95% confidence interval for `multimodal Brier - text-only Brier` must be below zero;
- calibration intercept and slope are the primary overconfidence gates; acceptable bounds are preregistered from the calibration partition before opening the final lockbox, and their final-lockbox confidence intervals must remain inside those bounds;
- expected calibration error and reliability plots are reported as secondary diagnostics;
- abstentions remain errors for full-coverage macro-F1, and selective metrics separately report non-abstained coverage and risk;
- per-signal precision, recall, confusion matrices, prevalence, and support are reported;
- performance is reported across language, channel, audio quality, and campaign slices when a slice contains at least 20 labelled turns from at least ten unique speakers;
- smaller slices are reported as `insufficient_slice_evidence`, not pooled into a favorable claim.

These are initial thesis floors. New evidence may justify raising them. Lowering them requires an explicit design revision and human approval.

### Shadow-Authorization Gate

Before any shadow run:

- annotation agreement has point `alpha >= 0.80` and a lower 95% confidence bound of at least `0.80`;
- a high-confidence threshold selected on the prevalence-representative calibration partition has a lower 95% confidence bound for precision of at least `0.80` on the untouched prevalence-representative final lockbox;
- the preregistered non-abstained coverage floor is met, so precision cannot pass on a trivial prediction denominator;
- independent sales-shaped audio confirms the result;
- safety, stop-intent, and pressure-escalation tests show no regression;
- the canonical pattern content has a verified `candidate_content_digest` and rollback target;
- low-quality or ambiguous cases abstain;
- a human grants signed shadow authorization bound to the candidate digest.

Shadow authorization does not permit sales-policy influence.

### Runtime-Activation Gate

Runtime activation requires all shadow-authorization evidence plus:

- a completed shadow report using offline replay or a separately approved private-call telemetry lane;
- no differential safety invariant failure between text-only and acoustically constrained decisions;
- verified provider audio/timing feasibility, latency, retention, consent, and deletion boundaries;
- an integrity-verified approved envelope and tested last-known-good rollback;
- a separate signed human runtime-activation approval bound to `candidate_content_digest` and the completed `shadow_report_digest`, with both detached approvals included in the final envelope digest.

Passing these gates does not establish production readiness, PSTN validity, legal compliance, or real-customer effectiveness.

## Privacy And Storage Architecture

Derived acoustic features remain potentially sensitive. Pseudonymous records must not be described as anonymous.

### Live Inference Lane

Default behavior:

- process audio in memory only;
- keep the speaker baseline and state timeline only until call end;
- do not persist raw audio, raw transcript, or per-turn acoustic vectors;
- do not create a persistent individual emotional profile;
- retain only approved non-sensitive operational counters when needed.

Eligible operational counters include:

- acoustic analysis available or unavailable;
- signal-quality bucket;
- abstention count;
- processing latency;
- approved pattern version.

The counters are persisted only through `OperationalAggregateV1` after the minimum cohort size is met. Default live persistence contains no call-level or turn-level rows.

### Approved Research Lane

Separately approved private research data uses:

```text
data/private/emotion-research/
  source-manifests/
  derived-features/
  reviewer-labels/
  split-manifests/
  candidate-patterns/
  evaluation-results/
```

Private records remain untracked and follow `docs/data/PRIVATE_CALL_CENTER_DATA_POLICY.md`.

Public or synthetic fixtures may enter tracked paths only when their provenance and usage terms are documented and they contain no private customer material. Otherwise, they stay under the private research boundary.

Research records may contain:

- research call and speaker IDs;
- turn IDs and timing;
- derived features and quality fields;
- redacted text signals;
- reviewer labels and agreement;
- dataset and schema versions.

Research records must not contain:

- names, email addresses, phone numbers, addresses, account identifiers, or payment data;
- exact personal circumstances whose primary value is identifying or profiling a person;
- raw customer audio in tracked files;
- raw private transcripts in tracked files;
- provider keys or payload secrets;
- inferred protected characteristics.

Additional controls:

- IDs are pseudonymous and exist only for approved research and dependency-independent splitting across speaker, call/session, dyad, source corpus, and scripted scenario;
- cohort reports with fewer than ten unique speakers are suppressed;
- raw private audio retention is study-specific and requires an explicit reviewed rule before ingestion;
- reviewer access to private audio is limited to the approved review environment; copies, exports, screenshots, and provider uploads are blocked;
- private research data has no indefinite default retention period;
- any approved deletion or revocation must remove linked research records and derived artifacts;
- safe public artifacts contain only reviewed aggregate evidence.

Without an approved research lane, cross-call learning uses public or synthetic data only.

### Provider Boundary

This design authorizes no provider write or customer-audio upload.

Before a live provider integration:

- verify whether the provider exposes customer audio and turn timing;
- document whether audio leaves the existing call path;
- document retention, logging, cost, timeout, and retry behavior;
- document consent and deletion boundaries;
- prevent a second unreviewed audio upload;
- preserve local-only and text-only fallbacks.

The current hosted Atlas configuration must not be assumed to expose a usable real-time customer-audio stream.

### Shadow Telemetry Boundary

Default shadow mode is offline replay over public, synthetic, or approved private research records. This requires no live customer telemetry.

A future live shadow run is blocked until a separate approved telemetry design defines consent or other valid authority, sampling, minimum persisted fields, aggregation, retention, linkage, deletion, reviewer access, provider behavior, and customer-facing disclosure. The default operational counters in the live inference lane are insufficient for feature-distribution or human-agreement analysis and must not be stretched into an undeclared research corpus.

## Offline Evolution Workflow

```text
approved research snapshot
  -> reviewer consensus
  -> candidate pattern
  -> frozen dependency-independent evaluation
  -> one controlled change
  -> result and regression report
  -> canonical pattern content + candidate_content_digest
  -> human shadow authorization
  -> shadow replay or separately approved shadow run
  -> shadow report
  -> human runtime-activation approval
  -> approved runtime version or rejection
```

Rules:

- one experiment changes one feature definition, fusion rule, threshold set, or model version;
- training, validation, and test cases remain frozen during comparison;
- no scheduled job may auto-promote a candidate;
- no live call may mutate a shared model;
- runtime receives only the approved pattern package, not the research corpus;
- shadow authorization and runtime-activation approval are separate signed decisions with distinct approval-record digests; both bind to the canonical candidate-content digest, and runtime activation additionally binds to the completed shadow-report digest;
- every version records a rollback target;
- failure or drift disables acoustic influence before considering retraining.

## Drift Handling

The default live lane may monitor only its approved aggregate operational counters:

- increasing abstention;
- worsening audio quality;
- latency budget misses.

Feature-distribution drift, shadow agreement, and later human-review disagreement require offline replay or the separately approved shadow telemetry lane. They are not derivable from default live counters.

Drift may:

- create a review item;
- quarantine an approved pattern version;
- fall back to text-only;
- trigger a new offline evaluation proposal.

Drift may not:

- retrain automatically;
- change runtime thresholds automatically;
- create or extend a customer profile;
- intensify persuasion;
- bypass the signed human shadow-authorization or runtime-activation gate.

## Failure Behavior

| Failure | Required behavior |
| --- | --- |
| Poor, silent, clipped, or overlapping audio | Use text-only mode and record an abstention reason. |
| Missing or unreliable speaker separation | Disable turn-dynamics evidence. |
| No usable speaker baseline | Cap acoustic confidence at low. |
| Text and acoustic evidence conflict | Lower confidence or abstain. |
| Feature extraction exceeds latency budget | Ignore the new acoustic evidence and continue with text. |
| Duplicate, out-of-order, cross-session, or stale acoustic event | Discard it without updating the baseline or state. |
| Corrected ASR revision arrives after acoustic fusion | Recompute only before the turn deadline; otherwise discard the stale fusion result. |
| Transcript is partial or unreliable but audio is usable | Keep acoustic influence low and allow only neutral clarification or text-independent stop handling. |
| Both transcript and audio are missing or unreliable | Do not continue normal persuasion; use neutral clarification, handoff, or termination. |
| Unknown or unapproved pattern version | Reject the package and use the existing text policy. |
| Candidate-content digest, signed approval, trust-store authorization, envelope digest, schema, or engine compatibility fails | Keep the last-known-good envelope or fall back to text-only. |
| State tracker exception | Fail closed to text-only; do not block the conversation. |
| Session cleanup fails | Disable acoustic processing for that session and emit a private error without the state body. |
| Explicit refusal or do-not-call | End or follow the existing stop policy regardless of emotion estimate. |
| Drift or evaluation regression | Disable the approved pattern version and roll back. |

## Evaluation And Validation Plan

### Contract Tests

- validate all required fields and versions;
- reject reusable speaker identifiers;
- reject raw audio, raw private transcript, and secret-like fields;
- permit candidate evidence-policy versions only in offline research and shadow replay while requiring `runtime_approved = false`;
- reject any unapproved pattern version at the live runtime boundary;
- validate mapping to BRAIN-002 state fields and block runtime connection until the typed provenance and monotonic-constraint extension exists;
- reject arbitrary free text in `CustomerTurnAuditV1`;
- verify only cohort-level `OperationalAggregateV1` records persist by default;
- reject cross-session, stale-revision, duplicate-event, and non-monotonic-turn inputs;
- verify candidate-content, detached-approval, shadow-report, and envelope digests plus registry sequence, engine compatibility, and schema compatibility;
- verify approval signatures, reviewer/key binding, stage authorization, validity, and revocation; reject forged reviewer IDs and unknown, expired, revoked, or wrong-stage keys;
- verify the research pipeline cannot write the active registry, the promotion writer cannot modify the trust store, and runtime registry access is read-only;
- verify atomic load and last-known-good rollback for corrupt, incomplete, replayed, downgraded, and incompatible packages.

### Feature Tests

- deterministic synthetic WAV fixtures for pitch, energy, pause, and voiced-region changes;
- silence, clipping, short-turn, overlap, and low-signal fixtures;
- tests that audio quality caps confidence;
- tests that turn-dynamics features require supplied speaker spans.

### Temporal Tracker Tests

- cold-start confidence remains low;
- consistent multimodal evidence can increase confidence;
- contradictory evidence reduces confidence;
- old evidence decays;
- hysteresis prevents one-turn state flipping;
- explicit refusal overrides all state estimates;
- ambiguous evidence abstains;
- adding acoustic evidence never expands the text-only allowed-action set or persuasion intensity;
- simultaneous calls cannot share baseline or state;
- late, duplicate, corrected, and deliberately crossed events cannot update the wrong turn or session;
- call-end, disconnect, timeout, cancellation, and exception cleanup remove the temporary baseline and state timeline.

### Experiment Tests

- speaker, call/session, dyad, source-corpus, and scripted-scenario dependency groups never cross partitions;
- training/discovery, prevalence-representative calibration, balanced diagnostic, and final-lockbox partitions remain dependency-disjoint;
- text-only, acoustic-only, and multimodal lanes use identical cases;
- evaluation cases remain frozen during a candidate comparison;
- final thresholds are frozen before the one-use final lockbox is opened;
- probability calibration and runtime precision are computed on prevalence-representative data, not the balanced diagnostic set;
- macro-F1, Brier score, expected calibration error, precision, abstention coverage, and confidence intervals are reported;
- per-signal prevalence, support, confusion matrices, precision, recall, and selective-risk curves are reported;
- candidate-family false-discovery handling is recorded;
- mandatory clustered power and precision analysis is recorded;
- no change is accepted on a single lucky run.

### Safety Tests

- voice evidence cannot increase urgency or pressure;
- differential invariant tests compare every text-only action with its acoustically constrained result;
- hidden emotion claims never reach buyer-facing output;
- low-confidence state cannot select an emotional-appeal tactic;
- stop, refusal, disclosure, handoff, and protected text remain unchanged;
- no provider call, outbound call, or customer-audio upload occurs in offline validation.

### Privacy Tests

- tracked artifacts contain no raw private audio or direct identifiers;
- private research output remains under `data/private/`;
- generated public reports suppress small cohorts;
- no provider key or provider payload is written;
- in-memory `CustomerTurnAuditV1` records are destroyed after aggregation and contain no arbitrary transcript strings;
- persisted `OperationalAggregateV1` records contain no call-level or turn-level rows, signal labels, or acoustic vectors;
- offline shadow replay reads only public, synthetic, or approved private research records;
- live shadow telemetry remains blocked without its separate approved design;
- deletion tests cover linked derived records before real private research begins.

## Implementation Sequence

These are EMOTION-STATE internal checkpoint names, not a revision of the existing thesis phase plan. The text-and-strategy baseline must be runnable, frozen, and recorded before EMOTION-STATE implementation begins.

### EMOTION-STATE Phase A: Source Manifest, Dataset Manifests, And Contracts

- record source provenance and attribution;
- record the project-owner permission attestation;
- define the reviewer rubric, multi-label aggregation, and synthetic evidence fixtures;
- implement `CustomerTurnEvidenceV1`, `CustomerTurnAuditV1`, `OperationalAggregateV1`, `PerceivedCustomerStateV1`, pattern-content, detached-approval, and approved-envelope schemas;
- create one manifest per public dataset with exact source, version, access and usage terms, hashes, label mapping, exclusions, and domain limitations;
- state explicitly that acted or non-sales corpora support offline thesis comparison only;
- map output to BRAIN-002 fields with typed modality provenance;
- validate abstention, session isolation, persistence, and privacy rules.

### EMOTION-STATE Phase B: Smallest Offline Feature Adapter

- select features only after the evidence and label contracts are frozen;
- adapt only the smallest approved interpretable algorithms needed for the frozen experiment;
- create synthetic deterministic feature fixtures;
- keep the adapter offline and project-local.

### EMOTION-STATE Phase C: Deterministic Temporal Tracker

- implement evidence priority, quality caps, decay, hysteresis, contradiction, and abstention;
- use fixed reviewed configuration only;
- run text-only, acoustic-only, and multimodal synthetic comparisons.

### EMOTION-STATE Phase D: Public-Data Thesis Experiment

- run the annotation pilot or map compatible public labels;
- require the dataset manifest to document how every source label maps to the project rubric, which labels are excluded, and why the mapping does not imply sales-domain validity;
- freeze dependency-independent splits and the one-use final lockbox;
- compare the three evaluation lanes;
- produce keep, revise, discard, or defer evidence.

### EMOTION-STATE Phase E: Approved Sales-Shaped Research

- begin only after a separate data-governance decision;
- use approved research records, not default live-call logs;
- test sales-shaped generalization and state-policy appropriateness;
- keep runtime influence disabled.

### EMOTION-STATE Phase F: Shadow And Provider Feasibility

- run offline shadow replay only;
- perform documentation-only provider interface feasibility review without provider writes, customer audio, or live calls;
- record that real audio/timing access, latency measurement, and live shadow telemetry require a separate approved specification;
- require human shadow authorization before offline replay;
- run shadow mode with no sales-policy influence;
- keep runtime activation blocked under EMOTION-STATE-001.

Each phase is a separate checkpoint. Passing one phase does not authorize the next phase automatically.

## Out Of Scope

- ElevenLabs agent changes;
- outbound calls;
- live customer testing;
- production emotion recognition;
- PSTN, ASR, interruption, or latency validation;
- self-report questions during sales conversations;
- persistent individual emotional profiles;
- speaker identification or voiceprints;
- protected-characteristic inference;
- autonomous training, threshold changes, or runtime promotion;
- direct adoption of the complete Creative Analysis Engine;
- claims that the agent knows how a customer truly feels.

## Readiness Boundary

Completion of the first implementation checkpoints may support an offline research/prototype claim only.

It must not be described as:

- production ready;
- validated on real customers;
- validated for PSTN or noisy call-center audio;
- legally or ethically cleared for commercial emotion recognition;
- proven to improve conversion;
- proof that acoustic features reveal true internal emotion.

## References

- `docs/architecture/VOICE_FEATURE_MODULE.md`
- `docs/brain/BRAIN_001_PROJECT_BRAIN_ARCHITECTURE.md`
- `docs/brain/BRAIN_002_RUNTIME_STATE_SCHEMA.md`
- `docs/data/DATA_READINESS.md`
- `docs/data/PRIVATE_CALL_CENTER_DATA_POLICY.md`
- `docs/thesis/BASELINE_SPEC.md`
- `docs/thesis/COLLABORATION_NOTE.md`
- `scripts/raw_audio_speech_features.py`
- IEMOCAP: https://sail.usc.edu/iemocap/
- MSP-Podcast: https://ecs.utdallas.edu/research/researchlabs/msp-lab/MSP-Podcast.html
- Krippendorff reliability guidance: https://onlinelibrary.wiley.com/doi/10.1111/j.1468-2958.2004.tb00738.x
- NIST AI RMF Core: https://airc.nist.gov/airmf-resources/airmf/5-sec-core/
