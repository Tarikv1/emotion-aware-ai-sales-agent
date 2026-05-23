# LIVE-DEMO-COMMERCIAL-REHEARSAL-001 Report

## Summary
- Status: `current_only_no_current_runtime_records`
- This packet is generated from ignored local private live-demo artifacts and redacts buyer transcript text.

## Private Input Discovery Count
- Private JSON files discovered: `460`
- Parsed rehearsal records: `0`
- Unreadable private inputs: `0`
- Current-runtime-marked records: `0`
- Unknown-version records: `425`
- Stale/legacy records: `35`
- Current-only evidence available: `false`

## Evidence Freshness Summary
- `stale_pre_current_runtime_artifact`: `35`
- `unknown_version_private_artifact`: `425`

## Rehearsal Record Count
- Records available for human review: `0`

## Campaign Coverage Found In Private Evidence

## Mechanical Issue Counts

## Current-Only Filter
- Default packet mode includes all archival private live-demo records.
- Run `python scripts\generate_live_demo_commercial_rehearsal_packet_001.py --current-only` to include only records stamped with the current runtime metadata.
- If current-runtime-marked records are `0`, current-only evidence is unavailable and a fresh rehearsal is needed.

## Top Concerning Rehearsal Records By Mechanical Signals Only
- No mechanical issues were detected by this packet generator.

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
