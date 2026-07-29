# EMOTION-STATE-005 Phase C1.1 Source Resolution

## Status

Public-source review complete. Decision: `maintain_defer_c2`.
Confusion and frustration remain `defer`; neither signal is eligible for C2.
This is a noncanonical research packet, not a candidate or acceptance
transaction.

## Question

Can authoritative public documentation resolve at least one direct confusion
or frustration corpus as admissible under the frozen Phase C1 rules?

## Why This Follow-Up Was Needed

The accepted Phase C1 checkpoint recorded 88 ordered discovery requests and
1,025 returned discovery records, but it retained zero candidates because 971
records had unresolved authoritative provenance and 54 were duplicates.
Forty-seven requests were incomplete. That result established a source
resolution failure; it did not establish that no relevant corpus exists.

Phase C1.1 therefore reviewed at most four named candidates per signal from
original papers and official landing pages. It did not repeat broad discovery
and did not read any dataset or annotation row.

## Frozen Review Contract

- Protocol:
  `research/experiments/configs/emotion-state-005-phase-c1-1-source-resolution-protocol.json`
- Protocol SHA-256:
  `DA789714B4835FD160BDB89FBB4F1E60125B5EFF28CC910F690CD4378B5B321B`
- Parent Phase C1 protocol SHA-256:
  `2540A1BA430F78B9F660BA466F6CFD7099CFFCAA6F1C1D1AC373F4BA1D4D2CCD`
- Candidate cap: exactly four ordered candidates for confusion and four for
  frustration, with one shared source and seven unique candidates.
- Timing limitation: candidate discovery and preliminary triage preceded the
  written C1.1 freeze. Final field extraction and adjudication followed it.
  This is a bounded source-resolution review, not a confirmatory experiment.

A source can pass only if authoritative documentation establishes spontaneous
conversation, the direct target construct, independent human-observer labels,
a turn or bounded-segment unit, at least 93 published usable direct-positive
segments, and qualifying pre-adjudication Krippendorff alpha with the frozen
point and confidence-interval thresholds. Missing evidence remains unresolved;
it is not inferred.

## Source Register

The aggregate-only source register is:

`research/sources/emotion_state/phase_c1_1_source_resolution.json`

It is 16,391 bytes with SHA-256
`9E6260FF367986D3F64930190BE18B373A8BB5426763FE31E6625EDEDC8B8B8F`.
It contains public source identities, published aggregate facts, gate fields,
and adjudications only. It contains no corpus rows, transcripts, audio,
participant identifiers, predictions, features, or probabilities.

## Confusion Adjudication

