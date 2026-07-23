# EMOTION-STATE-002 Phase B Public-Data Feasibility

## Status

Task 10 non-lockbox checkpoint independently reviewed and accepted;
final-lockbox and canonical gates remain unopened

The single Cut 4E replacement child exited `0` after `797.5s`. The committed
state is `non_lockbox_complete`, `912` bytes, SHA-256
`8BB141DFBF651889F0E1FD66C2DF35FF31F8DC211D98A7CD27512AE7D82ACC20`.
Independent aggregate-only review returned `NON_LOCKBOX_PACKET_PASS`,
`SEMANTIC_REPLAY_PASS`, `PRIVACY_PASS`, `ZERO_LOCKBOX_ACCESS_PASS`, and
`C0 I0`.

The retired lineage is not reused or mutated.

Final lockbox access, canonical publication, merge, runtime activation, Phase C,
providers, private data, calls, simulations, and source adaptation remain
blocked. The old `.tmp/emotion-state-002-phase-b/venv` and
`.tmp/emotion-state-002-phase-b/dependencies/wheelhouse` remain immutable
dependency inputs only.

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

1. **Offline implementation gate:** Task 9 and the Cut 4A source-contract
   correction passed independent review. The Cut 4B endpoint-admissibility,
   Cut 4C AMI source/range corrections, and Cut 4D published timing-matrix
   correction are committed and independently reviewed. The Cut 4E
   non-lockbox transaction and aggregate-only replay passed.
2. **Dependency gate:** Task 3 was separately authorized and completed. Any
   dependency recreation or change may access the package index and download
   wheels only through the ignored
   `.tmp/emotion-state-002-phase-b/resolver-venv/`, then install the reviewed
   wheels into the pip-free ignored evaluation environment at
   `.tmp/emotion-state-002-phase-b/venv/`. The split is required so evaluation
   runtime identity equals the reviewed lock without exempting bootstrap
   `pip`/`setuptools`. A rerun requires new explicit network/download/install
   authority and a reviewed artifact lock.
3. **Public-material gate:** Completed for the non-lockbox checkpoint. Exactly
   one Cut 4E child used the fixed public CREMA CSV/WAV and selected AMI
   authorities. The retired split/preflight/non-lockbox lineage under
   `.tmp/emotion-state-002-phase-b` was neither reused nor mutated.
4. **Final-lockbox gate:** Task 11 remains blocked and requires an explicit
   one-use lockbox authorization after independent review of the frozen
   non-lockbox packet.

The production lockbox evaluator remains unavailable; authorization alone does not wire it.
5. **Publication gate:** Task 12 may stage, independently validate, explicitly
   accept, commit, and optionally push the exact canonical pair only under
   separately stated acceptance/push authority.

No gate implicitly grants the next gate.

The frozen configuration still contains
`emotion-state-crema-interpretable-acoustic-v1` solely as the immutable
seed-lineage compatibility token that preserves deterministic actor assignment
and model seed `618797162`; it is not an active schema selector. New production
execution selects only the fixed v2 schema path, static SHA-256
`C2A7DE308BAD32C3798016061777669881E7FDD3403979DCCC166DCE38F307C4`, and
semantic SHA-256
`AEC550285DF6A92B3E86E16F66A2E5B554836BBE47C625106F517EB0CF1375DB`.

## Task 10 Non-Lockbox Result

The fixed actor-disjoint partitions contain:

| Partition | Records | Unique actors |
| --- | ---: | ---: |
| Training discovery | 2,491 | 35 |
| Calibration | 959 | 13 |
| Balanced diagnostic | 939 | 13 |

Every record has exactly `17` acoustic features. On the balanced diagnostic
partition:

- acoustic macro-F1: `0.3397005982`;
- class-prior macro-F1: `0.1349809886`;
- sentence-ID macro-F1: `0.1349809886`;
- acoustic lift over either baseline: `+0.2047196096`;
- diagnostic slices: `25`, with `0` suppressed;
- eligible slice instability: `true`;
- eligible slice reversal: `true`;
- final-decision eligible: `false`.

AMI v2 remains a separate conversational-mechanics lane:

| Partition | Meetings | Timing present | Timing usable | Dialogue-act files | Dialogue meetings | Fully labelled files |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Full corpus | 170 | 170 | 137 | 556 | 139 | 530 |
| Scenario-only | 138 | 138 | 136 | 552 | 138 | 527 |
| Full-only | 32 | 32 | 1 | 4 | 1 | 3 |

There are `26` dialogue-act files and `28` records without labels. Timing and
dialogue-act contributions remain unavailable under their recorded incomplete
coverage and unlabeled-record reasons.

All five packet lockbox counters are `0`. The packet SHA-256 is
`676D55D95978FBB27DDE50758A98C530979DC730A87C30CD6485178B624B313B`;
its internal review commitment is
`06F02FBF48337D4CB03B7AB5E82E87C9C79C95C232B8A073965CEA0C0C103B84`.
The diagnostic, slice, AMI, and cache-commitment SHA-256 values are,
respectively:

- `CE0D413F258B3F3AF9ECB87C620E52718F95BDF181D7C9E80E41162AA9BB8561`;
- `B557621438D71C05C9153B1379EB4F18167839941D3102822B8496860F127308`;
- `00B8F20CEAAD6B235A5FB415303ADD2FE6FC2A1A7C42FEF562585646FDC728CF`;
- `E0CB15583D43525B84745D3B0B4ABC1B8C4538BA410C7C89AF18C5D19112782F`.

This is acted-perception public-data evidence. The aggregate lift does not
overcome the observed slice instability/reversal or the unavailable AMI
contribution contracts, and it does not estimate customer internal emotion.

## Task 9 Validation Interface

The validator requires exactly one section:

```text
source
contracts
environment
synthetic
candidate --receipt .tmp/emotion-state-002-phase-b-cut4b/publication/receipt.json
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
