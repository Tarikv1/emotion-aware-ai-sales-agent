# EMOTION-STATE-001 Annotation Codebook

## Evidence Available To Reviewers

- Give each trained reviewer the customer audio turn, its transcript, and one or two preceding turns only when needed for context.
- Use three independent reviewers per labelled turn.
- Before accepted annotation, every reviewer completes a codebook-calibration practice set excluded from discovery and evaluation.
- Any codebook change invalidates prior calibration for new labels; rerun the practice set before accepting more labels.
- Do not ask customers for emotional self-report. Record only unsolicited direct statements already present in approved evidence.

## Evidence Hidden From Reviewers

- Hide model predictions, provider/LLM evaluator labels, conversion or appointment outcomes, future turns, and every other reviewer's labels.

## Label Fields

- Freeze valence to `-2..2`; freeze activation and engagement to `1..5`; do not change these scales without a reviewed schema version.
- Treat hesitation, frustration, confusion, interest, and disengagement as separate binary operational signals.
- Use only the enumerated reviewer-confidence values and `not_inferable` reason codes in `annotation_record_v1.schema.json`.
- `none` means all operational signals are negative. It is distinct from `not_inferable` and is never a reviewer-selected signal.
- Record direct explicit evidence as `evidence_class = direct_explicit` plus a redacted, nonreversible `evidence:uuid:<canonical-lowercase-uuid-v4>` reference issued independently of the statement text; never copy or encode the statement text in an identifier. The UUID may point only to a separately validated redacted evidence record in an approved research store.

## `not_inferable` And `ambiguous`

- `not_inferable` is mutually exclusive with dimensional and operational labels and requires an enumerated reason.
- Two or more `not_inferable` ratings produce `label_status = not_inferable`.
- One `not_inferable` rating is missing evidence; the other two reviewers must agree on every dimensional and operational label or the result is `ambiguous`.
- Unusable audio, insufficient context, or unresolved disagreement produces `ambiguous`; never force consensus.
- Retain reviewer-level disagreement records; do not overwrite them with the aggregate label.

## Consensus Rules

- Operational consensus-positive requires two of three reviewers.
- Dimensional consensus is the median of valid ordinal ratings.
- `not_inferable` and `ambiguous` turns are excluded from positive/negative supervised-label denominators but retained in end-to-end eligibility, abstention, and coverage metrics.
- Model non-abstention on a `not_inferable` reference turn is an abstention-policy error.

## Agreement Metrics

- Use ordinal Krippendorff's alpha for valence, activation, and engagement.
- Use nominal Krippendorff's alpha separately for each binary operational signal.
- Report speaker-clustered confidence intervals and per-label prevalence; do not pool disagreement into a favorable score.
- Derive every split dependency summary from the complete immutable three-reviewer records for its cases; reject missing records, mismatched summaries, and cross-partition speaker/call/dyad/corpus/scenario overlap.

## Privacy Boundary

- Do not persist unrestricted transcript quotes, raw customer audio, reusable customer identity, provider payloads, or secrets in tracked annotation artifacts.
- Pseudonymous dependency-group IDs are research-only and must remain consistent across the three records for one turn.
