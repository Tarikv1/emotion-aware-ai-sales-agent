# ULTRAVOX-WARM-SESSION-LATENCY-001

Run status: `warm_session_latency_measured`
Blocker: `None`

## Gates
Env file ignored: `true`
API key present: `true`
Tool token present: `true`
Prepared audio available: `true`
Prepared audio input count: `2`
Repeated synthetic inputs used: `true`

## Hosted Session
Provider call made: `true`
Session created: `true`
WebSocket connected: `true`
Audio turns attempted: `4`
Audio turns completed: `4`
Warm measured turn count: `3`

## Latency
Warm p50 first-agent-audio latency seconds: `4.638`
Warm p90 first-agent-audio latency seconds: `5.148`
Measured warm latencies seconds: `[4.001, 5.148, 4.638]`
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

Decision recommendation: `test voice/session settings and warm-run repeat once`
