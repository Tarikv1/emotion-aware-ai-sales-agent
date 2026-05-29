# ULTRAVOX-HOSTED-SANDBOX-001 Report

Run status: `not_run`
Sandbox run: `false`
Blocker: Ultravox env gates were not enabled; provider sandbox skipped by default.
Env file exists: `true`
Env file ignored by Git: `true`
Env file loaded: `true`
API key present: `false`
Provider call made: `false`
Tool call attempted: `false`
Tool call succeeded: `false`
Public tool endpoint required: `true`
Public tool endpoint available: `false`
Synthetic cases attempted: `0`
Outbound phone calls made: `false`
Real customer data used: `false`
Raw private audio or transcripts used: `false`
Audio committed: `false`
Live wiring allowed: `false`
Production call allowed: `false`
Runtime behavior changed: `false`
Response text changed: `false`

## Env Gates

- ENABLE_ULTRAVOX_SANDBOX=1: `false`
- ULTRAVOX_API_KEY present: `false`
- LOCAL_ULTRAVOX_ALLOW_PROVIDER_CALLS=1: `false`

## Tool Boundary

Tool-call behavior: `unknown` support, attempted `false`.
The project runtime remains the sales brain, campaign truth source, verifier, and canonical memory owner.

## Source Grounding

- [https://docs.ultravox.ai/gettingstarted/how-ultravox-works](https://docs.ultravox.ai/gettingstarted/how-ultravox-works): Ultravox supports REST call creation and joining through SDKs, telephony, or WebSockets; API integration gives control over custom tools and call flows.
- [https://docs.ultravox.ai/tools/overview](https://docs.ultravox.ai/tools/overview): Tools connect agents to external systems and can retrieve information or perform actions.
- [https://docs.ultravox.ai/tools/custom/http-vs-client-tools](https://docs.ultravox.ai/tools/custom/http-vs-client-tools): HTTP tools run on your server and Ultravox calls them via HTTP; client tools run in the client application.
- [https://docs.ultravox.ai/tools/custom/durable-vs-temporary-tools](https://docs.ultravox.ai/tools/custom/durable-vs-temporary-tools): Temporary tools are defined inline for API-created calls; durable tools are reusable and can be managed through API or web app.
- [https://docs.ultravox.ai/agents/call-stages](https://docs.ultravox.ai/agents/call-stages): Call stages can use tools for stage changes and need explicit prompt/tool configuration.
- [https://docs.ultravox.ai/gettingstarted/prompting](https://docs.ultravox.ai/gettingstarted/prompting): Prompts should contain full voice-agent behavior, including tool use and spoken-response guidance.
