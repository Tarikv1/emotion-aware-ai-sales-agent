# Thesis Results Template

## Method

Describe the controlled manual evaluation design, fixed case matrix, transcript export process, scoring rubric, evaluator workflow, and provider/tool boundaries.

## Agent variants

Summarize VARIANT-A, VARIANT-B, and any later VARIANT-C run. State exactly which files and settings each variant used.

## Evaluation cases

Report the 36-case matrix, vertical coverage, buyer situations, and target_success distribution.

## Metrics

Define the primary and secondary metrics. Include micro-close, follow-up, disqualification, stop-compliance, average score, safety, fake-claim, leakage, and turn-count metrics.

## Quantitative results table

| metric | VARIANT-A generic baseline | VARIANT-B Atlas 4N2 agent | difference | interpretation |
| --- | --- | --- | --- | --- |
| micro_close_success_rate |  |  |  |  |
| qualified_followup_rate |  |  |  |  |
| disqualification_correctness |  |  |  |  |
| stop_request_compliance_rate |  |  |  |  |
| average_sales_progression_score |  |  |  |  |
| average_objection_handling_score |  |  |  |  |
| average_spoken_naturalness_score |  |  |  |  |
| safety_violation_count |  |  |  |  |
| fake_claim_count |  |  |  |  |
| internal_language_leak_count |  |  |  |  |
| average_turns_to_close |  |  |  |  |

## Qualitative failure analysis

Group failures by hard flag, buyer situation, and agent variant. Explain which failures are design issues, platform issues, evaluator ambiguity, or prompt-specific issues.

## Example transcripts

Include short sanitized excerpts only. Do not include real customer data, phone numbers, addresses, emails, or private business details.

## Discussion

Interpret whether the structured campaign package improved sales behavior enough to justify its added complexity.

## Limitations

Discuss manual roleplay, evaluator subjectivity, hosted platform constraints, synthetic case limitations, and absence of real customer outcome data.

## Ethics/compliance

State consent boundaries, no real outbound calls, no live customer testing, no deceptive identity, no fake guarantees, and no account side effects.

## Future work

Define the next controlled iteration, required approval gates, and what evidence would be needed before any real-user or live-call path.
