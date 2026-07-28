# EMOTION-STATE-004 Phase C1 Operational-Signal Evidence Admission Design

## Status

Approved design specification dated 2026-07-26.

This document authorizes design documentation only. It does not authorize
source discovery, public-material access, annotation, implementation, model
training or evaluation, provider access, calls, simulations, product-runtime
changes, or runtime activation.

The design is stacked from reviewed Phase C0 HEAD
`48499cf1690338210c57bd720ef466a5f7abf0c7` on branch
`codex/emotion-state-phase-c1-evidence-admission-design`.

## Goal

Phase C1 determines whether defensible reference-label evidence exists for
each of five observer-perceived conversational signals:

1. hesitation;
2. frustration;
3. confusion;
4. interest; and
5. disengagement.

The real product question is not whether a generic emotion classifier can
produce a label. It is whether any target signal has sufficiently direct,
temporally local, reliable, and auditable observer annotations to justify a
later offline model-evaluation checkpoint.

Each signal is judged independently. Phase C1 may admit a strict subset. A
missing or weak signal remains unavailable; it cannot inherit evidence from
another signal.

## Evidence Boundary

Phase C1 is a source-and-label admissibility checkpoint, not a model
checkpoint.

It may later, under separate execution authority:

- research public source metadata and documentation;
- bind qualifying annotation definitions and provenance;
- identify source gaps;
- record rowless evidence cards and source receipts; and
- preregister a multi-rater human-annotation fallback using suitably licensed
  public spontaneous conversations.

It may not:

- treat acted or scripted speech as passing evidence;
- map emotion, sentiment, dialogue-act, or engagement proxies to the target
  labels;
- use LLM-generated labels as reference truth;
- read audio, transcripts, participant rows, or annotation rows;
- train, tune, or evaluate a model;
- reopen or reuse the Phase B final lockbox;
- modify prompts, knowledge bases, the temporal tracker, policy behavior,
  provider settings, or product runtime;
- access private data or providers;
- place calls or run conversational simulations; or
- make claims about hidden customer emotion, conversion, safety,
  production readiness, or commercial effectiveness.

A proposed annotation study does not itself earn `pass`. Until qualifying
annotations exist and pass their own reviewed gate, the affected signal
remains deferred.

## Lineage Reconciliation

The original
`docs/superpowers/specs/2026-07-14-emotion-state-layer-design.md` used
"Phase D" for a public-data thesis experiment. The executed checkpoint
lineage no longer matches that provisional name:

- Phase A completed bounded provenance, manifests, contracts, verification,
  and cohort-release work.
- Phase B (`EMOTION-STATE-002`) implemented the public acted-perception
  feasibility experiment, actor-disjoint evaluation, one-use lockbox, and
  decision evidence. Its accepted decision is `revise` because eligible slice
  instability and reversal remained true and confidence abstention did not
  improve the result.
- Phase C0 (`EMOTION-STATE-003`) proved deterministic temporal mechanics under
  frozen symbolic fixtures. Its `keep` decision applies only to those
  mechanics.

Most of the original Phase D experiment mechanics were therefore absorbed by
Phase B. Repeating a generic "Phase D public-data experiment" would duplicate
closed work while leaving the actual label-validity gap unresolved.

This successor is named `EMOTION-STATE-004 Phase C1` because it closes the
evidence-admission gap identified by Phase C0 before any acoustic evidence or
policy adapter can be admitted. The historical design remains historical; this
document records the corrected successor lineage without rewriting the closed
Phase B or Phase C0 checkpoints.

## Product Review

### Real Goal

Establish whether a future emotion-aware sales-agent research lane can use
construct-valid observer labels for the specific conversational states that
the product proposes to track.

### Assumption Most Likely To Be False

Public "emotion" or dialogue corpora may appear relevant while providing no
direct, temporally local labels for the five operational signals. Treating
anger as frustration, uncertainty as confusion, or engagement as interest
would recreate the unsupported proxy assumption that Phase C1 exists to test.

### What Will Break First

Direct signal labels may be absent, poorly documented, non-spontaneous,
conversation-level only, single-rated, or too unreliable to support later
evaluation. Phase C1 must allow `defer_c2` or `stop_c2` rather than weaken its
rules to manufacture a positive outcome.

