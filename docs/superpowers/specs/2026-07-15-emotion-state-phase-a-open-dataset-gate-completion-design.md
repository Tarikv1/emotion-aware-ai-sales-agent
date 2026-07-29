# EMOTION-STATE-001 Offline Phase A Open-Dataset Gate Completion Design

Date: 2026-07-15

Status: approved design; specification-only checkpoint; implementation and public-dataset download remain unstarted; `phase_a_complete=false`

## Authorization And Hard Boundaries

This design follows the user-approved instruction:

> Start offline Phase A gate completion; public-dataset research and selection are allowed, but no private data, provider access, calls, source adaptation, or runtime activation.

The selected design is the open-only two-lane approach:

1. CREMA-D supplies a controlled acoustic-sensitivity lane.
2. AMI manual annotations supply a conversational-mechanics lane.

This specification authorizes no implementation or data acquisition by itself. A later reviewed implementation plan must keep the following gates closed unless the user separately opens them:

- no private or customer data;
- no read from `data/private/` or `data/private-restricted/`;
- no ElevenLabs or other provider read or write;
- no outbound call or customer call;
- no provider-hosted simulation, call simulation, or synthetic sales-conversation simulation;
- no dataset download until separately authorized;
- no source copying, translation, adaptation, or independent reimplementation from Creative Analysis Engine;
- no runtime wiring, prompt change, BRAIN-002 mutation, policy influence, or runtime activation;
- no push, merge, or history rewrite.

No dashboard test, Analysis criterion, hosted prompt or knowledge base, voice, LLM, phone setting, or provider configuration is in scope.

## Goal

The existing checkpoint has deterministic contracts and fail-closed publication behavior, but it intentionally selects zero public datasets and leaves the unique-speaker cohort-release/dedup gate unresolved.

This design closes the remaining Phase A design questions by defining:

- the exact public datasets and release pins;
- the permitted role of each dataset;
- source-label and project-label boundaries;
- immutable local hash inventories;
- quality and exclusion rules;
- dependency and speaker-dedup rules;
- the exact meaning of `phase_a_complete=true`;
- the failure behavior that keeps the gate closed.

Phase A is a provenance, manifest, contract, and privacy-gate checkpoint. It is not public-dataset evaluation, acoustic feature implementation, model training, customer-state validation, or runtime integration.

## Approved Decisions

- Select exactly two public datasets for Phase A: `crema-d-v1.0-audio-wav` and `ami-manual-annotations-v1.6.2`.
- Keep Phase A English-only.
- Use CREMA-D only for controlled acoustic-sensitivity research with its original perceived acted-emotion labels.
- Use AMI manual annotations only for speaker, timing, transcript, dialogue, and turn-mechanics research.
- Do not map either dataset to the project's operational signals of hesitation, frustration, confusion, interest, or disengagement.
- Treat Creative Analysis Engine as a pinned, interpretable evidence-design reference only.
- Do not reuse `speech_call_readiness`, `emotion_readiness_comparison_score`, or any other readiness output as an emotion label.
- Keep all dataset material under ignored `data/public/`; track only reviewed manifests, hash inventories, schemas, and aggregate metadata.
- Require dataset-namespaced, source-provided speaker or participant identifiers for public-data deduplication.
- Treat five unique speakers as discovery-only evidence, not a stable or population-level pattern.
- Suppress every releasable aggregate whose unique-speaker requirement cannot be proven.
- Keep all runtime influence flags false.

## Approaches Considered

### CREMA-D Only

This is the smallest open-data option and has enough actors for speaker-disjoint controlled analysis. It cannot test dialogue turns, overlap, exchange rate, or conversational trajectories. It was rejected as the sole Phase A selection because it would leave the friend-project turn-dynamics concepts without a suitable public conversational evidence lane.

### CREMA-D Plus AMI Manual Annotations

This is the approved approach. It separates two questions that should not share labels:

- CREMA-D asks whether acoustic features respond to controlled, externally perceived acted-emotion differences.
- AMI asks whether turn and timing mechanics are derived consistently from public speaker-aligned conversation annotations.

The separation prevents AMI dialogue mechanics from becoming invented emotion ground truth and prevents CREMA-D single utterances from being presented as conversational validation.

### Wait For Restricted Naturalistic Emotion Data

MSP-Podcast and MSP-Conversation require an academic data-transfer agreement signed by an authorized institutional representative. The user confirmed that the university cannot provide that signature. IEMOCAP also requires manual academic access and restricts commercial sharing. These corpora remain reference-only access blockers, not selected Phase A datasets.

Waiting for them would stall the open Phase A without resolving the access constraint. Bypassing their agreements is prohibited.

## Creative Analysis Engine Provenance Boundary

The private source repository is:

