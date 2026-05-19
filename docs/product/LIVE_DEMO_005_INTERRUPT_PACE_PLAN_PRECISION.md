# LIVE-DEMO-005 Interrupt, Pace, And Plan Precision

`LIVE-DEMO-005-interrupt-pace-plan-precision` is a narrow follow-up to Tarik's supervised `LIVE-DEMO-004` listening feedback.

It does not open `PROD-102`, claim production readiness, add provider ASR, enable payment collection, create a provider-hosted durable agent, use voice cloning, make LLM calls required for live response, or let an LLM write final spoken responses.

## Goal

Improve the current live demo without broadening product scope:

- add a manual interrupt control for the agent's current spoken output
- make the live-demo voice about five percent faster
- preserve the no-spoken-barge-in browser ASR boundary
- answer Starter-vs-Growth plan-boundary questions directly
- record plan-boundary answers in compact conversation memory

## Runtime Behavior

Manual interruption is local browser behavior. It stops the current audio or browser fallback speech, clears pending submit timers, and restarts listening only after local microphone consent. It is not true voice barge-in.

True spoken interruption remains out of scope because browser SpeechRecognition cannot reliably separate Tarik's speech from the agent's own audio. A real streaming ASR/VAD checkpoint is still needed before production-style barge-in claims.

Plan-boundary questions now route before generic gap selection. If the buyer asks whether Starter lacks reminders or handoff review, the agent should directly confirm the boundary before steering to the next useful sales step.

## Commands

Validate the checkpoint without live microphone or provider calls:

```powershell
python scripts\validate_live_demo_005_interrupt_pace_plan_precision.py
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
- no claim that browser ASR is true production VAD
- manual interrupt stops current spoken output and returns to listening
- ElevenLabs stable live-demo speed is about five percent faster than the prior setting
- browser fallback speech rate is about five percent faster than the prior setting
- explicit price questions still get the compact price answer
- Starter-vs-Growth boundary questions answer directly
- repeated plan-boundary questions avoid exact duplicate final responses
- compact memory records `plan_boundary`

Human live check:

- interruption via the `Interrupt Agent` button or `Escape` feels usable
- the faster pace is not rushed
- the answer to "Starter does not cover reminders and handoff review?" sounds direct
- repeated plan or pricing discussion does not loop around the same sentence

## Evidence

Generated evidence:

- `research/experiments/generated/LIVE-DEMO-005-interrupt-pace-plan-precision/result.json`
- `research/experiments/generated/LIVE-DEMO-005-interrupt-pace-plan-precision/report.md`

This checkpoint is still supervised demo hardening, not production voice acceptance.
