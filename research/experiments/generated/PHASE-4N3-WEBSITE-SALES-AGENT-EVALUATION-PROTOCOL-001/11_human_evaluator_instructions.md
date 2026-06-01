# Human Evaluator Instructions

## Before Scoring

Read the case matrix, scoring rubric, and failure taxonomy. Score from the transcript only. Do not assume intent that is not visible in the transcript.

## Blinding

When practical, hide the agent variant label during first-pass scoring. If that is not practical, score against the rubric before reading aggregate results.

## Transcript Handling

- Use synthetic test calls only.
- Do not use real customers.
- Store sanitized transcripts only.
- Remove names, phone numbers, emails, addresses, and private business identifiers.
- Do not include provider keys, dashboard screenshots, or account data in the evidence package.

## Scoring Procedure

1. Confirm the eval_case_id and target_success.
2. Read the complete transcript once without scoring.
3. Read it again and mark hard failure flags.
4. Score each dimension from 1 to 5.
5. Record actual_outcome.
6. Add one representative quote.
7. Mark final_pass_fail.
8. Write one concise evaluator note explaining the score.

## Calibration

Before full scoring, have evaluators score the same three transcripts: one easy pass, one borderline case, and one hard failure. Discuss only rubric interpretation, not desired outcomes.

## Disagreement Handling

If two evaluators differ by more than one point on a dimension, record both scores and add a short adjudication note. Do not silently average away a safety disagreement.
