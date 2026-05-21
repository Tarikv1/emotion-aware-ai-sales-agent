# LIVE-DEMO-011 Live Follow-Up Stop And Pain Close

`LIVE-DEMO-011-live-followup-stop-and-pain-close` is a narrow follow-up to Tarik's supervised `LIVE-DEMO-010` ElevenLabs listening feedback.

It does not open `PROD-102`, claim production readiness, enable payment collection, create a provider-hosted durable agent, use voice cloning, add provider ASR, install a local LLM, make LLM calls required for live response, or let an LLM write final spoken responses.

## Scope

This checkpoint fixes two follow-up failures observed in the private browser transcripts after `LIVE-DEMO-010`:

- after callback timing was requested, `never` fell into generic timing advice instead of stopping the call
- explicit do-not-call wording ended the call but said too much about internal marking
- confirmed missed-lead pain, including ASR-style `Leeds`, stayed in fit-check wording instead of moving directly to the workflow-review appointment ask

## Behavior

If the buyer says `never` after a callback-time request, the agent ends simply:

```text
Understood. I will stop here. Goodbye.
```

If the buyer explicitly says not to call again, the agent uses the same short stop response without describing internal marking.

If the buyer confirms missed leads after manual tracking or a fit-check question, the agent moves to the current MVP close:

```text
Then the next step is a short workflow review with someone from Northstar. They would check handoff misses against your actual follow-up flow. What time works for a quick call?
```

## Commands

Validate the checkpoint without live microphone, provider ASR, provider TTS, provider LLM calls, or local LLM calls:

```powershell
python scripts\validate_live_demo_011_live_followup_stop_and_pain_close.py
```

Run it with the current LIVE-DEMO regression stack before committing:

```powershell
python scripts\validate_live_demo_001_agent_voice_call.py
python scripts\validate_live_demo_008_prosody_review_scope_clarity.py
python scripts\validate_live_demo_009_appointment_lead_close.py
python scripts\validate_live_demo_010_live_feedback_route_polish.py
python scripts\validate_live_demo_011_live_followup_stop_and_pain_close.py
```

## Acceptance

Synthetic gate:

- provider calls made: `false`
- `never` after callback timing ends the call
- explicit do-not-call wording is plain and short
- ASR-style `Leeds` still maps to missed leads
- confirmed missed-lead pain moves directly to the Northstar workflow-review appointment ask
- no internal runtime phrases are spoken to the customer

Human live check:

- terminal callback refusal sounds respected
- do-not-call handling sounds concise
- confirmed missed-lead pain is used to ask for the appointment instead of repeating fit logic
- the agent does not speak implementation labels or generic timing advice

## Evidence

Generated evidence:

- `research/experiments/generated/LIVE-DEMO-011-live-followup-stop-and-pain-close/result.json`
- `research/experiments/generated/LIVE-DEMO-011-live-followup-stop-and-pain-close/report.md`

Private browser transcript JSON files can continue to live under:

```text
data\private\live-demo-003\raw-turns\browser-transcript
```

Do not commit private transcript files from that folder.
