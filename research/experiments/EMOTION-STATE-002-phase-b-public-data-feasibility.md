# EMOTION-STATE-002 Phase B Public-Data Feasibility

## Status

offline implementation complete through Task 9; reviewed dependency environment
complete; independent Task 9 gate pending; public-material/model execution not
started

Task 9 is implemented; its independent review gate must pass before Task 10. Task 10/public-material evaluation, the final lockbox, canonical staging/acceptance, push, and merge remain blocked.

## Question

Determine whether a frozen, interpretable acoustic feature vector contains
speaker-independent information about CREMA-D's original six audio-perception
labels, while separately proving that AMI manual annotations can produce
deterministic, privacy-minimized conversational-mechanics aggregates.

Phase B is a public-data feasibility study. It does not estimate customer
internal emotion and does not map either dataset to hesitation, frustration,
confusion, interest, or disengagement.

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

## Boundary Gates

1. **Offline implementation gate:** Task 9 is implemented, but its independent
   review gate remains pending and must pass before Task 10. Task 9 runs only
   synthetic fixtures, tracked metadata, and the reviewed
   dependency-environment identity; it reads no public material.
2. **Dependency gate:** Task 3 was separately authorized and completed. Any
   dependency recreation or change may access the package index and download
   wheels only through the ignored
   `.tmp/emotion-state-002-phase-b/resolver-venv/`, then install the reviewed
   wheels into the pip-free ignored evaluation environment at
   `.tmp/emotion-state-002-phase-b/venv/`. The split is required so evaluation
   runtime identity equals the reviewed lock without exempting bootstrap
   `pip`/`setuptools`. A rerun requires new explicit network/download/install
   authority and a reviewed artifact lock.
3. **Public-material gate:** Task 10 remains blocked. Only after the Task 9
   independent gate passes may a new explicit public-material authorization
   permit reading the two public CREMA CSVs, CREMA WAVs, and selected AMI
   annotation files from their fixed ignored roots.
4. **Final-lockbox gate:** Task 11 remains blocked and requires an explicit
   one-use lockbox authorization after independent review of the frozen
   non-lockbox packet.

The production lockbox evaluator remains unavailable; authorization alone does not wire it.
5. **Publication gate:** Task 12 may stage, independently validate, explicitly
   accept, commit, and optionally push the exact canonical pair only under
   separately stated acceptance/push authority.

No gate implicitly grants the next gate.

## Task 9 Validation Interface

The validator requires exactly one section:

```text
source
contracts
environment
synthetic
candidate --receipt .tmp/emotion-state-002-phase-b/publication/receipt.json
checkpoint
```

`candidate` requires an injected-test or production `awaiting_acceptance`
transaction held under the shared publication authority while the journal,
receipt, state, result, and report are independently rebuilt and compared.
`checkpoint` requires accepted state, no live journal or receipt, and exactly
the state-bound canonical result/report pair. The production defaults currently
have neither lifecycle state and therefore fail closed.

Synthetic mutation coverage binds every result mapping shape and scalar leaf,
the renderer-owned report lines, receipt hashes, the one-use lockbox count, the
derived decision, the minimum contributor floor, and every closed-boundary
flag. Candidate bytes are rejected if they expose absolute paths, timestamps,
filenames or clip stems, actor/speaker/participant identifiers, row
arrays, transcripts, audio payload markers, model serialization,
probabilities, credentials, or hesitation, frustration, confusion, interest,
or disengagement.

## Frozen CREMA-D Label Ledger

- eligible concordant unique winners: `6570`
- summary `VoiceVote` ties: `644`
- raw audio-vote ties after a single `VoiceVote`: `204`
- unique-winner disagreements: `23`

Any implementation preflight count that differs from this ledger stops before
feature extraction. These are source-quality counts, not model results.

## Decision Boundary

A valid negative result completes the experiment and remains thesis evidence.