```text
https://github.com/WisdomBreathes/creative-analysis-engine
branch: dev
verified revision: 7cb99ea2da3016cd82d0b5f805c015a808ce4e0d
repository visibility: private
repository license metadata: absent
root LICENSE/COPYING/NOTICE file: absent
```

The local reviewed archive remains:

```text
D:\Codex\z\creative-analysis-engine-dev.zip
SHA-256: E579B966E226F2AF6E4F8F8203C7189FEC94FB448EFC09B4B6640C10A398ECCC
```

Read-only authenticated inspection proved byte equivalence only for the seven reviewed files below. It did not prove that every ZIP entry equals the repository tree.

| Path | Git blob SHA-1 |
|---|---|
| `README.md` | `f8a1afe3842b361432d8dcc061c5c5b6969cf363` |
| `docs/features/FEATURE_speech_call_readiness_analytics.md` | `b5e63a3dd9ba72f5eefc46688129aa98bf20a509` |
| `docs/features/FEATURE_speech_prosody.md` | `5d5cbd7e25dc7bce5fcf2c7fcb97448524c79f22` |
| `docs/features/FEATURE_speech_turn_dynamics.md` | `03f737ce52262fcac733016ec57f344d783a69b4` |
| `src/aggregation/speech_call_readiness.py` | `8387ae5d365d22c816e407e315701a066e745599` |
| `src/features/temporal/speech_prosody.py` | `dbadd19160affcd3aec864a9f4b77d3ed5e5a4d6` |
| `src/features/temporal/speech_turn_dynamics.py` | `4a46634ca9531e5181f72a554545083defcff59d` |

The repository provides interpretable observable features such as voiced ratio, pauses, pitch variability, intensity, articulation rate, turn count, turn duration, exchange rate, and speaker balance. It explicitly avoids opaque emotion labels. Its call-readiness aggregator consumes existing evidence and does not inspect audio, diarize speakers, or infer emotion.

The implementation checkpoint must update `research/sources/creative_analysis_engine/source_manifest.json` to record the verified repository URL, `dev` revision, seven-file equivalence scope, and absent observed license. The following fields remain fail-closed:

```text
adaptation_allowed = false
phase_b_approval.approved = false
copied_material = []
translated_material = []
adapted_material = []
independently_reimplemented_material = []
runtime_dependency_added = false
```

Friend and supervisor permission remains recorded for collaboration and attribution, but permission does not override the user's current no-source-adaptation instruction. No Phase B source-reuse gate is opened by this design.

## Dataset One: CREMA-D

### Immutable Identity

```text
dataset_id: crema-d-v1.0-audio-wav
canonical_source_url: https://github.com/CheyneyComputerScience/CREMA-D
release: v1.0
release_commit: f3b8611a309886568dfa957141775b2e05add04a
release_published_at: 2025-03-18T09:54:26Z
source_label: public-only
language: English
domain: acted isolated utterances with controlled sentences
```

The official repository describes 7,442 clips from 91 actors, 12 sentences, six acted emotion categories, four intensity levels, and crowd ratings for audio-only, visual-only, and audiovisual presentation.

### Terms And Access

The database is offered under Open Database License 1.0, while individual contents are offered under the Database Contents License. The official repository requests that users complete an access form and requires Git LFS for real media files.

An ordinary GitHub ZIP is not an acceptable data artifact because it contains Git LFS pointer stubs rather than the audio bytes. Any later acquisition must use the official release and verified Git LFS objects. An unofficial mirror cannot silently replace the canonical source.

### Selected Material

After separate download authorization, select only:

- `AudioWAV/`;
- `processedResults/summaryTable.csv`;
- the audio-only rating rows from the exact release path `finishedResponses.csv`;
- `SentenceFilenames.csv`;
- `README.md`;
- `LICENSE.txt`;
- Git LFS pointer metadata needed to verify the selected media objects.

Do not select `VideoFlash/` or video-derived visual labels. Do not use MP3 as the analysis signal when a corresponding valid WAV is available.

Do not ingest `VideoDemographics.csv` during Phase A. ActorID is already present in each selected filename. Age, sex, race, and ethnicity are unnecessary for the approved dependency grouping; any later fairness analysis using those attributes requires a separate minimization and ethics review.

### Label Semantics

Preserve the exact raw audio-perception codes and normalize them only through this frozen source-label map:

```text
A -> anger
D -> disgust
F -> fear
H -> happy
N -> neutral
S -> sad
```

The intended filename codes `ANG`, `DIS`, `FEA`, `HAP`, `NEU`, and `SAD` remain separate prompt metadata and are not substituted for the raw rater codes. Every derived record retains the raw code, normalized source label, source column, and source file path.

