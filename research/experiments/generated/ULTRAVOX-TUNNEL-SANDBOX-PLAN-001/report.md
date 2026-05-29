# ULTRAVOX-TUNNEL-SANDBOX-PLAN-001 Report

Do not open tunnel in this phase. No Ultravox provider call was made.

Candidate tunnel choices for a later gated phase:
- ngrok
- cloudflared tunnel
- localtunnel

Future gates required:
- `ENABLE_ULTRAVOX_SANDBOX=1`
- `LOCAL_ULTRAVOX_ALLOW_PROVIDER_CALLS=1`
- `LOCAL_ULTRAVOX_ALLOW_PUBLIC_TOOL_TUNNEL=1`
- `PROJECT_ULTRAVOX_TOOL_TOKEN present`
- `ULTRAVOX_API_KEY present`

Minimum safety controls:
- random auth token
- synthetic prompts only
- no real customer data
- no outbound phone
- endpoint path unguessable if possible
- short-lived tunnel
- logs sanitized
- stop tunnel after run

Dashboard and durable tool setup should wait until the temporary tool passes.
