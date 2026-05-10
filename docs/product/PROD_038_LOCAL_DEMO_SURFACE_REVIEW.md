# PROD-038 Local Demo Surface Review

PROD-038 records the review outcome for the `PROD-037` local trace demo surface.

The surface structure is useful, but the conversation content is not accepted. The customer responses are too artificial, too cooperative, and too evaluation-like for a convincing sales-agent demo.

## Local Commands

```powershell
python scripts\run_prod_038_local_demo_surface_review.py
python scripts\validate_prod_038_local_demo_surface_review.py
```

## Outputs

- `research/experiments/generated/PROD-038-local-demo-surface-review/result.json`
- `research/experiments/generated/PROD-038-local-demo-surface-review/report.md`
- `research/experiments/generated/PROD-038-local-demo-surface-review/local_demo_surface_review_packet.json`

## Result

- Demo surface UI accepted: `true`
- Customer response realism accepted: `false`
- Conversation quality gate passed: `false`
- Reviewed calls: `8`
- Reviewed turns: `14`
- Customer response issue count: `5`
- Voice playback unblocked: `false`
- Scenario branching unblocked: `false`
- More call seeds unblocked: `false`
- Public demo polish unblocked: `false`
- Next build recommendation: `customer_realism_simulator_hardening`

## Decision

The next checkpoint is `PROD-039-customer-realism-simulator-hardening`.

PROD-039 should keep the same fixed calls and improve customer-response realism before any voice playback, scenario branching, more seeds, or public-facing demo polish.

## Customer Response Issues

- Customers accept too cleanly after one or two answers.
- Customer wording uses evaluation labels that belong in metadata, not spoken dialogue.
- State transitions are too neat and cooperative.
- Follow-up questions are too helpful and sales-ready.
- Safety boundaries appear in unnatural buyer wording instead of staying in flags and expected outcomes.

## Boundary

PROD-038 does not call providers, call an LLM, read private data, download datasets, start a server, collect payment, enable retrieval by default, enable composer hooks by default, change runtime behavior, unblock voice playback, unblock public demo polish, or allow production runtime promotion.