The intended actor prompt is not reference truth. The controlled acoustic lane uses the audio-only crowd perception evidence, including vote distributions, agreement, and abstention for ambiguous or tied cases.

The raters heard audio presentation files, while computational feature extraction will use corresponding WAV files. The manifest must record this cross-encoding modality limitation. Filename agreement alone is insufficient when the official issue list or objective duration/content checks indicate a mismatch.

The following mappings are prohibited:

```text
anger -> frustration
happy -> interest
sad -> disengagement
fear -> hesitation
neutral -> no customer concern
```

`project_label_mapping` must explicitly record that there is no mapping to the five project operational signals. CREMA-D cannot populate `PerceivedCustomerStateV1` operational labels or validate a customer-state policy.

### Quality And Exclusion Rules

The later verifier must:

- reject Git LFS pointer text masquerading as WAV content;
- reject missing, empty, zero-duration, unreadable, or structurally invalid WAV files;
- reject non-finite samples and invalid sample metadata;
- record the official known issue for `1076_MTI_SAD_XX.wav` and exclude it if the pinned release confirms the documented no-audio condition;
- inspect the WAV counterparts of every official MP3/video mismatch rather than assuming that a different encoding is valid;
- treat tied audio-only majority labels as ambiguous unless a preregistered vote-distribution rule resolves them without using test outcomes;
- retain every exclusion and reason in an immutable quality inventory;
- prove that ActorID is parsed from the filename and never split across dependency partitions;
- use sentence identity as an additional scripted-scenario dependency key.

The exact included and excluded counts are populated only after authorized local verification. They must not be guessed from the advertised 7,442 clips.

### Permitted Research Lanes

- controlled acoustic feature sensitivity;
- fixed-sentence lexical negative controls;
- speaker-disjoint acted-speech diagnostics;
- offline thesis limitations analysis.

Not permitted:

- customer emotion truth;
- sales-call or natural-conversation validation;
- operational-signal training without a separately approved annotation design;
- runtime influence;
- provider upload;
- redistribution from this project.

## Dataset Two: AMI Manual Annotations

### Immutable Identity

```text
dataset_id: ami-manual-annotations-v1.6.2
canonical_source_url: https://groups.inf.ed.ac.uk/ami/download/
release: AMI manual annotations v1.6.2
release_date: 2017-04-10
source_label: public-only
language: English
domain: scenario-based and naturally occurring multi-party meetings
```

The selected release is the official 22 MB manual-annotation archive. The official page states that its annotations were unchanged from the 2014-06-16 release and that the license was changed to CC BY 4.0 in the 2017 release.

### Selected Material

After separate download authorization, select only:

- the official `AMI manual annotations v1.6.2` archive;
- the extracted NXT metadata, speaker-aligned orthographic transcripts, timing links, dialogue acts, and official partition metadata contained in that release;
- the official release/license page captured as provenance metadata.

Do not select AMI audio, video, automatic annotations, DOME annotations, social-role annotations, or speculative emotion material during Phase A.

### Label Semantics

AMI supplies no emotion reference labels for this project. The official annotation documentation states that the speculative emotion annotations are not generally available and that coding instructions do not imply released annotations.

Allowed source annotations are limited to their original structural meanings, such as:

- participant or speaker association;
- word and utterance timing;
- transcript boundaries;
- turn continuation and completion;
- disfluency and nonverbal transcript markers where actually released;
- dialogue-act categories where actually released;
- official meeting and partition membership.

`project_label_mapping` must be empty for emotion and operational signals. Dialogue acts, pauses, overlap, floor maintenance, or backchannels cannot be relabeled as hesitation, frustration, confusion, interest, or disengagement.

### Dependency And Quality Rules

The later verifier must:

- hash the exact downloaded archive before extraction;
- hash every selected extracted file in a stable path-sorted inventory;
- validate that all selected paths remain under `data/public/emotion-state/ami-manual-annotations-v1.6.2/`;
- preserve participant, meeting, meeting-series, site, and scenario identifiers as dependency keys where available;
- never split a participant or four-meeting scenario series across an evaluation boundary;
- record that some TNO participant metadata was not gathered;
- block any later speaker-dependent evaluation over records whose participant identity cannot be verified;
- record documented synchronization and dropout limitations even though Phase A selects no media;
- retain the official scenario and full-corpus partition definitions as source metadata without assigning project cases during Phase A.

The current `split_manifest_v1.schema.json` cannot represent every required AMI dependency without loss. The implementation must leave v1 readable and add `split_manifest_v2.schema.json` with these exact dependency dimensions in every partition:

```text
speaker
call_session
dialogue_dyad
source_corpus
scripted_scenario
meeting_series
recording_site
```

The AMI mapping is:

