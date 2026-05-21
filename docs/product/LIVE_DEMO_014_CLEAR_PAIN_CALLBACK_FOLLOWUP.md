# LIVE-DEMO-014 Clear Pain Callback Follow-Up

`LIVE-DEMO-014-clear-pain-callback-followup` is a narrow follow-up to the supervised ElevenLabs pass after `DIALOGUE-MANAGER-003`.

It does not open `PROD-102`, install or wire a local LLM, enable provider ASR, create a provider-hosted durable agent, use voice cloning, let an LLM write final spoken responses, collect payment, sign contracts, promote production runtime, or broaden appointment-setting into autonomous sale closure.

## Scope

This checkpoint fixes the latest live-demo dialogue failures without broad-rewriting the runtime:

- `it's all clear` after a diagnostic question was ignored and replaced with another scripted diagnostic
- confirmed missed callbacks still triggered a negative `if clean` disclaimer and an unexplained `Growth` plan name
- `what do you mean Growth` did not acknowledge the unclear term
- `I have to think about it` after the workflow-review ask was treated like a stop
- `yeah let's do that` after a callback-later offer did not ask for a usable callback time

## Behavior

Clear/no-pain replies are now acknowledged before the agent probes for any remaining relevant gap:

```text
Got it. If the follow-up flow is already clear, I should not push a review. Before I let you go, do missed callbacks, manual tracking, or handoffs ever create a problem, or is this not relevant for you?
```

Confirmed missed callbacks now move toward the Northstar workflow review without an unexplained plan name:

```text
That sounds like the gap. RouteSignal is meant to help demo leads get assigned, reminded, and followed up. A short workflow review with someone from Northstar would check missed callback reminders against your actual follow-up flow. Would a short workflow review be useful for this gap?
```

Unexplained `Growth` references now get a plain correction:

```text
Sorry, I should have explained that. Growth is the RouteSignal setup for teams that need follow-up reminders and handoff review around inbound demo requests. The practical question is whether missed callbacks are worth a short workflow review.
```

Appointment hesitation now keeps follow-up open:

```text
No problem. You do not have to accept the workflow review now. I can keep it to a short summary and call back later. What time should I call back?
```

Affirming the callback-later option without a time now asks for a time instead of ending or drifting:

```text
Sure. What time should I call back?
```

## Architecture Note

The fix stays in the existing manager/pragmatics/policy stack:

- `runtime/core/dialogue_pragmatics.py` now catches Growth term questions, appointment hesitation, and callback-later affirmation before generic focus progression.
- `runtime/core/live_voice_session_policy.py` now has explicit clear/no-pain acknowledgement, think-about-it callback wording, callback-later time request wording, broader pain confirmation for missed callbacks/manual tracking issues, and a narrower stability-guard exception for true workflow-review appointment asks.

The change keeps deterministic final speech. It adds no local or provider LLM call.

## Commands

Validate the checkpoint without live microphone, provider ASR, provider TTS, provider LLM calls, or local LLM calls:

```powershell
python scripts\validate_live_demo_014_clear_pain_callback_followup.py
```

Run it with the current LIVE-DEMO/dialogue regression stack before committing:

```powershell
python scripts\validate_live_demo_009_appointment_lead_close.py
python scripts\validate_live_demo_010_live_feedback_route_polish.py
python scripts\validate_live_demo_011_live_followup_stop_and_pain_close.py
python scripts\validate_live_demo_012_soft_stop_and_context_recovery.py
python scripts\validate_live_demo_013_reasoner_route_guard.py
python scripts\validate_dialogue_manager_001_root_repair.py
python scripts\validate_dialogue_manager_002_pragmatic_dialogue_repair.py
python scripts\validate_dialogue_manager_003_plain_sales_clarity_and_vague_appointment_time.py
python scripts\validate_live_demo_014_clear_pain_callback_followup.py
```

## Acceptance

Synthetic gate:

- provider calls made: `false`
- local LLM calls made: `false`
- `it's all clear` is acknowledged and does not rotate into a different scripted diagnostic
- stated missed callbacks move toward a Northstar workflow-review ask without callback-scheduling ambiguity
- customer-facing speech avoids unexplained `Growth` in the missed-callback close
- `what do you mean Growth` receives a plain correction
- `think about it` keeps callback follow-up open
- `yeah let's do that` after callback-later asks for a usable callback time

Human live check:

- buyer input is acknowledged before the agent moves forward
- explicit pain is used to set the appointment, not to reopen whether a pain exists
- hesitation produces a low-pressure callback/summary path, not a premature stop
- callback-later agreement does not end until a usable time is captured

## Evidence

Generated evidence:

- `research/experiments/generated/LIVE-DEMO-014-clear-pain-callback-followup/result.json`
- `research/experiments/generated/LIVE-DEMO-014-clear-pain-callback-followup/report.md`

Private browser transcript JSON files can continue to live under:

```text
data\private\live-demo-003\raw-turns\browser-transcript
```

Do not commit private transcript files from that folder.
