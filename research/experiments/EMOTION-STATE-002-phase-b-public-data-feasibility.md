# EMOTION-STATE-002 Phase B Public-Data Feasibility

## Status

offline implementation started; dependency/public-material/model execution not
started

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

1. **Offline implementation gate:** Tasks 1, 2, 4, 5, 6, 7, 8, and 9 edit
   tracked research code/docs and run only synthetic or tracked-metadata tests.
   They require a later implementation authorization.
2. **Dependency gate:** Task 3 may access the package index and download wheels
   only through the ignored
   `.tmp/emotion-state-002-phase-b/resolver-venv/`, then install the reviewed
   wheels into the pip-free ignored evaluation environment at
   `.tmp/emotion-state-002-phase-b/venv/`. The split is required so evaluation
   runtime identity equals the reviewed lock without exempting bootstrap
   `pip`/`setuptools`. It requires explicit network/download/install authority
   and a reviewed artifact lock.
3. **Public-material gate:** Task 10 may read the two public CREMA CSVs, CREMA
   WAVs, and selected AMI annotation files from their fixed ignored roots. It
   requires explicit public-material evaluation authority.
4. **Final-lockbox gate:** Task 11 requires an explicit one-use lockbox
   authorization after independent review of the frozen non-lockbox packet.
5. **Publication gate:** Task 12 may stage, independently validate, explicitly
   accept, commit, and optionally push the exact canonical pair only under
   separately stated acceptance/push authority.

No gate implicitly grants the next gate.

## Frozen CREMA-D Label Ledger

- eligible concordant unique winners: `6570`
- summary `VoiceVote` ties: `644`
- raw audio-vote ties after a single `VoiceVote`: `204`
- unique-winner disagreements: `23`

Any implementation preflight count that differs from this ledger stops before
feature extraction. These are source-quality counts, not model results.

## Decision Boundary

A valid negative result completes the experiment and remains thesis evidence.
