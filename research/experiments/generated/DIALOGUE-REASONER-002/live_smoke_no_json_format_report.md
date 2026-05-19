# DIALOGUE-REASONER-002 LLM Provider Evaluation

- Mode: `live`
- Blocked reason: `None`
- Cases: `0/1`
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

- `agent-open-starts-sales-call`: `fail`, latency `45085.971` ms
