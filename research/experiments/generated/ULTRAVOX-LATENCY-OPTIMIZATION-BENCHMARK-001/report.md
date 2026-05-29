# ULTRAVOX-LATENCY-OPTIMIZATION-BENCHMARK-001

Run status: `latency_optimization_measured`
Blocker: `None`

## Gates
Env file ignored: `true`
API key present: `true`
Tool token present: `true`
Prepared audio available: `true`
Repeated synthetic inputs used: `true`

## Optimized Session
Provider call made: `true`
Session created: `true`
WebSocket connected: `true`
Audio turns attempted: `4`
Audio turns completed: `4`
Warm measured turn count: `3`
Voice selection applied: `false`

## Latency
Optimized p50 first-agent-audio latency seconds: `4.69`
Optimized p90 first-agent-audio latency seconds: `6.073`
Measured warm latencies seconds: `[3.58, 4.69, 6.073]`
Per-turn latency uses client-observed receive times after each prepared audio send finishes; it does not store raw provider audio in public evidence.

## Tool Boundary
Local HTTP tool request count: `4`
Tool call attempted: `true`
Tool call succeeded: `true`
Tool boundary enforced: `true`
Product truth drift count: `0`
Fake side effect count: `0`
CRM/email/calendar claim count: `0`

## Boundaries
No new audio generated: `true`
Raw audio stored public: `false`
Audio committed: `false`
Live wiring allowed: `false`
Production call allowed: `false`
Runtime behavior changed: `false`
Response text changed: `false`