```text
participant ID -> speaker, required
meeting ID -> call_session, required
four-meeting day or shared series ID -> meeting_series, required for scenario series
documented standalone non-scenario meeting -> meeting_series is not_applicable
recording location -> recording_site, required
AMI dataset manifest ID -> source_corpus, required
scenario identity -> scripted_scenario, required for scenario meetings and not_applicable for documented natural meetings
multi-party meeting -> dialogue_dyad is not_applicable, never fabricated
```

The CREMA-D mapping is:

```text
ActorID -> speaker, required
dataset manifest ID -> source_corpus, required
sentence code -> scripted_scenario, required
call_session -> covered_by_higher_dependency(speaker), subject to verified nesting
meeting_series -> not_applicable for isolated utterances
dialogue_dyad -> not_applicable for isolated utterances
recording_site -> advisory and not_available; no site-generalization claim allowed
```

The source paper describes actor recording sessions in a sound-attenuated environment but does not expose a recording-site key in the selected release. Phase A therefore records site as an uncontrolled, unavailable advisory dependency rather than pretending it does not exist. CREMA-D remains eligible only for the approved exploratory controlled-sensitivity lane; it cannot support site-independent, collection-setting-independent, or confirmatory promotion claims.

Every split-manifest validator must reject dependency overlap across training/discovery, calibration, diagnostic, and lockbox partitions. Dependency requirements use exactly:

```text
required
covered_by_higher_dependency
advisory
not_applicable
```

`covered_by_higher_dependency` requires a named resolved covering key and a verified nesting rule; the validator must prove that the covering group never crosses partitions. If CREMA-D recording-session-to-speaker nesting cannot be verified from the pinned source metadata, `call_session` becomes `advisory/not_available` and every session-independent claim remains blocked.

`not_applicable` is allowed only when the dataset definition proves that a dimension does not exist, such as `dialogue_dyad` for isolated CREMA-D clips or multi-party AMI meetings. `required/not_available` means a dependency that should exist is unresolved; that record must enter `dependency_unknown_quarantine` and cannot enter any training, calibration, diagnostic, lockbox, metric, or claim denominator. `advisory/not_available` may enter an explicitly exploratory lane only when the manifest blocks confirmatory promotion and every generalization claim involving that dimension. Unknown records cannot be distributed across partitions or treated as mutually independent.

The v2 schema therefore includes:

```text
dependency_status_by_key
dependency_requirement_by_key
dependency_applicability_reason_by_key
dependency_covering_key_by_key
dependency_unknown_quarantine.case_ids
dependency_unknown_quarantine.reason_codes
dependency_unknown_quarantine.claims_allowed = false
confirmatory_claims_allowed
```

A later reviewed design may confine a particular unknown-dependency class to one non-confirmatory partition, but Phase A chooses the simpler fail-closed quarantine rule.

### Permitted Research Lanes

- transcript-derived turn-boundary checks;
- speaker-balance and exchange-rate mechanics;
- overlap and timing-schema validation when supported by released annotations;
- dependency-group and dedup test design;
- offline thesis limitations analysis.

Not permitted:

- prosody evaluation without a later approved AMI audio selection;
- emotion or operational-signal labels;
- sales or customer-state claims;
- runtime influence;
- provider upload;
- redistribution from this project.

## Dataset Manifest Architecture

The implementation must retain every required field in `research/sources/emotion_state/dataset_manifest_contract.json` and create one immutable manifest per selected dataset under:

```text
research/sources/emotion_state/datasets/
  crema-d-v1.0-audio-wav.manifest.json
  ami-manual-annotations-v1.6.2.manifest.json
```

Each manifest must include the existing required fields:

```text
dataset_id
canonical_source_url
release_or_version
accessed_on
terms_or_license
access_restrictions
local_file_hashes
source_label
source_labels
project_label_mapping
excluded_labels
language
domain
domain_limitations
permitted_research_lanes
redistribution_status
```

The contract should add structured fields without weakening the existing ones:

```text
manifest_version
selected_artifacts
source_revision
release_published_at
dependency_keys
quality_rules
known_issues
exclusion_inventory
hash_inventory
completion_status
runtime_influence_allowed
```

The selected-dataset gate requires the v2 split schema above even though Phase A leaves all case partitions unpopulated. This makes the future no-leakage rule representable before data assignment begins.

Raw public data remains ignored under:

```text
data/public/emotion-state/crema-d-v1.0/
data/public/emotion-state/ami-manual-annotations-v1.6.2/
```

Tracked manifests must not embed raw audio, unrestricted transcript content, biometric templates, or private identifiers.

## Hash Inventory Design

`local_file_hashes` must not be an unverified count or a single directory name. It must reference a tracked, deterministic inventory containing:

