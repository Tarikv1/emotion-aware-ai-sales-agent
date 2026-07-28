# EMOTION-STATE-004 Phase C1 Operational-Signal Evidence Admission

## Status

Protocol frozen; source discovery not run.

## Question

Does direct, temporally local, independently rated observer-label evidence
exist for hesitation, frustration, confusion, interest, or disengagement in
spontaneous conversation?

## Claim Boundary

This checkpoint assesses rowless source and label admissibility only. It does
not assess customer internal emotion, model quality, sales performance,
provider behavior, real calls, runtime behavior, or production readiness.

## Frozen Protocol

- Protocol ID: `emotion-state-phase-c1-discovery-v1`.
- Protocol authority:
  `research/experiments/configs/emotion-state-004-phase-c1-discovery-protocol.json`.
- Direct-label grid: five signals by four query templates by four discovery
  channels, for exactly `80` seed queries.
- Fallback-material grid: two signal-agnostic templates by four discovery
  channels, for exactly `8` additional queries.
- Expected total: exactly `88` query records.
- Each seed query returns at most `25` records.
- Detailed screening is capped at `20` deduplicated candidates per signal and
  `10` fallback-material candidates.
- Citation depth is one hop, capped at five backward and five forward
  candidates per signal.

The four planned discovery services remain discovery aids only. Their results
cannot establish source identity, license, access, annotation semantics,
construct validity, or signal admission.

## Evidence Admission Rule

A signal can pass only when authoritative source documentation establishes all
of the following:

- spontaneous conversation rather than acted or scripted speech;
- the direct target construct rather than a proxy or post-hoc synonym;
- independent human-observer labels;
- turn or bounded-segment temporal granularity;
- verifiable pre-adjudication reliability under the frozen
  `krippendorff_alpha` rule; and
- at least `93` published usable direct-positive labelled segments, with rated
  units not fewer than published positives.

Acted or scripted speech, proxy constructs, whole-conversation labels,
single-rater labels, adjudicated-only labels, self-report, LLM labels, and a
planned-but-unexecuted annotation study cannot produce `pass`. Explicit
refusal, stop, and do-not-call intent remain protected text intents and are not
relabelled as disengagement.

## Transport And Privacy Boundary

Only rowless transport metadata is contractually representable. Receipts may
contain bounded public HTTPS URLs, timestamps, statuses, hashes, byte counts,
base content types, and closed reason codes. They may not contain response
bodies, headers, cookies, credentials, local paths, tool instructions, corpus
rows, audio, transcripts, participant or customer identifiers, annotations,
features, predictions, probabilities, or model metrics.

Purpose-specific response caps are `2,000,000` bytes for seed queries,
`2,000,000` bytes for citation discovery, and `20,000,000` bytes for an
authoritative document. The total unique ignored source cache is capped at
`512,000,000` bytes. These limits are frozen contract values; no retrieval
occurred in this task.

## Annotation Fallback

The fallback protocol is preregistration material only. Execution is not
authorized and requires a separate checkpoint. It requires at least three
independent raters per segment, independent
`present|absent|uncertain_or_unratable` labels, preserved raw disagreement,
bounded context frozen before annotation, pilot-only codebook revision,
training/pilot exclusion from later evaluation, and annotator blinding to
model outputs, sales decisions, and other raters. LLM labels and majority vote
as ground truth are forbidden.

## Stop Rule

Discovery remains incomplete unless all `80` direct-label and `8`
fallback-material query records exist and all bounded citation attempts are
represented. An incomplete query, truncated result, candidate overflow,
incomplete citation budget, unresolved candidate, feasible fallback, or
unresolved fallback prevents a signal-level `fail` and forces at least
`defer`.

## Decision Rule

Signal decisions are independently ordered as `pass|defer|fail`. Overall
decisions are derived only from those signal decisions:

- all five pass: `proceed_full_to_c2`;
- at least one but fewer than five pass: `proceed_partial_to_c2`;
- no pass and at least one defer: `defer_c2`;
- otherwise: `stop_c2`.

Only a later accepted signal-level `pass` may enter a C2 eligibility list.
This protocol freeze does not produce any signal decision.

## Rowless Aggregate V2

The offline Task 5 working draft emits only
`EmotionStatePhaseC1AggregateResultV2`. V1 payloads reject. In addition to the
global counts, V2 carries exact per-signal/fallback search-lane witnesses,
sorted sparse categorical source-signature multiplicities with exact document
counts, exact per-signal fallback-material status counts, and per-card
categorical eligibility/reliability witnesses. Search-lane discovery cannot
exceed 25 records per complete query; an overflow flag requires the exact
direct/fallback order cap of 20/10. The validator rederives search completeness,
signal fail readiness, candidate outcomes, ordered reason codes, fallback
status, signal decisions, exact global document count, and overall decision
from those local facts. The four aggregate search-meta reason-code counts remain
exactly zero; residual rejection and unresolved reason counts must reconcile to
exact card, discovery, citation, and fallback witnesses.

Validation and report rendering require the exact canonical protocol,
search-ledger, source-ledger, and review-receipt bytes as caller-supplied
in-memory arguments. They bind all four hashes, fully validate their contracts
and cross-links, require an admitted review, and recompute a nonrecursive exact
aggregate projection from those inputs and the payload's implementation
identities. Public acceptance requires that projection to equal the submitted
aggregate field for field in addition to the independent local V2 algebra
checks. Full evidence-card rehashing and exact per-signal card order remain
separate checks. No path is read. This prevents coherent rewrites of card
semantics, source/license facts, search completeness, fallback feasibility,
review verdicts, or linked input identities.

The canonical JSON result is capped at `524288` bytes. The frozen maximum
100-card test shape measures `155411` canonical bytes. The payload remains
rowless, but sparse source signatures and per-card categorical diagnostics may
fingerprint public source configurations. It therefore contains no source ID,
title, URL, path, participant, segment, transcript, audio, prediction,
probability, feature, or model metric, and it grants no private-data or runtime
authority.

## Work Not Performed

No network access, public research, source retrieval, dataset or private-data
read, annotation, audio or transcript read, model training or evaluation,
external source adaptation, provider access, call, simulation, prompt or
knowledge-base change, runtime activation, candidate generation, canonical
generation, C2 work, push, merge, or history rewrite occurred in this task.
