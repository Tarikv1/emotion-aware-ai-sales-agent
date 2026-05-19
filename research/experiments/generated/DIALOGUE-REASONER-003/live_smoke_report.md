# DIALOGUE-REASONER-003 Hybrid Gate Evaluation

- Mode: `live`
- Blocked reason: `None`
- Cases: `61`
- Guard batch: `30/30`
- Invocation gate batch: `30/30`
- Reasoning quality batch: `1/1`
- Provider calls made: `true`
- Text sent to provider: `true`
- API key value logged: `false`
- Runtime route override allowed: `false`
- Opens PROD-102: `false`

## Boundary

- Deterministic runtime owns dialogue act, buyer intent, topic, sales stage, response strategy, safety boundary, and call control.
- The provider may only return reasoning enrichment fields for allowed cases.
- Provider config comes from ignored local env, process env, or explicit non-secret flags.
- Live mode requires `--live` and `--consent-confirmed`.

## Live Reasoning Results

- `reason-product-route-signal-summary`: `pass`, latency `4126.721` ms
