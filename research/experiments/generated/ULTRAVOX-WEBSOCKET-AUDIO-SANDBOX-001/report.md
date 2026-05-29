# ULTRAVOX-WEBSOCKET-AUDIO-SANDBOX-001

Run status: `blocked_synthetic_audio_generation_failed`
Blocker: `System.Speech failed; SAPI.SpVoice fallback failed. Exception calling "Speak" with "1" argument(s): "No voice installed on the system or none available with the current security setting." At line:6 char:1 + $synth.Speak('What is this?') | Out-Null + ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ + CategoryInfo : NotSpecified: (:) [], ParentContainsErrorRecordException + FullyQualifiedErrorId : InvalidOperationException SAPI.SpVoice generation failed: (-2147352567, 'Exception occurred.', (0, None, None, None, 0, -2147200960), None)`

## Gates
Env file ignored: `true`
API key present: `true`
Tool token present: `true`
Synthetic audio generated: `false`
Public endpoint preflight passed: `false`

## Hosted Session
Provider call made: `false`
Ultravox session created: `false`
Join URL received: `false`
WebSocket connected: `false`
Audio turns attempted: `0`
Audio turns completed: `0`

## Audio And Transcript
User transcript count: `0`
Agent transcript count: `0`
Agent audio chunks received: `0`
Agent audio bytes received: `0`
Output audio duration seconds: `None`
First agent audio latency seconds: `None`
First transcript latency seconds: `None`

## Tool Boundary
Local HTTP tool request count: `0`
Tool call attempted: `false`
Tool call succeeded: `false`
Product truth drift count: `0`
Unsupported claim count: `0`
Fake side effect count: `0`
CRM/email/calendar claim count: `0`

## Boundaries
Agent audio files written under local_artifacts: `[]`
Raw audio stored public: `false`
Audio committed: `false`
Live wiring allowed: `false`
Production call allowed: `false`
Runtime behavior changed: `false`
Response text changed: `false`

Decision recommendation: `prepare local synthetic audio inputs manually`
