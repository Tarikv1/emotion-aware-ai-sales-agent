# ULTRAVOX-AUDIO-LATENCY-AUDIT-001

First agent audio latency seconds: `8.599`
Current observed latency seconds: `8.599`
Live target seconds: `2-3`
Live-ready latency: `false`
Promising with warm session: `unknown`
Needs warm-turn benchmark: `true`
Another provider run should separate cold-start vs warm-turn latency: `true`

## Breakdown
Session creation time ms: `510.012`
Tunnel setup time ms: `881.747`
Public endpoint preflight time ms: `130.34`
WebSocket connect latency ms: `324.111`
Ping round trip ms: `176.85`
First transcript latency seconds: `5.341`
First user transcript latency seconds: `None`
Tool request latency ms: `None`
Time from tool response to agent audio seconds: `None`

## Interpretation
First agent audio latency likely includes session setup/startup: `false`
First agent audio latency likely includes first-turn startup: `true`
The runner starts first_agent_audio_latency_seconds immediately before sending the first audio turn, after tunnel setup, session creation, and WebSocket connection. It likely includes first-turn audio upload, transcription, tool, model, and voice startup, but not tunnel/session setup.

## Boundaries
New provider call made: `false`
New audio generated: `false`
Audio files copied: `false`
Audio files committed: `false`
Outbound phone call made: `false`
Real customer data used: `false`
Raw private audio or transcripts used: `false`
Live wiring allowed: `false`
Production call allowed: `false`
Runtime behavior changed: `false`
Response text changed: `false`
