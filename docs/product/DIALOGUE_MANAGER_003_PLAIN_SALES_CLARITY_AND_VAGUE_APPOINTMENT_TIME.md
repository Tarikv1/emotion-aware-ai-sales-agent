# DIALOGUE-MANAGER-003 Plain Sales Clarity And Vague Appointment Time

`DIALOGUE-MANAGER-003-plain-sales-clarity-and-vague-appointment-time` is the narrow follow-up after `DIALOGUE-MANAGER-002-pragmatic-dialogue-repair`.

It does not open `PROD-102`, claim production readiness, enable payment collection, create a provider-hosted durable agent, use voice cloning, add provider ASR, install or wire a local LLM, make LLM calls required for live response, or let an LLM write final spoken responses.

## Problem

The manager/pragmatics layer made small buyer moves explicit, but the live listening pass still exposed three customer-facing failures:

- call-purpose recovery explained the workflow in internal terms instead of plain sales-call language
- missed-lead pain could drift into another diagnostic or explanation instead of moving toward a workflow-review appointment
- vague appointment availability such as `sometime next week` could be treated as a non-decision and end the call

These are not evidence for a broad runtime rewrite. They are evidence that the existing manager needs tighter response templates, missed-lead recognition, and appointment-time clarification ownership.

## Scope

This checkpoint keeps the existing dialogue manager and pragmatic classifier.

The slice is intentionally narrow:

- make call-purpose and product-purpose answers explain RouteSignal as assigning, reminding, and following up on demo leads
- recognize missed-lead phrases such as `leads missing` as real workflow pain
- keep repeated affirmative replies after an appointment ask on the appointment-time request
- acknowledge when the buyer says they already stated the problem
- treat vague appointment timing as `appointment_time_clarification_needed`
- remove customer-facing internal fragments such as `selling point`, `owner lookup`, `handoff status`, `fictional profile`, `check fit only`, and `if not stop`

It does not replace deterministic routing with a local LLM.

## Behavior

Covered live failure shapes:

- `what is this call about` after the opener gets a plain RouteSignal explanation
- `we get some leads missing time to time` selects a missed-lead gap and names the thing being sold
- `I already told you` acknowledges the repeated buyer context and asks for a workflow-review time
- `yeah sure` after appointment context keeps asking for a usable time
- `sometime in the next week` keeps the call open and asks for a concrete day/time

## Commands

Validate the checkpoint without live microphone, provider ASR, provider TTS, provider LLM calls, or local LLM calls:

```powershell
python scripts\validate_dialogue_manager_003_plain_sales_clarity_and_vague_appointment_time.py
```

Run it with the focused live-demo regression stack before committing:

```powershell
python scripts\validate_dialogue_manager_003_plain_sales_clarity_and_vague_appointment_time.py
python scripts\validate_dialogue_manager_002_pragmatic_dialogue_repair.py
python scripts\validate_dialogue_manager_001_root_repair.py
python scripts\validate_live_demo_009_appointment_lead_close.py
python scripts\validate_live_demo_011_live_followup_stop_and_pain_close.py
python scripts\validate_live_demo_013_reasoner_route_guard.py
python scripts\validate_runtime_manifest.py
```

## Evidence

Generated evidence:

- `research/experiments/generated/DIALOGUE-MANAGER-003-plain-sales-clarity-and-vague-appointment-time/result.json`
- `research/experiments/generated/DIALOGUE-MANAGER-003-plain-sales-clarity-and-vague-appointment-time/report.md`

Private browser transcript JSON files can continue to live under:

```text
data\private\live-demo-003\raw-turns\browser-transcript
```

Do not commit private transcript files from that folder.
