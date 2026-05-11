# PROD-046A German Naturalized Policy Regression

PROD-046A verifies the PROD-045 runtime-policy surface with naturalized German de-DE customer utterances. The cases preserve runtime intent and customer move IDs without literal translation, external scripts, or transcript text.

## German Changes

- German phrase triggers added: `true`.
- German localized responses changed: `true`.
- English PROD-045 regression still passed after the German changes.

## Results

- German positive cases: 66
- German positive passes: 66
- German positive failures: 0
- German false-positive cases: 6
- German false-positive passes: 6
- German false-positive failures: 0
- Unknown-runtime-signal count: 0
- Generic German clarification count: 0
- German response language mismatches: 0
- English operational wording hits: 0
- ASCII German limitation hits: 0

## Boundaries

- Retrieval enabled: `false`
- Provider calls made: `false`
- LLM used: `false`
- Private data read: `false`
- Payment collection allowed: `false`
- Contract signing allowed: `false`
- Production runtime promotion allowed: `false`
- Voice playback unblocked: `false`
- Public demo polish unblocked: `false`

Next recommended checkpoint: `PROD-046-core-sales-policy-human-review`.