```text
algorithm = SHA-256
path normalization = project-relative forward-slash paths
ordering = ascending ordinal path order
one entry per selected local file
inventory file SHA-256
selected file count
selected byte count
```

The manifest stores the hash-inventory path and its own SHA-256 digest. The validator recomputes every selected file hash and the inventory digest.

For CREMA-D, the validator must also compare each downloaded Git LFS object's declared OID with the independently computed local SHA-256 where the pointer metadata exposes that OID.

For AMI, no official checksum is currently relied upon. The manifest must state that the locally computed archive hash pins the exact bytes retrieved from the canonical source on `accessed_on`; it must not misrepresent that hash as publisher-signed evidence.

Any missing file, extra selected file, hash mismatch, case collision, pointer stub, or path escape fails the gate. A changed remote artifact requires a new manifest version and review; it cannot silently overwrite the pinned release.

## Unique-Speaker Cohort-Release And Dedup Gate

### Why A Separate Gate Is Required

Ten call records do not prove ten speakers. Repeated calls or many turns from one speaker can create a false pattern. Call IDs, session IDs, and turn IDs therefore cannot substitute for a deduplicated speaker basis.

The gate must be testable entirely with synthetic and public metadata. It opens no live identity mechanism and reads no customer data.

### Allowed Speaker Bases

```text
public_dataset_actor_id namespaced by dataset_manifest_id
public_dataset_participant_id namespaced by dataset_manifest_id
synthetic_fixture_speaker_id
privacy_reviewed_pseudonymous_cohort_token
```

For public data, the dedup key is exactly the tuple `(dataset_manifest_id, source_speaker_id)`. A bare ActorID or participant ID is invalid. Dataset-local keys do not prove that two records from different corpora represent different natural people, so datasets may not be pooled to reach a unique-speaker threshold unless an independently reviewed cross-corpus identity source proves that distinction. Phase A provides no such source.

`privacy_reviewed_pseudonymous_cohort_token` is reserved and disabled until a separate privacy and security review approves its derivation, retention, rotation, deletion, access, and threat model.

Forbidden speaker bases include:

- call ID, session ID, or turn ID treated as a speaker;
- raw name, phone number, email address, account ID, or CRM identifier;
- audio fingerprint, voiceprint, speaker embedding, or biometric match;
- a provider evaluator or model prediction;
- an undocumented hash of a direct identifier;
- probabilistic dedup presented as certain identity.

### Three Different Thresholds

The design preserves three separate thresholds:

1. **Candidate discovery:** at least five unique speakers and ten independently labelled turns, with no more than two qualifying turns from one speaker. This creates a research hypothesis only.
2. **Contribution-limited aggregate release:** at least ten proven unique speakers in the aggregation window. At most one eligible call or source session per speaker may contribute. Select the earliest eligible record by source timestamp, with a canonical record digest as the tie-breaker; if those fields are unavailable, suppress rather than choose nondeterministically. The aggregate emits no speaker token or per-speaker row.
3. **Confirmatory promotion:** an untouched final lockbox with at least 30 unique speakers overall, at least 30 consensus-positive and 30 consensus-negative turns per promoted label, and the existing statistical simulation-based power and precision requirement. These are collection floors, not assertions that every analysis is powered. The later numerical power analysis may raise them. It is not a provider, call, or conversation simulation and is not executed by this Phase A design.

The five-speaker discovery floor can never satisfy aggregate release or confirmatory promotion.

### Release Contract

Add an offline `CohortReleaseEvidenceV1` contract with at least:

```text
release_scope
source_label
aggregation_window
input_record_count
eligible_record_count
unique_speaker_count
unique_speaker_basis
dependency_keys
max_contribution_per_speaker
dedup_evidence_digest
minimum_unique_speakers
metric_allowlist_version
minimum_unique_speakers_per_output_cell
fixed_window_id
window_overlaps_previous_release = false
previous_release_digest
release_replaces_digest
direct_identifiers_present = false
voiceprint_used = false
speaker_tokens_persisted = false
contains_per_speaker_rows = false
contains_demographic_slices = false
contains_state_or_signal_labels = false
release_status
suppression_reason_codes
runtime_influence_allowed = false
```

The Phase A metric allowlist is limited to the existing non-state operational aggregate fields:

```text
eligible_call_count
audio_analysis_availability_rate
audio_quality_bucket_counts
abstention_rate
processing_latency_percentiles
evidence_policy_version_counts
```

Every reported scalar, bucket, percentile, or version cell must independently contain contributions from at least ten unique speakers after the one-record-per-speaker cap. Cells below the threshold are omitted, not emitted as zero. Sparse cells may be combined into `other` only when the combined cell also meets the same threshold and the combination rule was frozen before seeing the release data.

