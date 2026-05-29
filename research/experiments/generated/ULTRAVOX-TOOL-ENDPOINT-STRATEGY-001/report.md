# ULTRAVOX-TOOL-ENDPOINT-STRATEGY-001 Report

No Ultravox provider call was made. No public tunnel was opened.

## Options

### 1. HTTP tool with temporary HTTPS tunnel

Local FastAPI or stdlib HTTP endpoint first, then a later short-lived ngrok, cloudflared, or localtunnel exposure. This is the primary next path after local validation because it is the quickest hosted sandbox path and matches Ultravox HTTP tools.

Risks: public endpoint exposure, auth required, tunnel provider logging and URL leakage risk.

### 2. Client tool

Tool runs in a browser or client app. This has lower server exposure and fits a future browser/WebRTC demo, but it likely requires client/SDK work and is not the fastest next sandbox path.

### 3. Data connection tool

Websocket or server-side real-time channel. This may fit a long-term product architecture but is more complex and is not the first sandbox path unless HTTP tools are blocked.

## Decision

Build the local HTTP endpoint first, validate it locally, then in a later gated phase expose it through a temporary HTTPS tunnel for the hosted Ultravox sandbox.

Use a temporary per-call tool for testing. Dashboard and durable tool setup should wait until the endpoint schema is stable, secret handling is confirmed, and the temporary endpoint passes.