### Simpler Alternative

A fixture-only guarded policy adapter could be designed next. That work is
smaller and useful, but it does not test whether the proposed sensing inputs
mean what the project claims. Evidence admission is the stronger next
checkpoint for the real product and thesis goal.

### Recommendation

Use a bounded corpus-first source screen. If no existing source qualifies,
record a preregistered independent-human annotation route as a deferred
fallback. Keep source validity, annotation execution, model evaluation, policy
adaptation, and runtime work as separate gates.

## Approaches Considered

### Corpus-First Screening With Annotation Fallback

Screen existing public sources against frozen rules, signal by signal. Where
coverage is missing, preregister a separate human-annotation checkpoint.

Benefits:

- tests existing evidence before incurring annotation cost;
- retains a credible route to later evaluation;
- keeps a missing source from becoming a fabricated proxy mapping; and
- supports partial admission without claiming a global emotion layer.

This is the selected approach.

### Annotation-First

Select a public spontaneous-conversation corpus and immediately design a new
annotation study. This may be faster when existing annotations are unlikely to
qualify, but it risks annotation cost before source suitability, licensing,
construct definitions, and evidence rules are fully established.

### Existing-Evidence Only

Create a source matrix and stop wherever direct evidence is absent. This is
the smallest research effort, but it is likely to end with deferred signals
and no reviewed route toward a later evaluation.

## Signal Construct Contract

Every label refers to an observer-perceived conversational state. It is not a
claim about the speaker's hidden internal emotion.

### Hesitation

Perceived reluctance or uncertainty in response delivery.

It is not automatically established by:

- a pause;
- latency;
- a disfluency;
- a short answer; or
- a turn-taking gap.

### Frustration

Perceived conversational strain or irritation associated with the
interaction or task.

It is not automatically established by:

- generic negative affect;
- anger;
- loudness;
- urgency; or
- disagreement.

### Confusion

Perceived difficulty understanding the content or process.

It is not automatically established by:

- disagreement;
- missing information;
- a question;
- uncertainty; or
- an ASR or connection failure.

### Interest

Perceived attention and willingness to continue exploring.

It is not automatically established by:

- politeness;
- compliance;
- positive affect;
- purchase intent; or
- a long response.

### Disengagement

Perceived withdrawal or reduced participation.

It is not automatically established by:

- concise speech;
- ordinary silence;
- low energy;
- a connection problem; or
- an explicit refusal.

Explicit refusal, stop requests, and do-not-call intent are separate protected
text intents. They can never be replaced by or inferred from disengagement.

## Label Form

The fallback annotation design treats the five signals as independent
multilabel decisions:

- `present`;
- `absent`; or
- `uncertain_or_unratable`.

Signals may co-occur. An annotator is never forced to choose a single emotion
class.

Existing sources retain their native direct labels during Phase C1. Phase C1
does not collapse, threshold, or convert those labels for model use. Any C2
mapping must be separately preregistered before label outcomes or model
results are inspected.

## Candidate And Signal Decisions

### Candidate-Source Status

Each candidate source receives exactly one status:

- `admissible`: every mandatory evidence rule passes;
- `rejected`: at least one mandatory rule is violated, with explicit reason
  codes; or
- `unresolved`: required documentation or metadata cannot be verified.

### Per-Signal Decision

Each operational signal receives exactly one decision:

- `pass`: at least one admissible existing source directly supports the
  signal;
- `defer`: a credible path exists, but direct evidence is absent, unresolved,
  insufficient, or requires the planned human-annotation study; or
- `fail`: the complete bounded search and annotation-feasibility review find
  no ethical, licensed, construct-valid path.

Rejecting one source does not fail a signal. Exhausting one dataset, one query,
or one search service does not fail a signal.

There is no global "emotion layer passed" decision.

## Mandatory Source-Admissibility Rules

A source can support `pass` for a signal only when all of the following are
verified:

1. exact source identity, version, and auditable provenance;
2. compatible public access and usage rights;
3. ethically and legally usable spontaneous conversational material;
4. direct annotation of the operational signal rather than a proxy construct;
5. turn-level or bounded time-segment-level annotation;
6. independent human-observer methodology;
7. signal-specific reliability evidence;
8. sufficient documentation or rater evidence to verify that reliability;
9. sufficient usable positive examples under the preregistered precision rule;
10. recorded language, population, domain, modality, context, and exclusions.

