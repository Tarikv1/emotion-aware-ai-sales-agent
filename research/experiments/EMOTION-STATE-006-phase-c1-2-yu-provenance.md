# EMOTION-STATE-006 Phase C1.2 Yu Provenance Decision

## Status

Official/public provenance review complete. Decision:
`maintain_defer_c2`.

No official public material path was found in the bounded review. Confusion and
frustration remain `defer`; neither signal is eligible for C2. This is a
noncanonical research packet, not a dataset, model, candidate, or acceptance
transaction.

## Question

Can official public primary sources resolve all remaining admission evidence
for the Yu et al. student-teacher junior-high mathematics corpus?

## Frozen Review Contract

- Protocol:
  `research/experiments/configs/emotion-state-006-phase-c1-2-yu-provenance-protocol.json`
- Protocol size: 3,492 bytes.
- Protocol SHA-256:
  `D12C1D4E71AD3BB7BFDF1E70F2623608F7EB7B76B9489BF52398236C52901051`
- Target: only the Yu et al. corpus retained as unresolved by Phase C1.1.
- Required findings: official material release, explicit dataset-use terms,
  preserved independent per-rater annotations, qualifying pre-adjudication
  Krippendorff alpha with a point estimate and 95% confidence interval, and
  original spontaneous conversational provenance.
- Reliability thresholds: alpha point at least 0.80 and 95% interval lower
  bound at least 0.67. Both values must be published and pre-adjudication.
- Missing evidence remains unresolved and cannot be inferred.

The protocol was frozen before the new public web search. This is a bounded
official-source provenance review, not a confirmatory experiment.

## Method

The review followed four routes in order:

1. official APSCE article, paper, and proceedings records;
2. official Yuan Ze University author and laboratory pages;
3. exact-title and author metadata searches on public data repositories; and
4. Crossref DOI metadata and linked relations.

Only official public documents, institutional pages, public repository
metadata, and publisher/DOI metadata were used as authoritative evidence.
Domain-restricted public-web results were inspected for discovery only; their
snippets and irrelevant hits were not used as evidence. The source register
records each repository query, check date, outcome, and empty relevant
material-record ID set. Those searches are corroborative discovery trace only;
the admission decision does not treat search-engine absence as proof.

## Source Register

The aggregate-only source register is:

`research/sources/emotion_state/phase_c1_2_yu_provenance.json`

It is 12,784 bytes with SHA-256
`6A4465C7EDA050BA28AE8CA982371E0DCD07DF7FCD753E9C52465D54CAB81198`.
It records official source identities, published aggregate facts, bounded
negative-search outcomes, gate adjudications, and boundary attestations only.
It contains no corpus row, annotation, transcript, audio, participant
identifier, prediction, feature, or probability.

## Findings

| Required field | Official/public evidence | Outcome |
| --- | --- | --- |
| Official corpus or material release | Both APSCE article pages expose the paper and state that data are not yet available. The reviewed official author and laboratory pages expose no linked Yu corpus material. The source register separately records the exact corroborative repository-discovery queries; they returned no relevant material record. | `not_found_in_reviewed_official_public_sources` |
| Explicit dataset-use or license terms | No dataset license or use terms appear on the reviewed APSCE or institutional pages. The 2012 Crossref record has no license object or related dataset/supplement relation. | `not_found_in_reviewed_official_public_sources` |
| Preserved independent per-rater annotations | The papers describe two teacher annotators plus a third adjudicator and publish aggregate agreement, but expose no independent per-rater annotation material. | `not_found_in_reviewed_official_public_sources` |
| Qualifying pre-adjudication reliability | The original paper reports only A1-A2 raw agreement: 84.33% for confusion and 59.60% for frustration. It publishes neither a Krippendorff-alpha point estimate nor a confidence interval. | `not_published_in_reviewed_official_public_sources` |
| Original spontaneous conversational provenance | The 759 text sentences are documented as coming from student-teacher classroom mathematics discussions. The paper does not call the interaction spontaneous. The 2012 speech follow-up says 379 selected sentences were recorded later in an office. | `partially_supported_but_exact_required_provenance_unresolved` |

The negative findings are bounded: no path was found in the reviewed official
public sources. They do not prove that private or unpublished materials do not
exist.

## Published Aggregate Facts Preserved

- 759 sentence units;
- 134 final confusion labels;
- 99 final frustration labels;
- 84.33% raw A1-A2 confusion agreement;
- 59.60% raw A1-A2 frustration agreement; and
- two teacher annotators plus a third teacher adjudicator.

These facts do not substitute for released per-rater labels, lawful material
availability, or the frozen reliability statistic and interval.

## Provenance Correction

Phase C1.1 treated the corpus as conversational based on the classroom-dialogue
description. C1.2 narrows that claim:

- classroom text-dialogue origin is supported;
- the exact spontaneous-interaction requirement is not explicitly documented;
  and
- the speech follow-up does not establish original classroom audio because its
  selected sentences were recorded later in an office.

The source therefore remains unresolved under the exact provenance gate. This
is not evidence that the classroom discussions were scripted; it is evidence
that the reviewed official sources do not publish the required spontaneous
designation.

## Decision And Recommendation

- confusion: `defer`;
- frustration: `defer`;
- new C2-eligible signals: none;
- overall: `maintain_defer_c2`.

The narrow official/public investigation identified no admissible material
path. The recommended next product decision is to retire the public-dataset
model route for confusion and frustration. If separately authorized later,
the maintainable alternative is to design only observable clarification or
repair rules, without hidden-emotion claims. That alternative is not designed
or implemented here, and this checkpoint cannot open C2.

Evidence that would change this decision is an official release with explicit
use terms, preserved independent pre-adjudication annotations, a qualifying
Krippendorff-alpha point and 95% interval, and official documentation resolving
the exact spontaneous conversational provenance requirement.

## Independent Review

Read-only packet review first returned `C0/I1/M0` because the public-repository
search was not reproducible. After the exact corroborative search ledger was
added, delta review returned `C0/I0/M1` because discovery inspection and
authoritative evidence were not distinguished precisely. After that boundary
wording was corrected, final review of the six-file packet returned
`C0/I0/M0` and `READY`.

## Boundary

No dataset or annotation was downloaded or read. No login, form, owner contact,
message, private-data access, provider access, call, simulation, model
evaluation, source adaptation, runtime action, candidate/canonical staging, C2
work, merge, history rewrite, or push occurred.

This checkpoint does not infer any customer's emotion and does not establish
model quality, real-call performance, safety, conversion, production readiness,
or commercial effectiveness.
