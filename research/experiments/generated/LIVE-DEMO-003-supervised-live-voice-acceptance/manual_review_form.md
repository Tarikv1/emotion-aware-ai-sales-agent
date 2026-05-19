# LIVE-DEMO-003 Manual Review Form

Use this file to review the live call. The JSON packet is the machine artifact; this form explains the fields in plain language.
For machine evaluation, fill the companion CSV and rerun the generator with `--manual-review-csv`.

- Checkpoint: `LIVE-DEMO-003-supervised-live-voice-acceptance`
- Demo session: `LIVE-DEMO-003-synthetic-sample`
- Campaign: `campaign-prod-005-b2b-software`
- Provider TTS used: `false`
- Browser fallback voice used: `true`
- Review CSV: `D:\Codex\active\emotion-aware-ai-sales-agent\research\experiments\generated\LIVE-DEMO-003-supervised-live-voice-acceptance\manual_review.csv`

## Field Guide

- `asr_captured_correctly`: true, false, or unclear: did the transcript match what you said?
- `agent_interrupted_or_talked_over_user`: true if the agent started while you were still speaking.
- `turn_taking_felt_natural`: 1-5: did listen/speak timing feel natural?
- `response_latency_felt_acceptable`: 1-5: did the delay feel acceptable?
- `voice_consistency`: 1-5: did the same voice/style stay consistent?
- `response_naturalness`: 1-5: did the response sound natural?
- `sales_steering`: 1-5: did the agent guide toward a useful sales next step?
- `repeated_itself`: true if it repeated the same answer or question.
- `echoed_customer_too_much`: true if it mirrored your sentence instead of advancing.
- `callback_confusion_seen`: true if workflow callbacks were confused with scheduling.
- `buyer_agency_preserved`: true if the agent respected stop/no/later boundaries.
- `notes`: short free-text note for the turn.
- `accepted_for_next_iteration`: true only if this turn is acceptable for the next iteration.

## Turn Review

### Turn 1

- You said: __agent_open__
- Agent said: Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM. Do you have a minute? I am looking for the person handling inbound demo follow-up. We help stop missed callbacks and messy handoffs. Is that worth a quick check?
- Call control: `continue-call`

Fill in the CSV row for this turn. Use 1-5 scores, true/false booleans, and short notes.

### Turn 2

- You said: hmm okay
- Agent said: Inbound demo requests need owner, callback, and handoff status. Which part slips first for your team?
- Call control: `continue-call`

Fill in the CSV row for this turn. Use 1-5 scores, true/false booleans, and short notes.

### Turn 3

- You said: I didn't understand what you asked
- Agent said: I was asking whether missed callbacks, messy handoffs, or unclear owners happen in your inbound demo flow. In plain terms, which part needs a clearer owner or callback?
- Call control: `continue-call`

Fill in the CSV row for this turn. Use 1-5 scores, true/false booleans, and short notes.

### Turn 4

- You said: callbacks are probably the problem
- Agent said: Then callback reminders are the value point: fewer inbound demo requests wait without a next step. Would a short workflow review focus only on that gap?
- Call control: `continue-call`

Fill in the CSV row for this turn. Use 1-5 scores, true/false booleans, and short notes.

### Turn 5

- You said: what do you mean by callbacks?
- Agent said: Callbacks here mean follow-up reminders after an inbound demo request, not scheduling this call. RouteSignal keeps owner and next step visible. Are missed follow-ups happening often enough to check?
- Call control: `continue-call`

Fill in the CSV row for this turn. Use 1-5 scores, true/false booleans, and short notes.

### Turn 6

- You said: tell me more
- Agent said: New trial requests need priority routing, duplicate checks, and callback visibility. Which gap should I keep this focused on?
- Call control: `continue-call`

Fill in the CSV row for this turn. Use 1-5 scores, true/false booleans, and short notes.

### Turn 7

- You said: why does that matter?
- Agent said: In plain terms, it matters only if that gap costs time today: missed callbacks, unclear owners, or lost handoffs. Which one costs time today?
- Call control: `continue-call`

Fill in the CSV row for this turn. Use 1-5 scores, true/false booleans, and short notes.

### Turn 8

- You said: what does it cost?
- Agent said: In plain terms, RouteSignal is only relevant if demo follow-up is slipping: missed callbacks, unclear owners, or handoff status. Which of those actually happens?
- Call control: `bridge-then-continue`

Fill in the CSV row for this turn. Use 1-5 scores, true/false booleans, and short notes.

### Turn 9

- You said: I am not sure it fits our workflow
- Agent said: Fit depends on a real workflow gap: missed leads, callbacks, or handoffs. If that is not happening, stop here.
- Call control: `continue-call`

Fill in the CSV row for this turn. Use 1-5 scores, true/false booleans, and short notes.

### Turn 10

- You said: no
- Agent said: No problem. Do you mean now is not a good time, or that missed callbacks and handoffs are not an issue?
- Call control: `continue-call`

Fill in the CSV row for this turn. Use 1-5 scores, true/false booleans, and short notes.

### Turn 11

- You said: what next?
- Agent said: The useful next step is a short summary of owner, next callback, and handoff status. Would a short written summary help you judge fit?
- Call control: `continue-call`

Fill in the CSV row for this turn. Use 1-5 scores, true/false booleans, and short notes.

### Turn 12

- You said: call me back later
- Agent said: No problem. What time should I note for the callback?
- Call control: `continue-call`

Fill in the CSV row for this turn. Use 1-5 scores, true/false booleans, and short notes.

### Turn 13

- You said: tomorrow at 3 works
- Agent said: Confirmed. I will record that callback time for the specialist. Goodbye.
- Call control: `schedule-and-end`

Fill in the CSV row for this turn. Use 1-5 scores, true/false booleans, and short notes.