| Candidate | Documented evidence | C1.1 outcome |
| --- | --- | --- |
| [Yu et al. classroom corpus](https://library.apsce.net/index.php/ICCE/article/view/2655) | Real junior-high mathematics discussions; 759 sentence units; direct confusion label; two teacher annotators and a third adjudicator; 134 post-adjudication confusion sentences; 84.33% raw agreement. No Krippendorff alpha or interval is published, and no official corpus release or dataset license is documented. | `unresolved`. This is the closest candidate, but it cannot pass on percent agreement or adjudicated final labels alone. |
| [DAiSEE](https://arxiv.org/abs/1609.01885) | 9,068 ten-second video snippets from students watching educational or recreational videos; direct confusion intensity labels from crowd raters with expert-consensus filtering. It is not conversation. Reliability uses a weighted Cohen-kappa filter rather than qualifying Krippendorff alpha. | `rejected`. The non-conversational domain is decisive. |
| [HRI-confusion](https://doi.org/10.1016/j.dib.2025.112047) | Controlled Wizard-of-Oz Pepper tasks use designed confusion and non-confusion conditions plus participant ratings after each dialogue. The 789 face/body clips are views of experimental conversations, not 789 independently observed direct-positive units. Raw media access requires an application. | `rejected`. Condition/self-report labels, whole-conversation units, missing approved reliability, and restricted access fail the gate. |
| [Li, Kelleher, and Ross pilot](https://www.semdial.org/anthology/papers/Z/Z21/Z21-3013/) | Semi-spontaneous human-avatar dialogue with designed confusion stimuli; 19 usable participants. Evidence uses task condition, post-interaction self-report, and pretrained automated indicators. The paper does not establish stable local dialogue boundaries or direct independent observer labels. | `rejected`. The label path, temporal unit, positive support, and reliability requirements are not met. |

Confusion decision: `defer`. There are zero passes, one unresolved candidate,
and three hard rejects.

## Frustration Adjudication

| Candidate | Documented evidence | C1.1 outcome |
| --- | --- | --- |
| [Yu et al. classroom corpus](https://library.apsce.net/index.php/ICCE/article/download/2655/2531/3619) | The same sentence-level classroom corpus publishes 99 post-adjudication frustration sentences, clearing the numerical support floor. Raw frustration agreement is only 59.60%; no Krippendorff alpha or interval and no official material license are documented. | `unresolved`. The count alone cannot establish reliability or lawful material availability. |
| [FUSE](https://aclanthology.org/2024.lrec-main.666/) | Unscripted dyadic task dialogue; the game frustration label covers the final 90-second response interval. Labels are immediate post-task self-report plus one partner perception. The exact positive segment count and approved reliability evidence are unpublished. The [official page](https://fusecorpus.github.io/FUSE/) states CC BY-NC 4.0. | `rejected`. Self-report and a single partner perception are prohibited label paths. |
| [MULTICOLLAB](https://aclanthology.org/2024.lrec-main.1023/) | Natural Zoom task dialogue with experimentally induced frustration. Participants replayed the recording and timestamped their own frustration; modeling uses 4.5-second windows. The paper reports 297 four-level and 176 binary total instances, not the eligible positive count, and no inter-rater reliability. The [official repository](https://github.com/mp6510/MULTICOLLAB) states CC BY-NC 4.0. | `rejected`. Direct but self-report-only labels fail the observer gate. |
| [IEMOCAP](https://sail.usc.edu/iemocap/Busso_2008_iemocap.pdf) | Direct turn-level frustration labels from three external raters. USC identifies the corpus as acted: professional actors performed scripts and improvised hypothetical target-emotion scenarios. The paper reports Fleiss kappa, not Krippendorff alpha; the spontaneous original-label values are .34 for all turns and .43 for agreed turns. [Official access](https://sail.usc.edu/iemocap/iemocap_release.htm) requires a release form. | `rejected`. The acted/elicited guard is decisive. |

Frustration decision: `defer`. There are zero passes, one unresolved candidate,
and three hard rejects.

## Construct Caution

[Baker et al.](https://doi.org/10.1111/cogs.70035) argue that confusion and
frustration have multiple forms and substantial overlap. That does not justify
collapsing the two labels. It strengthens the project rule that a direct named
label, local conversational context, independent observation, and preserved
uncertainty are required before either construct can influence later
evaluation.

## Decision And Recommendation

The source-first review resolves the earlier discovery ambiguity but does not
open C2:

- confusion: `defer`;
- frustration: `defer`;
- new C2-eligible signals: none;
- overall: `maintain_defer_c2`.

Only the Yu et al. classroom corpus is worth a later targeted provenance
decision. Evidence that could change the result is an official release with
clear use terms, preserved independent per-rater labels, confirmed
conversational provenance, and a qualifying pre-adjudication Krippendorff-alpha
point and interval. Requesting material or contacting owners is outside this
checkpoint.

If that narrow provenance path is not separately authorized or cannot supply
the missing evidence, the maintainable alternative is to retire the
public-dataset model route for these two signals and later design only
observable dialogue-state rules, such as explicit clarification and repair
behavior, without hidden-emotion claims. That alternative is not implemented
here.

## Technical Findings

1. The parent Phase C1 reason catalog has no exact code for a source that is
   authoritatively documented as non-conversational. This packet records the
   failed gate directly and does not invent a machine-card reason.
2. A fresh Windows checkout with global `core.autocrlf=true` changes
   raw-byte-bound committed LF files to CRLF worktree bytes because exact
   `.gitattributes` rules are absent. The Phase C1 checkpoint fails
   `validator_worktree_binding`. `check_project_drift.py` and `check_setup.py`
   also abort before their checks because the Phase A guard-policy bytes differ
   from the frozen policy. No validator, guard, test, or `.gitattributes`
   correction was made under this research-only authority, and none of those
   three blocked paths is claimed as passing.

## Boundary

This checkpoint used public official pages, original papers, institutional
records, and DOI metadata only. It performed no dataset download, login, form
submission, raw data or annotation read, private-data access, provider access,
call, simulation, model evaluation, source adaptation, runtime change,
candidate/canonical staging, C2 work, push, merge, or history rewrite.

It does not infer any customer's emotion and does not establish model quality,
real-call performance, PSTN/ASR/latency behavior, safety, conversion,
production readiness, or commercial effectiveness.
