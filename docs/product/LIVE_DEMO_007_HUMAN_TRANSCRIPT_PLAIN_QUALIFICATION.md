# LIVE-DEMO-007 Human Transcript And Plain Qualification

`LIVE-DEMO-007-human-readable-transcript-and-plain-qualification` is a narrow follow-up to Tarik's supervised `LIVE-DEMO-006` browser transcript review.

It does not open `PROD-102`, claim production readiness, add provider ASR, enable payment collection, create a provider-hosted durable agent, use voice cloning, add spoken backchannels, make LLM calls required for live response, or let an LLM write final spoken responses.

## Goal

Improve the live demo in two places that affected the latest listening review:

- make the visible browser transcript human-readable before the raw turn packet
- keep memory/stability/provider diagnostics available, but out of the default transcript view
- stop early qualification from assuming a workflow is already broken
- replace early CRM-workflow jargon with plain lead/follow-up language
- explain terms such as shared inbox, responsible person, handoff, and callback before asking diagnostic questions

## Runtime Behavior

The browser transcript is now the review-first surface. It appears before the raw turn packet and defaults to buyer/agent/call-control lines. Diagnostic memory remains available in the collapsible diagnostics area and in JSON export for debugging.

The early qualification ladder now starts with plain context. If the buyer says "maybe" after the opening, the agent explains that the check is about demo or information requests getting a clear next reply. It does not assume that something is broken.

If the buyer asks what a shared inbox lead means, the agent defines the term before continuing. If the buyer says they do not know, the agent asks one concrete question: who makes sure a demo request gets the next reply.

## Private Transcript Folder

Tarik can place browser transcript JSON files here for local debugging:

```text
data\private\live-demo-003\raw-turns\browser-transcript
```

This folder is private local data. Do not commit transcripts from this folder.

## Commands

Validate the checkpoint without live microphone or provider calls:

```powershell
python scripts\validate_live_demo_007_human_transcript_plain_qualification.py
```

Run the live demo with ElevenLabs after validation:

```powershell
python scripts\run_live_demo_001_agent_voice_call.py --live-tts --consent-confirmed --timeout-seconds 8 --port 8796 --private-out data\private\live-demo-003\raw-turns
```

## Acceptance Criteria

Hard gates:

- no provider-hosted durable agent
- no voice cloning
- no LLM blocking or mutating the live spoken response
- no `PROD-102`
- no raw audio upload to the Python server
- no transcript audio storage
- visible transcript appears before the raw turn packet
- visible transcript defaults to human-readable buyer/agent/call-control lines
- diagnostics remain available separately for debugging
- "maybe" after the opening does not trigger unexplained workflow jargon
- shared-inbox clarification defines the term plainly
- "I don't know" asks one concrete plain-language qualification question

Human live check:

- Tarik can read the transcript without scanning raw memory fields
- the agent explains what it is checking before diagnosing workflow gaps
- early conversation feels more like a sales call and less like an internal CRM checklist

## Evidence

Generated evidence:

- `research/experiments/generated/LIVE-DEMO-007-human-readable-transcript-and-plain-qualification/result.json`
- `research/experiments/generated/LIVE-DEMO-007-human-readable-transcript-and-plain-qualification/report.md`

This checkpoint is supervised demo hardening, not production voice acceptance.
