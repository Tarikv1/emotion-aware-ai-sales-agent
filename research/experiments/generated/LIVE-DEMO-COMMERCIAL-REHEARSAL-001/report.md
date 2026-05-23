# LIVE-DEMO-COMMERCIAL-REHEARSAL-001 Report

## Summary
- Status: `ready_for_human_review`
- This packet is generated from ignored local private live-demo artifacts and redacts buyer transcript text.

## Private Input Discovery Count
- Private JSON files discovered: `418`
- Parsed rehearsal records: `418`
- Unreadable private inputs: `0`

## Rehearsal Record Count
- Records available for human review: `418`

## Campaign Coverage Found In Private Evidence
- `campaign-prod-005-b2b-software`
- `campaign-prod-005-b2c-telecom`
- `synthetic-automotive-service-review`
- `synthetic-healthcare-admin-review`
- `synthetic-insurance-review`

## Mechanical Issue Counts
- `audio_url_missing_when_provider_called`: `1`
- `call_control_unexpected`: `18`
- `final_response_missing`: `20`
- `provider_audio_failed`: `1`
- `repeated_response`: `28`
- `response_too_long_for_live_voice`: `3`
- `tts_input_missing`: `20`

## Top Concerning Rehearsal Records By Mechanical Signals Only
- `live-demo-commercial-rehearsal-001-0104`: `2` flags (provider_audio_failed, audio_url_missing_when_provider_called)
- `live-demo-commercial-rehearsal-001-0262`: `2` flags (final_response_missing, tts_input_missing)
- `live-demo-commercial-rehearsal-001-0290`: `2` flags (final_response_missing, tts_input_missing)
- `live-demo-commercial-rehearsal-001-0291`: `2` flags (final_response_missing, tts_input_missing)
- `live-demo-commercial-rehearsal-001-0292`: `2` flags (final_response_missing, tts_input_missing)
- `live-demo-commercial-rehearsal-001-0293`: `2` flags (final_response_missing, tts_input_missing)
- `live-demo-commercial-rehearsal-001-0294`: `2` flags (final_response_missing, tts_input_missing)
- `live-demo-commercial-rehearsal-001-0295`: `2` flags (final_response_missing, tts_input_missing)
- `live-demo-commercial-rehearsal-001-0296`: `2` flags (final_response_missing, tts_input_missing)
- `live-demo-commercial-rehearsal-001-0297`: `2` flags (final_response_missing, tts_input_missing)
- `live-demo-commercial-rehearsal-001-0298`: `2` flags (final_response_missing, tts_input_missing)
- `live-demo-commercial-rehearsal-001-0299`: `2` flags (final_response_missing, tts_input_missing)

## Safety Boundary Summary
- Generator provider calls made: `false`
- Validator provider calls made: `false`
- Validator live TTS calls made: `false`
- Raw private transcript text included: `false`
- Raw customer audio found: `false`

## What ChatGPT/human reviewer should evaluate next
- Compare hashed transcript source records with authorized private artifacts only when needed.
- Check ASR accuracy, latency, turn-taking, TTS playback, spoken text match, and commercial next-step quality.
- Verify campaign selector integrity under RouteSignal and generic campaign switching.

## Recommended Live Rehearsal Scenarios
### A. RouteSignal normal path
- Start RouteSignal
- Permission
- callbacks are a problem
- it causes delays
- tomorrow at 3 works

### B. RouteSignal challenge path
- what does your product do
- why should I care
- are you a robot
- who are you

### C. Generic insurance product-detail path
- select synthetic insurance
- what does your product do
- so you cannot give me details?
- maybe coverage fit
- it is active now
- it wastes time

### D. Rapport/hardship path
- I'm driving
- I just got out of the hospital
- everything is expensive right now
- last company like this wasted my time

### E. ASR stress path
- yeah that would be good
- okay that would be good
- call me tomorrow at 3
- say deliberately noisy or short phrases and check repair behavior

### F. Campaign selector integrity
- Start with RouteSignal selected
- Switch to generic insurance
- Switch back to RouteSignal
- Confirm campaign metadata and response content do not mix

## Next Likely Implementation Area
- Preliminary only: use this packet to decide whether live-call issues are ASR, browser turn-taking, TTS playback, campaign selection, or dialogue quality before changing runtime behavior.