Acted or scripted speech may be retained only as development or
negative-control evidence. It cannot produce `pass`.

Whole-conversation labels may be recorded as context but cannot establish when
a target state occurred and therefore cannot produce `pass`.

Public availability alone is insufficient. Unclear consent, incompatible
licensing, unstable identity, or an inaccessible authoritative description
leaves the source unresolved or rejected.

## Rowless Evidence Card

Every candidate source receives a rowless evidence card containing only:

- source identifier and title;
- authoritative origin;
- version, revision, and retrieval date;
- source-document and receipt hashes;
- license and access classification;
- conversational domain, language, population, and spontaneity;
- exact native annotation definition;
- temporal unit and context window;
- annotation modality;
- number and independence of raters as documented;
- reported agreement method and evidence;
- direct per-signal correspondence;
- inclusion, exclusion, unresolved, and rejection reason codes;
- limitations and nonclaims.

The card contains no audio, transcript, participant identity, annotation row,
example utterance, prediction, feature, probability, or model metric.

## Bounded Source Discovery

Before public research begins, the implementation checkpoint must freeze and
hash:

- exact search locations;
- exact query strings;
- per-signal query budgets;
- inclusion and exclusion rules;
- deduplication logic;
- citation-following depth;
- source-receipt format;
- stop conditions; and
- decision precedence.

Authoritative evidence may come from:

- peer-reviewed papers;
- official corpus pages;
- official repositories; and
- authoritative license or data-use documents.

Third-party mirrors may support discovery but cannot establish provenance,
version, permission, or admissibility.

Candidates are screened fail-fast in this order:

1. identity and provenance;
2. license and access;
3. spontaneous conversational setting;
4. direct signal annotation;
5. temporal locality;
6. independent human observers;
7. verifiable reliability.

The search uses a frozen finite budget and at most one backward and one forward
citation hop for an otherwise eligible candidate. Every query, candidate,
deduplication, rejection, unresolved fact, authoritative URL, retrieval date,
revision, and document hash is recorded in a reproducible ledger.

The source-discovery phase is documentation- and metadata-only. It does not
read corpus audio, transcripts, participant rows, annotation rows, or dataset
archives.

## Human-Annotation Fallback

If a signal remains deferred after source discovery, Phase C1 may preregister,
but does not execute, a separate annotation checkpoint.

That future checkpoint must require:

- appropriately licensed public spontaneous conversations;
- at least three independent human observers per segment;
- a bounded context window frozen before annotation;
- independent multilabel decisions for all five signals;
- annotators blinded to model outputs, sales decisions, and other raters;
- a separate training and pilot set excluded from later evaluation;
- codebook revisions only during the pilot, followed by a frozen main-study
  codebook;
- preserved raw disagreement and `uncertain_or_unratable` decisions;
- no majority-vote result that hides disagreement;
- retained conversation- and speaker-level grouping solely for later disjoint
  splitting;
- no LLM-generated labels;
- no private conversations or customer calls; and
- no inference of protected characteristics.

The main-study sample size must be derived from a preregistered
reliability-precision target and pilot prevalence. A raw number of customers
who appear to show the same behavior is not evidence of a stable pattern.

Executing the annotation study requires a new, independently reviewed
checkpoint. A feasible plan leaves the signal at `defer`; it does not produce
`pass`.

## Reliability Gate

Agreement is assessed before adjudication so consensus cannot conceal
ambiguity.

An existing source can support `pass` only when it provides:

- at least two independent human ratings on the same units;
- signal-specific, chance-corrected reliability evidence;
- enough published aggregate documentation to verify the calculation;
- uncertainty bounds; and
- sufficient usable positive examples under the frozen precision rule.

Phase C1 may record that raw rater assignments are available, but it cannot
read them under its metadata-only boundary. If aggregate documentation is
insufficient and verification would require annotation-row access, the source
remains unresolved pending a separately authorized checkpoint.

For the future fallback study, the primary reliability statistic is
Krippendorff's alpha with bootstrap uncertainty. The following ordered rule
produces exactly one status:

