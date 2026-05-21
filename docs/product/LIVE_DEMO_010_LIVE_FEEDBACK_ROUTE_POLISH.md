# LIVE-DEMO-010 Live Feedback Route Polish

`LIVE-DEMO-010-live-feedback-route-polish` is a narrow follow-up to Tarik's supervised `LIVE-DEMO-009` ElevenLabs listening feedback.

It does not open `PROD-102`, claim production readiness, enable payment collection, create a provider-hosted durable agent, use voice cloning, add provider ASR, make LLM calls required for live response, or let an LLM write final spoken responses.

## Scope

This checkpoint fixes four live-demo defects observed in the local browser transcript:

- after the opener asked `Do you have a minute?`, the buyer said `no I don't`, but the agent continued qualification
- a concrete missed-lead workflow problem was answered with another fit-check question instead of moving toward the appointment-setting next step
- internal/runtime-sounding instruction phrases reached customer speech
- a spreadsheet-verb phrase created an avoidable TTS pronunciation ambiguity

The fix stays inside deterministic live-demo route polish. It does not install or wire a local LLM. The small local-LLM idea remains a separate evaluation candidate after these deterministic failures are closed.

## Behavior

If the buyer refuses time after the opener, the agent treats it as a timing refusal and asks for callback timing instead of continuing qualification:

```text
Of course. What time should I note for the callback?
```

If the buyer describes concrete missed-lead pain after the manual-tracking path, the agent moves to the current MVP close:

```text
Then the next step is a short workflow review with someone from Northstar. They would check owner routing against your actual follow-up flow. What time works for a quick call?
```

If the buyer keeps confirming the pain after the appointment ask but still gives no usable time, the agent stays on the appointment-time request instead of drifting to generic timing advice.

The customer-facing response bank avoids internal instruction phrases and uses `sit in a spreadsheet` for the spreadsheet workflow description.

## Commands

Validate the checkpoint without live microphone, provider ASR, provider TTS, provider LLM calls, or local LLM calls:

```powershell
python scripts\validate_live_demo_010_live_feedback_route_polish.py
```

Run it with the current LIVE-DEMO regression stack before committing:

```powershell
python scripts\validate_live_demo_001_agent_voice_call.py
python scripts\validate_live_demo_008_prosody_review_scope_clarity.py
python scripts\validate_live_demo_009_appointment_lead_close.py
python scripts\validate_live_demo_010_live_feedback_route_polish.py
```

## Acceptance

Synthetic gate:

- provider calls made: `false`
- `no I don't` after the opener routes to callback timing, not qualification
- observed missed-lead pain moves toward a Northstar workflow-review appointment
- non-time confirmation after an appointment ask keeps asking for a usable time
- internal runtime phrases are blocked from customer speech
- the ambiguous spreadsheet-verb TTS phrase is avoided
- no payment, contract, or production close language

Human live check:

- a buyer's time refusal sounds heard and respected
- concrete workflow pain moves the call forward instead of repeating qualification
- the agent does not speak implementation labels or runtime logic
- pronunciation no longer trips over the spreadsheet sentence

## Evidence

Generated evidence:

- `research/experiments/generated/LIVE-DEMO-010-live-feedback-route-polish/result.json`
- `research/experiments/generated/LIVE-DEMO-010-live-feedback-route-polish/report.md`

Private browser transcript JSON files can continue to live under:

```text
data\private\live-demo-003\raw-turns\browser-transcript
```

Do not commit private transcript files from that folder.
