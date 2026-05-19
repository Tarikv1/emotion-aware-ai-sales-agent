# DIALOGUE-REASONER-003 Hybrid Gate Evaluation

- Mode: `live`
- Blocked reason: `None`
- Cases: `100`
- Guard batch: `30/30`
- Invocation gate batch: `30/30`
- Reasoning quality batch: `37/40`
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

- `reason-product-route-signal-summary`: `pass`, latency `3812.897` ms
- `reason-product-what-do-you-do`: `pass`, latency `4241.504` ms
- `reason-product-what-does-it-do`: `pass`, latency `3988.314` ms
- `reason-product-inbound-demo`: `pass`, latency `4012.377` ms
- `reason-product-manager-visibility`: `pass`, latency `5103.491` ms
- `reason-product-ownership`: `pass`, latency `4445.859` ms
- `reason-workflow-included`: `pass`, latency `4566.958` ms
- `reason-workflow-steps`: `pass`, latency `3536.35` ms
- `reason-workflow-after-price`: `pass`, latency `4354.535` ms
- `reason-workflow-shared-inbox`: `pass`, latency `6701.664` ms
- `reason-workflow-slack`: `pass`, latency `4156.541` ms
- `reason-workflow-handoff-review`: `pass`, latency `5718.122` ms
- `reason-manual-spreadsheet`: `pass`, latency `4975.827` ms
- `reason-manual-current-process`: `pass`, latency `4093.199` ms
- `reason-manual-not-broken`: `pass`, latency `5345.568` ms
- `reason-manual-small-volume`: `pass`, latency `4566.026` ms
- `reason-manual-owner-routing`: `pass`, latency `4309.527` ms
- `reason-manual-enough`: `pass`, latency `4708.764` ms
- `reason-selected-handoffs-price`: `pass`, latency `4343.544` ms
- `reason-selected-callbacks-price`: `pass`, latency `3605.683` ms
- `reason-selected-routing-price`: `pass`, latency `3706.267` ms
- `reason-selected-handoff-delay`: `pass`, latency `3473.311` ms
- `reason-selected-callback-urgency`: `pass`, latency `12052.933` ms
- `reason-selected-owner-confusion`: `pass`, latency `4566.044` ms
- `reason-selected-manager-misses`: `pass`, latency `4261.635` ms
- `reason-selected-reminders`: `pass`, latency `3711.324` ms
- `reason-fit-situation`: `pass`, latency `5222.994` ms
- `reason-fit-relevant`: `fail`, latency `4572.196` ms
- `reason-fit-small-team`: `pass`, latency `4759.2` ms
- `reason-fit-low-volume`: `pass`, latency `5293.252` ms
- `reason-fit-current-crm`: `pass`, latency `4430.432` ms
- `reason-fit-team-process`: `pass`, latency `5916.535` ms
- `reason-effort-worth-time`: `pass`, latency `4078.864` ms
- `reason-effort-too-much`: `pass`, latency `4062.871` ms
- `reason-effort-busy`: `pass`, latency `4195.801` ms
- `reason-effort-switching`: `fail`, latency `5269.094` ms
- `reason-topic-shift-product`: `pass`, latency `4286.174` ms
- `reason-topic-shift-workflow`: `pass`, latency `4696.099` ms
- `reason-topic-shift-manual`: `fail`, latency `4255.644` ms
- `reason-topic-shift-fit`: `pass`, latency `4052.646` ms