1. `defer` when reliability is unverifiable or the effective sample is
   insufficient;
2. otherwise `pass` when the point estimate is at least `0.80` and the lower
   95% bound is at least `0.67`;
3. otherwise candidate source `rejected` when the upper 95% bound is below
   `0.67`; and
4. otherwise `defer`.

The same alpha thresholds apply to an existing source. An existing alpha result
without a verifiable uncertainty bound cannot produce `pass`.

The checkpoint always reports:

- `uncertain_or_unratable` frequency;
- class prevalence;
- positive agreement;
- negative agreement; and
- pre-adjudication disagreement.

Those values cannot be discarded merely to improve alpha.

The frozen discovery protocol must contain an adequacy rule for every
reliability statistic that an existing source is allowed to use. The rule,
including threshold and uncertainty requirement, must be independently
reviewed before candidate reliability outcomes are extracted. A statistic
without a preapproved rule leaves the source unresolved.

If an existing source uses a statistic other than alpha, Phase C1 cannot
pretend it is numerically interchangeable with alpha. Adding a metric-specific
rule requires a new reviewed protocol version and hash before that candidate's
reliability value is used in an admissibility decision. A threshold cannot be
selected after seeing the candidate value.

Passing the reliability gate establishes only a usable observer-perception
label. It does not establish objective customer emotion, model quality,
runtime readiness, or commercial value.

## Planned Component Placement

The implementation plan may propose project-local research files such as:

- `research/experiments/EMOTION-STATE-004-phase-c1-operational-signal-evidence-admission.md`;
- a frozen discovery configuration under `research/experiments/configs/`;
- rowless evidence-card and decision contracts under `scripts/`;
- a deterministic research runner under `scripts/`;
- an independently implemented validator under `scripts/`;
- focused tests under `scripts/`;
- methodology and roadmap trace updates; and
- a canonical result/report pair under
  `research/experiments/generated/EMOTION-STATE-004-phase-c1-operational-signal-evidence-admission/`.

No Phase C1 implementation belongs under `runtime/`. The reusable sales-agent
core, provider configuration, and accepted Phase C0 artifacts remain
unchanged.

Exact filenames, schemas, and task order are implementation-plan decisions,
not authority granted by this design.

## Transaction Workflow

Phase C1 uses a preregistered, review-gated transaction:

1. freeze and hash the search protocol, construct definitions, evidence rules,
   and stop conditions;
2. independently review the preregistration before candidate outcomes are
   inspected;
3. conduct only the separately authorized public documentation and metadata
   search;
4. record authoritative-source receipts and hashes in an input ledger;
5. build a deterministic, rowless candidate result and report;
6. independently verify every proposed `pass`, every source rejection, search
   completeness, and every signal decision; and
7. publish the canonical result/report only through a caller-locked prepare,
   validate, and accept transaction.

Official documentation may be cached only in a fixed ignored research area
when later authorized. Tracked records contain provenance, hashes,
classifications, aggregate counts, and decisions, not copied papers, search
result dumps, conversations, or participant-level material.

There is no performance lockbox in Phase C1 because no model is evaluated.
The preregistration hash and finite search ledger prevent post-hoc changes to
the evidence rules.

Candidate creation, canonical acceptance, commit, and push remain separate
gates. Passing one does not authorize the next.

## Canonical Aggregate

The canonical rowless result must bind:

- exact `EmotionStatePhaseC1AggregateResultV2` schema and checkpoint identity;
- exact implementation Git HEAD;
- frozen configuration hash;
- source-receipt hashes;
- search-ledger hash;
- validator identity;
- ordered target-signal list;
- aggregate candidate counts by status and reason code;
- exact per-signal and fallback search-lane counts sufficient to rederive
  completeness, per-complete-query discovery capacity, exact-cap overflow,
  retained supply, citation order, and signal fail readiness;
- sorted sparse source-signature multiplicities sufficient to reconcile source,
  exact document, role, membership, candidate-union, and card-source counts
  without publishing source identities;
- per-signal decisions and evidence-card hashes;
- per-card categorical eligibility and reliability witnesses sufficient for a
  validator-local status and ordered-reason derivation;
- exact per-signal fallback-material status counts and locally derived
  fallback-feasibility classification;