Phase A permits only fixed, non-overlapping, closed aggregation windows and one release per window. It prohibits ad hoc filters, nested or overlapping windows, demographic slices, campaign slices, state/signal-label slices, and repeated queries that could reconstruct suppressed cells through differencing. A correction must replace the entire prior release, name `release_replaces_digest`, preserve the same window and allowlist, and remain auditable; it cannot publish a second complementary view.

The released aggregate may retain only the approved cohort-level metrics and unique-speaker count. It must not retain the token set used to establish uniqueness.

If uniqueness cannot be proven, `release_status` must be `suppressed`. The system must not fall back to eligible call count.

This is a suppression-based, privacy-minimized contribution gate. It is not anonymity, differential privacy, or proof that re-identification is impossible. Pseudonymous records must not be described as anonymous.

### Required Synthetic Tests

- 12 calls from 4 speakers are suppressed.
- 10 calls from 10 valid synthetic speakers can pass the cohort floor when every other rule passes.
- 20 turns from 5 speakers can create a discovery candidate but cannot be released as a ten-speaker aggregate.
- duplicate public actor IDs are deduplicated.
- identical bare speaker strings from two datasets remain separate namespaced keys but cannot be pooled to satisfy a cohort threshold.
- a missing speaker basis suppresses release.
- a call ID used as a speaker ID is rejected.
- raw phone, email, account, voiceprint, or speaker-embedding methods are rejected.
- over-contribution by one speaker is deterministically capped or suppresses the aggregate according to the frozen policy.
- an output cell supported by fewer than 10 unique speakers is omitted.
- overlapping, nested, filtered, or complementary releases are rejected.
- a replacement release must bind to the digest of the release it replaces and preserve the exact window and metric allowlist.
- output serialization contains no input speaker tokens or per-speaker rows.
- every runtime influence flag remains false.

## Reference-Label Boundary

The current project annotation schema remains an offline contract and performs no annotation during Phase A.

Public source labels must be represented as source labels, not silently transformed into project labels. Project operational signals require a separately approved observer-annotation study with blinded reviewers, preserved disagreement, explicit `not_inferable`, and no customer self-report prompt.

Neither selected dataset can create a `PatternCandidateV1` for the five project operational signals during Phase A. CREMA-D's perceived acted-emotion labels and AMI's structural annotations are deliberately outside that candidate denominator.

The following remain weak evidence or features, never reference labels by themselves:

- pitch, pause, intensity, articulation rate, or speech rate;
- interruption, overlap, turn length, hangup, or speaker balance;
- dialogue-act class;
- appointment, purchase, rejection, or conversion;
- a model, LLM, provider evaluator, or friend-project readiness score.

## Completion State Machine

### Design And Selection Approved

This specification records:

```text
selected_public_datasets = [
  "crema-d-v1.0-audio-wav",
  "ami-manual-annotations-v1.6.2"
]
dataset_download_authorized = false
dataset_evaluation_started = false
phase_a_complete = false
```

### Material Verification Pending

After separate download authorization, the implementation may retrieve only the selected canonical artifacts into ignored `data/public/`, compute the exact inventories, resolve the quality exclusions, and populate immutable manifests.

Any acquisition or verification failure leaves `phase_a_complete=false` and records the exact blocker. Partial downloads, unofficial mirrors, guessed checksums, Git LFS pointers, and unverified exclusions cannot satisfy the gate.

### Phase A Complete

`phase_a_complete=true` is allowed only when all of the following are true:

- the Creative Analysis Engine source manifest records the verified private repository URL, `dev` revision, seven-file equivalence scope, absent license, and no-adaptation state;
- exactly two selected public-dataset manifests exist;
- every selected artifact has a verified local SHA-256 inventory;
- CREMA-D source-label, rating-modality, quality, dependency, and domain limitations are explicit;
- AMI's non-emotion role, selected annotation-only scope, dependency limits, and domain limitations are explicit;
- the unique-speaker cohort-release/dedup contract and synthetic tests pass;
- the v2 split schema represents every required dependency key and rejects cross-partition overlap;
- selected dataset IDs are reflected consistently in the Phase A case, result, report, product documentation, and thesis logs;
- every public-data, privacy, contract, JSON, trace, setup, drift, and diff validator passes;
- no runtime consumer imports or uses the new manifests or cohort evidence;
- scoped change and execution evidence records no provider operation, call, provider-hosted simulation, call simulation, synthetic sales-conversation simulation, private-data operation, source adaptation, or runtime operation by the Phase A change set during the captured verification window.

The completion artifact must carry an explicit scope field equivalent to:

```text
phase_a_completion_scope = source_provenance_dataset_manifests_offline_contracts_and_cohort_release_gate_only
```

