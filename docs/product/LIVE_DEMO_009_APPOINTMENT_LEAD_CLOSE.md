# LIVE-DEMO-009 Appointment Lead Close

`LIVE-DEMO-009-appointment-lead-close` is a narrow follow-up to Tarik's supervised `LIVE-DEMO-008` listening feedback.

It does not open `PROD-102`, claim production readiness, enable payment collection, create a provider-hosted durable agent, use voice cloning, add provider ASR, make LLM calls required for live response, or let an LLM write final spoken responses.

## Scope

This checkpoint fixes two live-demo defects:

- the opening asked for time permission and then asked a second qualification question before the buyer answered
- after a real workflow gap and buyer agreement, the runtime kept asking whether a short workflow review was useful instead of moving to an appointment-setting next step

The MVP close for the live demo is appointment-setting, not payment or autonomous contract closure.

## Behavior

The opener now asks one permission question and waits:

```text
Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. I am looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. Do you have a minute?
```

After permission, the agent can continue qualification.

When the buyer has selected or confirmed a real gap and then agrees that the review would help, the runtime asks for an appointment with a Northstar person instead of asking another usefulness question:

```text
Then the next step is a short workflow review with someone from Northstar. They would check missed callback reminders against your actual follow-up flow. What time works for a quick call?
```

If the buyer gives a time after that appointment ask, the local demo confirms the workflow-review time and ends the call. Explicit callback scheduling still uses the existing callback route.

## Commands

Validate the checkpoint without live microphone, provider ASR, provider TTS, or provider LLM calls:

```powershell
python scripts\validate_live_demo_009_appointment_lead_close.py
```

Run it with the existing LIVE-DEMO regression stack before committing:

```powershell
python scripts\validate_live_demo_001_agent_voice_call.py
python scripts\validate_live_demo_008_prosody_review_scope_clarity.py
python scripts\validate_live_demo_009_appointment_lead_close.py
```

## Acceptance

Synthetic gate:

- provider calls made: `false`
- opener asks exactly one permission question
- early permission `yes` starts qualification, not appointment close
- confirmed workflow pain moves to an appointment ask
- repeated `yes` after the appointment ask keeps asking for a usable time instead of drifting back to generic timing advice
- explicit `call me back later` still uses the callback scheduling route
- a time after appointment context confirms workflow-review scheduling and ends the call
- no payment, contract, or production close language

Human live check:

- the opening no longer feels like two questions at once
- after buyer agreement, the agent tries to set a short human workflow-review appointment
- the appointment ask feels like the sales next step, not a hard close or payment attempt

## Evidence

Generated evidence:

- `research/experiments/generated/LIVE-DEMO-009-appointment-lead-close/result.json`
- `research/experiments/generated/LIVE-DEMO-009-appointment-lead-close/report.md`

Private browser transcript JSON files can continue to live under:

```text
data\private\live-demo-003\raw-turns\browser-transcript
```

Do not commit private transcript files from that folder.
