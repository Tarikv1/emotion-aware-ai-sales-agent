# EMOTION-STATE-002 Phase B Public-Data Feasibility

## Status

Task 11 final lockbox completed exactly once and independently reviewed;
decision `revise`; canonical publication remains unopened

The single final-lockbox child exited `0` after `346.9s`; no retry occurred.
The state is `lockbox_complete` with `lockbox_open_count=1`, exact state
SHA-256
`69B6475BB32209DD50A6E24866F19D6B44FB51BFA458836BF3B1805140C2BC8C`,
and result SHA-256
`E3EC0EB82E77C1979BF8F921D6EBF6321F510687A608C933473C4DB04AE02F35`.
Two independent aggregate-only reviews returned `C0/I0/M0`.

The retired lineage is not reused or mutated.

Canonical publication, merge, runtime activation, Phase C, providers, private
data, calls, simulations, and source adaptation remain blocked. The old
`.tmp/emotion-state-002-phase-b/venv` and
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
4. **Final-lockbox gate:** Task 11 completed once under its one-use
   authorization and is closed.

The production lockbox completed exactly once and is closed. Do not run
`admit-lockbox` or `lockbox` again for this experiment version. The reviewed
guarded ledger is the canonical UTF-8 LF JSON file
`.tmp/emotion-state-002-phase-b-cut4b/task-11-guarded-ledger.json`, SHA-256
`8515DA4A622A8AF8CE3BE07BE6CAFC8360EDE729F2845317E13C701DBA18299A`.
Its exact ordered command entries retain only `argv`, `exit_code`,
`stdout_sha256`, and `stderr_sha256`. The source-silent admission receipt
SHA-256 is
`0F10FD618FD20819EB7D21981C29E77B6936977D80659A82A5CE1886C1191278`;
it binds implementation HEAD
`c7a5e4037ad8134c96dcd7e8b9577f08fe92391b`, predecessor-state SHA-256
`8BB141DFBF651889F0E1FD66C2DF35FF31F8DC211D98A7CD27512AE7D82ACC20`,
and packet SHA-256
`676D55D95978FBB27DDE50758A98C530979DC730A87C30CD6485178B624B313B`.
The persisted lockbox result retains only the AMI aggregate and authority
SHA-256; AMI meeting, participant, timing-turn, dialogue-turn, dialogue-label,
transcript, probability, feature, and audio rows remain absent.
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

## Task 11 Final Lockbox Result

The final set contains `2,181` cases from `30` actors. The decision contract is
final-decision eligible and returns `revise`.

| Model | Macro-F1 | Balanced accuracy | Brier | ECE | Log loss |
| --- | ---: | ---: | ---: | ---: | ---: |
| Acoustic | 0.3635639146 | 0.3469108660 | 0.4645830705 | 0.0428792113 | 0.9730765286 |
| Class prior | 0.1260336470 | 0.1666666667 | 0.6080410523 | 0.1150032828 | 1.2873759421 |
| Sentence ID | 0.1260336470 | 0.1666666667 | 0.5941195659 | 0.1152010501 | 1.2432829186 |

The acoustic macro-F1 lift over each baseline is `0.2375302676`, with paired
95% interval `[0.2006732151, 0.2644157664]`. Sentence-driven apparent lift is
`false`; eligible slice instability and reversal are both `true`; confidence
abstention improvement is `false`. Those failures prevent `keep` despite the
aggregate lift.

The persisted AMI value has exactly `{aggregate, authority_sha256}`. Its
aggregate SHA-256 is
`31B068BF9AEF99340A6895BCF3997265168591EE31073001382C0BA5ACE89A6C`;
its authority SHA-256 is
`55815CFB3CD49A6164744425F154E35403601BF1A1FF8DEC50AE7207943BCEE7`.
Full/scenario/full-only meeting counts remain `170/138/32`; timing usable counts
remain `137/136/1`; dialogue-act file counts remain `556/552/4`; fully labelled
file counts remain `530/527/3`; and `26` files containing `28` records remain
unlabelled. AMI timing and dialogue contributions remain unavailable.

The exact result, evidence, and mint SHA-256 values are:

- result:
  `E3EC0EB82E77C1979BF8F921D6EBF6321F510687A608C933473C4DB04AE02F35`;
- evidence:
  `93CE60508E565A66BBEDEC48CDD0F0D48CC72D7DA771C419ABD5242570E437E3`;
- mint:
  `0912A83A6DFCE3B90C06E409E50D1DEBFC42619A0594BD714883549839799E0F`.

This is offline acted-perception feasibility evidence. It does not establish
customer internal emotion, any of the five operational signals, real-call
performance, AMI contribution evidence, provider/PSTN/ASR/latency feasibility,
runtime readiness, commercial effectiveness, or production readiness.

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