All later readiness flags remain false.

## Expected Implementation Surface

The later implementation plan may modify only the reviewed offline contract and documentation surface needed for this checkpoint, including:

- `research/sources/creative_analysis_engine/source_manifest.json`;
- `research/sources/emotion_state/dataset_manifest_contract.json`;
- the two immutable dataset manifests and their tracked hash inventories;
- `split_manifest_v2.schema.json` with the approved dependency dimensions and v1 compatibility tests;
- a cohort-release evidence schema or contract;
- synthetic cohort/dedup fixtures;
- the existing Phase A case, builder, runner, validator, and focused tests;
- product documentation, thesis methodology/decision/readiness records, command maps, setup registration, and drift registration;
- the canonical Phase A `result.json` and `report.md` pair after every gate passes.

The implementation must not modify:

- hosted provider state;
- ElevenLabs agents, prompts, knowledge bases, tools, Analysis criteria, voices, LLMs, or phone settings;
- runtime prompts or campaign behavior;
- BRAIN-002 runtime state;
- call orchestration;
- private data policies to weaken them;
- source code from Creative Analysis Engine;
- unrelated dashboard or product behavior.

## Verification Strategy

Implementation must be test-driven and fail closed. At minimum, verify:

- exact source URLs, releases, commits, licenses, and selected artifact names;
- exact dataset count and ordering;
- exact local hash inventories and file counts;
- CREMA-D media are real WAV bytes rather than Git LFS pointer stubs;
- known quality issues and every exclusion are recorded;
- source labels cannot populate project operational signals;
- AMI cannot present dialogue or timing annotations as emotion labels;
- all v2 dependency dimensions are represented and disjoint across populated partitions;
- duplicate speakers cannot inflate discovery or aggregate counts;
- unique-speaker evidence is absent from released row-level output;
- forbidden identity and biometric methods are rejected;
- missing dedup evidence suppresses release;
- baseline fingerprints remain unchanged unless the implementation plan explicitly identifies and approves a required checkpoint fingerprint update;
- live-runtime consumer import scans return the expected no-match result;
- scoped private-path, provider, call, provider-simulation, call-simulation, sales-conversation-simulation, source-adaptation, and runtime-activation scans return the expected no-match result over executable changed files and their Phase A dependency closure;
- JSON, traceability, reference, setup, drift, focused runtime-contract, thesis, and `git diff --check` validators pass.

If any validator times out or fails, preserve the exact error, distinguish passed work from blocked work, do not publish a success pair, and do not claim completion.

### Auditable Forbidden-Action Evidence

A global repository text scan cannot prove that no forbidden operation occurred: the repository already contains unrelated provider and call code, while this specification itself must contain boundary wording. The implementation must instead bind its evidence to an exact change set and execution window.

The Phase A result records:

```text
implementation_baseline_commit
repository_head_commit
verification_run_id
verification_input_path_inventory_digest
executable_dependency_closure_digest
executed_command_ledger_digest
guard_policy_digest
verification_input_tree_digest
provider_environment_scrubbed = true
private_path_guard_enabled = true
network_guard_enabled = true
```

`implementation_baseline_commit` is captured as the approved specification commit before implementation begins. The canonical verification-input inventory contains one path-sorted entry for every staged, unstaged, and untracked changed input file except the canonical output pair and ignored transaction state:

```text
path
git_state = staged | unstaged | untracked
git_mode
sha256
```

When one path has both staged and unstaged bytes, both states and both SHA-256 values are recorded. The dependency-closure inventory uses path, Git mode, and SHA-256 for every reachable executable file. `guard_policy_digest` covers the exact environment-scrub, private-path, network, import, subprocess, and publication-guard policy bytes.

The verification-input inventory explicitly excludes:

```text
research/experiments/generated/EMOTION-STATE-001-phase-a-contracts/result.json
research/experiments/generated/EMOTION-STATE-001-phase-a-contracts/report.md
.tmp/emotion-state-001-phase-a-publication/**
```

Only the exact canonical output pair and ignored transaction state above may be excluded; all source, contract, manifest, test, documentation, registration, and policy inputs remain byte-bound.

`verification_input_tree_digest` binds the baseline commit, repository HEAD, canonical verification-input inventory, dependency-closure inventory, dataset-manifest and hash-inventory digests, command ledger, and guard-policy digest. `verification_run_id` is derived from that input digest and the validator version. The logical execution window starts when the guarded validator process begins and ends when that process exits; wall-clock timestamps do not enter the canonical deterministic result.

