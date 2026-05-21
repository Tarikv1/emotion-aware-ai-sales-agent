# LIVE-DEMO-012 Soft Stop And Context Recovery

`LIVE-DEMO-012-soft-stop-and-context-recovery` is a narrow follow-up to Tarik's supervised `LIVE-DEMO-011` ElevenLabs listening feedback.

It does not open `PROD-102`, claim production readiness, enable payment collection, create a provider-hosted durable agent, use voice cloning, add provider ASR, install a local LLM, make LLM calls required for live response, or let an LLM write final spoken responses.

## Scope

This checkpoint fixes the live failure where callback refusal and call-purpose recovery stayed trapped in stale timing context:

- after `no I don't`, the buyer said a soft refusal like `maybe just don't`; the agent said it could leave the call there but `call_control` stayed `continue-call`
- after that missed terminal state, call-purpose questions were answered with generic timing text
- ASR-shaped purpose wording such as `what is this called about` was not recognized as a call-purpose question
- after purpose recovery, an `owners` answer still fell back to timing instead of workflow-gap handling

## Behavior

Soft callback refusal after a callback-time request now ends the call:

```text
Understood. I will stop here. Goodbye.
```

Call-purpose questions override stale timing context and move the active focus back to qualification:

```text
I am calling about inbound demo follow-up: owners, callback reminders, and handoff status. Which of those creates the most missed follow-up?
```

If the buyer then answers with an owner/routing gap, the agent stays on the sales workflow track instead of returning to timing:

```text
Then priority routing is the value point: each inbound request gets a clear owner faster. I would keep the workflow review focused on that one gap. Would a short workflow review be useful for that gap?
```

## Commands

Validate the checkpoint without live microphone, provider ASR, provider TTS, provider LLM calls, or local LLM calls:

```powershell
python scripts\validate_live_demo_012_soft_stop_and_context_recovery.py
```

Run it with the current LIVE-DEMO regression stack before committing:

```powershell
python scripts\validate_live_demo_001_agent_voice_call.py
python scripts\validate_live_demo_008_prosody_review_scope_clarity.py
python scripts\validate_live_demo_009_appointment_lead_close.py
python scripts\validate_live_demo_010_live_feedback_route_polish.py
python scripts\validate_live_demo_011_live_followup_stop_and_pain_close.py
python scripts\validate_live_demo_012_soft_stop_and_context_recovery.py
```

## Acceptance

Synthetic gate:

- provider calls made: `false`
- soft callback refusal after callback timing ends the call
- call-purpose questions override stale timing context
- purpose recovery moves focus back to qualification
- owner/routing answers after purpose recovery stay on the sales workflow track
- generic timing fallback text is not used for purpose questions

Human live check:

- `maybe just don't` after callback timing stops the call instead of restarting listening
- `what is this call about` gets a plain purpose answer
- `owners` after that purpose answer stays on owner-routing workflow logic
- the agent does not speak generic timing advice when the buyer is asking about purpose

## Evidence

Generated evidence:

- `research/experiments/generated/LIVE-DEMO-012-soft-stop-and-context-recovery/result.json`
- `research/experiments/generated/LIVE-DEMO-012-soft-stop-and-context-recovery/report.md`

Private browser transcript JSON files can continue to live under:

```text
data\private\live-demo-003\raw-turns\browser-transcript
```

Do not commit private transcript files from that folder.
