# DIALOGUE-REASONER-002 LLM Provider Evaluation

- Mode: `dry-run`
- Blocked reason: `dry-run-mode`
- Planned cases: `30`
- Provider calls made: `false`
- Text sent to provider: `false`
- API key value logged: `false`
- Opens PROD-102: `false`

## Boundary

- Live mode requires `--live` and `--consent-confirmed`.
- Provider config comes from `runtime/config/local/dialogue_reasoner.env`, environment variables, or explicit non-secret flags.
- API key values are not written to generated evidence.
- The live demo response path is not changed by this runner.

## Planned Cases

- `agent-open-starts-sales-call`: prompt chars `5364`
- `greeting-opens-like-sales-call`: prompt chars `5366`
- `caller-identity-recall-after-opener`: prompt chars `5525`
- `clarify-previous-question-qualification`: prompt chars `5603`
- `clarify-previous-question-price`: prompt chars `5569`
- `bare-no-after-opener`: prompt chars `5525`
- `no-time-needs-callback-time`: prompt chars `5512`
- `callback-time-confirms-and-ends`: prompt chars `5434`
- `direct-price-question`: prompt chars `5403`
- `low-info-after-price`: prompt chars `5574`
- `growth-plan-value`: prompt chars `5416`
- `starter-plan-fit`: prompt chars `5409`
- `product-explanation`: prompt chars `5414`
- `workflow-scope`: prompt chars `5410`
- `manual-tracking-objection`: prompt chars `5436`
- `handoffs-selected-after-price`: prompt chars `5582`
- `callbacks-selected-after-price`: prompt chars `5588`
- `fit-question`: prompt chars `5414`
- `timing-objection`: prompt chars `5404`
- `effort-worth-objection`: prompt chars `5440`
- `salesforce-integration-boundary`: prompt chars `5407`
- `security-boundary`: prompt chars `5387`
- `specialist-not-needed-for-basics`: prompt chars `5443`
- `topic-shift-price-to-product`: prompt chars `5602`
- `topic-shift-price-to-workflow`: prompt chars `5586`
- `repeat-price-without-loop`: prompt chars `5596`
- `generic-followup-after-qualification`: prompt chars `5568`
- `asr-fragment-repair`: prompt chars `5368`
- `off-topic-unclear-turn`: prompt chars `5579`
- `recommendation-request-preserves-agency`: prompt chars `5581`