- exact C2-eligible signal list;
- overall C1 decision;
- privacy and boundary booleans;
- limitations and nonclaims;
- canonical result and report identities.

The V2 aggregate rejects V1 payloads. Aggregate search-meta reason codes remain
zero because query completeness, truncation, overflow, and citation stops are
represented and validated in `search_lane_counts`; rejection and unresolved
reason totals must instead reconcile exactly to card, discovery, citation, and
fallback witnesses. The final canonical JSON result is capped at `524288`
bytes in both builder and validator. The frozen maximum 100-card test shape is
`155411` canonical bytes.

Aggregate validation and report rendering are pure in-memory operations but
require the caller to supply the exact canonical protocol, search-ledger,
source-ledger, and review-receipt bytes. They verify all four result-bound
SHA-256 values; fully validate every envelope and cross-link; require an
admitted review; and use a nonrecursive deterministic projection helper to
recompute the exact aggregate from those bytes plus the payload's implementation
identities. Public acceptance requires field-for-field canonical equality with
that projection in addition to the independent local V2 algebra checks.
Source-card validation still parses every evidence card, recomputes its
canonical full-card SHA-256, and requires each signal's diagnostic hash
sequence to equal the source-ledger card sequence for that signal. The
functions perform no path read. Private local-algebra/render helpers are test
surfaces only, never acceptance authority. A recomputable digest carried only
by the aggregate is insufficient authority.

The result is rowless, but rowlessness is not anonymity. Sparse source
signatures and per-card categorical diagnostics may fingerprint public source
configurations. This is an explicit limitation and a reason not to extend the
same structure to private or participant-level material without a new design
review.

It must not contain:

- source-material paths;
- participant, speaker, meeting, or conversation identifiers;
- annotation or transcript text;
- audio references;
- participant- or segment-level rows;
- predictions, probabilities, features, or model metrics;
- protected-characteristic inference; or
- runtime approval.

## Validation Strategy

The independent validator must fail closed on:

- proxy labels presented as direct;
- acted or scripted sources presented as admissible;
- conversation-level labels presented as temporally local;
- missing provenance, version, license, retrieval, or source hash;
- single-rater or unverifiable reliability claims;
- one signal borrowing another signal's evidence;
- missing, wrong, noncanonical, or wrong-schema caller-supplied protocol,
  search-ledger, source-ledger, or review-receipt bytes;
- a blocked review receipt, forged cross-ledger hash, incompatible source
  rewritten as admissible, search/fallback rewrite, or any aggregate field that
  differs from the deterministic four-input projection;
- a per-signal evidence-card hash sequence that is missing, extra, reordered,
  or cross-signal-swapped relative to the bound source ledger;
- an annotation plan incorrectly producing `pass`;
- incomplete query, citation, receipt, or stop-rule evidence;
- a deferred or failed signal appearing in the C2-eligible list;
- inconsistent candidate, signal, or overall decision algebra;
- a V1 payload, malformed lane witness, invalid citation anchor, or
  lane/global reconciliation mismatch;
- discovery beyond a lane's complete-query capacity or overflow on an
  unsaturated direct/fallback order;
- a malformed, unsorted, duplicated, or unreconciled sparse source signature;
- a source-signature document count inconsistent with its mask, cap, or the
  exact global document count;
- a per-card claimed status/reason, source-signature, document-mask, proxy, or
  positive-count contradiction;
- a fallback claim inconsistent with its exact per-signal material status
  counts;
- nonzero search-meta reason counts or residual reason counts without an exact
  local witness;
- a result larger than `524288` bytes;
- unknown schema keys, reason codes, or signal names;
- model metrics or participant-level content in the canonical pair;
- a true runtime or provider authority flag; or
- customer-emotion, conversion, safety, or production claims.

Focused mutation tests must cover every rejection class.

Repeated generation from identical inputs must produce identical canonical
UTF-8 LF bytes and hashes. Candidate and checkpoint validation must reject
mode/report contradictions independently of renderer equality.

Independent review must inspect the authoritative source documentation and
decision derivation. It cannot trust generator labels or external evaluator
summaries.

Candidate-to-canonical acceptance also requires:

