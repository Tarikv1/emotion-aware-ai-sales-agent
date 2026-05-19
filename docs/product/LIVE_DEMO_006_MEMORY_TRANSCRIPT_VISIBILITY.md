# LIVE-DEMO-006 Memory And Transcript Visibility

`LIVE-DEMO-006-memory-transcript-visibility` is a narrow follow-up to Tarik's supervised live-demo feedback after `LIVE-DEMO-005`.

It does not open `PROD-102`, claim production readiness, add provider ASR, enable payment collection, create a provider-hosted durable agent, use voice cloning, make LLM calls required for live response, or let an LLM write final spoken responses.

## Goal

Improve live-demo reviewability and repetition control without broadening the runtime product scope:

- expose the full current browser-session transcript in the live demo
- allow local JSON and text transcript downloads
- keep transcript data local and text-only
- add compact response signatures and recent response subjects to conversation memory
- prevent exhausted same-focus follow-up fallback text from repeating exactly

## Runtime Behavior

The browser demo now keeps a visible per-turn transcript for the active session. Each turn records the buyer transcript, final agent response, call control, compact conversation memory, stability guard packet, async enrichment boundary packet, provider boundary summary, and server latency. It does not store audio.

The transcript panel is a local review surface for Tarik's supervised demo work. It does not upload customer audio to the Python server, does not create a durable provider agent, and does not change the provider boundary.

Conversation memory now exposes compact `last_response_signatures`, `recent_response_subjects`, `candidate_response_subject`, and `candidate_response_signature` fields. These are deterministic text-derived signals only; they store no secrets and no audio.

## Commands

Validate the checkpoint without live microphone or provider calls:

```powershell
python scripts\validate_live_demo_006_memory_transcript_visibility.py
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
- browser page exposes a full local text transcript for the active session
- transcript can be downloaded as JSON or text
- transcript includes memory, stability guard, async enrichment boundary, provider boundary, and latency fields
- repeated same-focus follow-ups avoid exact duplicate final responses
- compact memory exposes response signatures and recent response subjects

Human live check:

- Tarik can review the whole spoken exchange after a live run
- repeated price or workflow follow-up does not loop around the same sentence
- the transcript gives enough context to diagnose unrelated answers without opening raw private audio

## Evidence

Generated evidence:

- `research/experiments/generated/LIVE-DEMO-006-memory-transcript-visibility/result.json`
- `research/experiments/generated/LIVE-DEMO-006-memory-transcript-visibility/report.md`

This checkpoint is supervised demo hardening, not production voice acceptance.