Under the existing OS publication lock, the runner recomputes every verification-input SHA-256, Git state, Git mode, closure edge, and component digest. Any input change aborts publication. It then generates deterministic `result.json` containing the normalized input evidence, hashes those final result bytes, generates `report.md` with the result hash marker, and passes the pair to the existing transactional publication protocol. The result never hashes itself, and `verification_input_tree_digest` never claims to describe the output pair. Input evidence covers the committed diff from the baseline plus every uncommitted input path at validation time. Dependency-closure evidence covers imports and subprocess targets reachable from the changed Phase A executables, not unrelated repository modules.

Every Phase A child process runs with provider credential variables removed from its environment; secret values are never logged. Focused tests deny network connection attempts and reads from `data/private/` or `data/private-restricted/`. The deterministic executed-command ledger records sequence number, command identity, working directory, and exit status without wall-clock timestamps, environment values, or secrets.

The normalized changed-path inventory, dependency-closure inventory, command ledger, guard-policy identity, and their component digests are embedded deterministically inside `result.json`. Dataset file-hash inventories remain in their separately tracked immutable manifest paths and are bound into `result.json` by SHA-256. No third file is added to the canonical generated-artifact directory.

The existing publication contract remains unchanged: the canonical directory contains exactly `result.json` and `report.md`; publication uses the OS lock, ignored `.tmp/` staging, file `fsync`, journal, verified previous-pair backups, result-first/report-last replacement, startup recovery, and cleanup. `report.md` contains the exact marker `result.json sha256:<64-uppercase-SHA-256>`. Consumers must require the focused validator to pass before accepting the pair.

The completion claim is therefore limited to the observed Phase A change set and captured run. Static scans, environment scrubbing, path/network guards, and the command ledger are corroborating evidence; none is described as proof about all activity on the machine or all pre-existing repository code.

## Failure And Rollback Behavior

- No manifest is complete while its `local_file_hashes` inventory is absent or unverified.
- No remote change may be accepted under an existing manifest version.
- No missing source label may be filled from an intended actor prompt or filename without recording that provenance.
- No AMI annotation may be assigned an emotion meaning that the source did not provide.
- No cohort report may be released by counting calls when speaker uniqueness is unknown.
- No incomplete aggregate may be promoted into a pattern candidate.
- No candidate may influence runtime.
- Any integrity or provenance failure preserves the last valid Phase A artifact pair and leaves `phase_a_complete=false`.
- Rollback affects offline manifests and generated checkpoint artifacts only; there is no provider or runtime rollback because this phase changes neither.

## Readiness Boundary

Passing this design's implementation gate would establish a bounded offline research/prototype checkpoint:

- exact provenance for the reviewed friend-project evidence reference;
- exact selection and local integrity of two public datasets;
- honest separation of acted acoustic labels from conversation mechanics;
- a privacy-minimized, contribution-limited, fail-closed unique-speaker cohort-release contract without anonymity or differential-privacy claims;
- deterministic offline validation.

It would not establish:

- a customer's true or internal emotion;
- accuracy for hesitation, frustration, confusion, interest, or disengagement;
- public-dataset model performance;
- acoustic feature implementation;
- sales-call, real-customer, PSTN, ASR, streaming, or latency performance;
- provider feasibility;
- safety or commercial effectiveness in live conversations;
- production readiness;
- source adaptation approval;
- shadow authorization;
- runtime activation.

## Primary Sources

- CREMA-D official repository: https://github.com/CheyneyComputerScience/CREMA-D
- CREMA-D release `v1.0`: https://github.com/CheyneyComputerScience/CREMA-D/releases/tag/v1.0
- CREMA-D paper: https://pmc.ncbi.nlm.nih.gov/articles/PMC4313618/
- Open Database License 1.0: https://opendatacommons.org/licenses/odbl/1-0/
- Database Contents License 1.0: https://opendatacommons.org/licenses/dbcl/1-0/
- AMI corpus overview: https://groups.inf.ed.ac.uk/ami/corpus/
- AMI download and release page: https://groups.inf.ed.ac.uk/ami/download/
- AMI manual annotation documentation: https://groups.inf.ed.ac.uk/ami/corpus/annotation.shtml
- AMI transcript documentation: https://groups.inf.ed.ac.uk/ami/corpus/transcription.shtml
- AMI official partitions: https://groups.inf.ed.ac.uk/ami/corpus/datasets.shtml
- AMI documented data problems: https://groups.inf.ed.ac.uk/ami/corpus/dataproblems.shtml
- MSP-Podcast access reference: https://lab-msp.com/MSP/MSP-Podcast.html
- MSP-Podcast data-transfer agreement: https://lab-msp.com/MSP/publications/Busso-FDPDTUA-MSP-Podcast-v4.pdf
- MSP-Conversation access reference: https://lab-msp.com/MSP/MSP-Conversation.html
- IEMOCAP release form: https://sail.usc.edu/iemocap/release_form.php
