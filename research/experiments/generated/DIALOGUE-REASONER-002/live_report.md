# DIALOGUE-REASONER-002 LLM Provider Evaluation

- Mode: `live`
- Blocked reason: `None`
- Cases: `18/30`
- Provider calls made: `true`
- Text sent to provider: `true`
- API key value logged: `false`
- Opens PROD-102: `false`

## Boundary

- Live mode requires `--live` and `--consent-confirmed`.
- Provider config comes from `runtime/config/local/dialogue_reasoner.env`, environment variables, or explicit non-secret flags.
- API key values are not written to generated evidence.
- The live demo response path is not changed by this runner.

## Live Results

- `agent-open-starts-sales-call`: `pass`, latency `2528.149` ms
- `greeting-opens-like-sales-call`: `pass`, latency `2230.326` ms
- `caller-identity-recall-after-opener`: `pass`, latency `2656.923` ms
- `clarify-previous-question-qualification`: `pass`, latency `3353.671` ms
- `clarify-previous-question-price`: `fail`, latency `4509.118` ms
- `bare-no-after-opener`: `fail`, latency `3456.782` ms
- `no-time-needs-callback-time`: `pass`, latency `2263.675` ms
- `callback-time-confirms-and-ends`: `pass`, latency `2425.705` ms
- `direct-price-question`: `fail`, latency `3345.87` ms
- `low-info-after-price`: `pass`, latency `3386.437` ms
- `growth-plan-value`: `fail`, latency `3239.925` ms
- `starter-plan-fit`: `fail`, latency `4556.875` ms
- `product-explanation`: `pass`, latency `3786.414` ms
- `workflow-scope`: `pass`, latency `2818.455` ms
- `manual-tracking-objection`: `fail`, latency `3288.086` ms
- `handoffs-selected-after-price`: `pass`, latency `4235.619` ms
- `callbacks-selected-after-price`: `pass`, latency `3354.766` ms
- `fit-question`: `fail`, latency `4024.468` ms
- `timing-objection`: `fail`, latency `3330.201` ms
- `effort-worth-objection`: `fail`, latency `3618.158` ms
- `salesforce-integration-boundary`: `pass`, latency `3295.399` ms
- `security-boundary`: `pass`, latency `2452.952` ms
- `specialist-not-needed-for-basics`: `fail`, latency `3229.903` ms
- `topic-shift-price-to-product`: `pass`, latency `3424.921` ms
- `topic-shift-price-to-workflow`: `pass`, latency `3139.348` ms
- `repeat-price-without-loop`: `pass`, latency `4581.189` ms
- `generic-followup-after-qualification`: `fail`, latency `5490.024` ms
- `asr-fragment-repair`: `pass`, latency `2236.702` ms
- `off-topic-unclear-turn`: `fail`, latency `3171.373` ms
- `recommendation-request-preserves-agency`: `pass`, latency `3661.236` ms
