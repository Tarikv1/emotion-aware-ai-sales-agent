# PROD-038 Local Demo Surface Review

PROD-038 records the review outcome for the PROD-037 local trace demo surface. The surface structure is useful, but the customer responses are not realistic enough for the next demo expansion.

## Result

- Checkpoint id: `PROD-038-local-demo-surface-review`
- Source checkpoint: `PROD-037-local-interactive-trace-demo-surface`
- Reviewed calls: `8`
- Reviewed turns: `14`
- Demo surface UI accepted: `true`
- Customer response realism accepted: `false`
- Conversation quality gate passed: `false`
- Customer response issue count: `5`
- Voice playback unblocked: `false`
- Scenario branching unblocked: `false`
- More call seeds unblocked: `false`
- Public demo polish unblocked: `false`
- Next build recommendation: `customer_realism_simulator_hardening`
- Next checkpoint: `PROD-039-customer-realism-simulator-hardening`

## Customer Response Issues

- `over-cooperative-acceptance` (blocker): Some customers accept too cleanly after one or two answers, which makes the sale path feel scripted instead of earned.
- `evaluator-like-wording` (blocker): Customer lines describe benchmark states such as accepting a non-binding review or rejecting the deal in language no buyer would normally use.
- `too-clean-state-transition` (blocker): Replies move neatly from one objection category to the next instead of mixing confusion, skepticism, interruptions, and partial understanding.
- `low-friction-follow-up` (major): Follow-up questions are too helpful and sales-ready, so customers sound like cooperative test fixtures.
- `artificial-boundary-language` (major): Customers mention safety boundaries such as billing handling in unnatural ways.

## Next Customer-Realism Requirements

- customer dialogue must not use evaluation labels
- acceptance must be less immediate and more conditional
- rejections must sound like real buyer pushback, not status declarations
- follow-up questions must include realistic vagueness, friction, and incomplete understanding
- safety boundaries stay in metadata instead of buyer wording
- the same fixed calls must be rerun before claiming improvement

## Boundary

PROD-038 does not call providers, call an LLM, read private data, download datasets, start a server, collect payment, enable retrieval by default, enable composer hooks by default, change runtime behavior, unblock voice playback, unblock public demo polish, or allow production runtime promotion.