- the complete focused test suite;
- the relevant pinned predecessor suites;
- the project-wide guarded ledger;
- thesis-update and reference-registry gates;
- project drift and context-reading guards;
- protected-runtime diff;
- `git diff --check`;
- exact candidate/canonical pair validation;
- independent severity review of the frozen bytes.

After the separately authorized commit, final closeout additionally requires a
clean post-commit worktree and committed-HEAD reruns of the bounded final
ledger. A post-commit condition cannot gate the earlier acceptance
transaction.

## Overall Decision Rule

The ordered overall decisions are:

- `proceed_full_to_c2`: all five signals are `pass`;
- `proceed_partial_to_c2`: one to four signals are `pass`;
- `defer_c2`: no signal passes and at least one signal is `defer`;
- `stop_c2`: no signal passes and all five signals are `fail`.

Only `pass` signals may appear in the C2-eligible list. No outcome authorizes
C2 automatically.

Every outcome is research-only and must set `runtime_approved=false`.

## Downstream Gates

### Phase C2 Model Evaluation

If separately approved, C2 may evaluate only Phase C1-admitted signals. It
must use a new untouched evaluation design, not the closed Phase B lockbox, and
must compare:

- transcript-only evidence;
- acoustic-only evidence;
- multimodal evidence; and
- frozen non-emotion baselines.

C2 must independently address calibration, useful abstention,
dependency-disjoint robustness, slice stability, and domain limitations.

### Guarded Policy Adapter

A typed text-only sales decision, action and persuasion-intensity lattice,
differential monotonicity proof, and refusal/do-not-call preservation remain a
separate checkpoint. Phase C1 provides no policy authority.

### Sales-Shaped, Shadow, Provider, And Runtime Work

Sales-shaped research, private or customer data, offline shadow replay,
providers, PSTN/ASR/latency work, calls, prompts, knowledge bases, and runtime
activation each require later governance and evidence gates.

## Risks And Limitations

The canonical report must retain this exact ten-item order and wording:

- Observer labels measure perception, not hidden internal emotion.
- Language, culture, speaker, population, and domain bias remain.
- Public conversational corpora may not resemble sales calls.
- Recording modality and bounded context may change judgments.
- Rare signals may prevent reliable annotation or later evaluation.
- License, consent, or incomplete documentation may leave a promising source
  unresolved.
- Agreement does not prove construct truth.
- Partial admission does not validate the other signals.
- No public-data result alone proves real-call, provider, latency, safety,
  conversion, or production behavior.
- Sparse source signatures and per-card categorical diagnostics may fingerprint
  public source configurations.

## Explicit Exclusions

This design and its documentation commit exclude:

- public source research or network access;
- source-document retrieval;
- public or private dataset access;
- audio, transcript, annotation, participant, or feature-row reads;
- dependency installation or update;
- annotation execution;
- model training, tuning, inference, or evaluation;
- source-code adaptation from external repositories;
- provider or ElevenLabs access;
- calls or conversational simulations;
- prompt, knowledge-base, voice, LLM, phone, or provider-setting changes;
- BRAIN integration;
- temporal-tracker or product-runtime changes;
- candidate or canonical generation;
- lockbox access;
- automatic cross-call learning or evolution;
- push, merge, or history rewrite;
- Phase C2 implementation;
- guarded policy-adapter implementation;
- shadow or runtime activation; and
- production, commercial, conversion, safety, true-emotion, or real-customer
  claims.

## Design Approval Record

Tarik approved these design decisions in sequence on 2026-07-26:

1. Phase C1 operational-signal evidence admission as the next checkpoint;
2. direct observer labels only, with no proxy mappings;
3. independent per-signal `pass`, `fail`, or `defer` decisions;
4. turn- or time-segment-level labels only;
5. spontaneous conversational evidence for `pass`;
6. source-and-label admission in C1, with model evaluation deferred to C2;
7. a preregistered independent-human annotation fallback when existing public
   annotations do not qualify;
8. corpus-first source screening before annotation;
9. exact purpose, boundary, decision, construct, discovery, annotation,
   reliability, transaction, validation, and downstream-gate sections; and
10. writing the approved design into the repository.

No visual companion was required because the material design question was an
evidence-governance sequence rather than a spatial or interaction-design
problem.
