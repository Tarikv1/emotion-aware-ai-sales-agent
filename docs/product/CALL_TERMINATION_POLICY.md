# Call Termination Policy

## Purpose

Define when the AI sales agent should continue, bridge, transfer, schedule and end, or hang up.

This policy applies across campaign types. Campaign-specific rules may be stricter, but they should not weaken these base rules.

## Call-Control Values

Every live turn should produce a `call_control` value:

- `continue-call`: keep the call open and continue normal qualification.
- `bridge-then-continue`: say a short bridge response while slower lookup or verification runs.
- `transfer-or-escalate`: route to a human or specialist workflow instead of continuing autonomous qualification.
- `end-call`: say the appropriate closing sentence, update records, and hang up.
- `schedule-and-end`: confirm the appointment or callback, update records, and end the call politely.

## Immediate End-Call Triggers

The agent should end the call after a short acknowledgment when the customer:

- says not to call again
- asks to stop the call
- explicitly refuses further conversation
- becomes angry and clearly wants the call to end
- uses abusive or threatening language that makes continuation unsafe
- is underage or clearly not legally eligible for the campaign
- says they are in an emergency or unsafe situation
- is not the intended recipient and there is no safe continuation path

Example:

```text
Customer: Stop calling me.
Agent: Understood. I will make sure this contact is marked so you are not called again. Goodbye.
call_control: end-call
next_action: suppress-contact
```

## Polite Close Then End Call

The agent should close politely and end the call when the customer:

- says they are not interested
- declines permission to continue
- says now is a bad time and does not want follow-up
- declines twice in the same call
- asks only for information and refuses callback or further discussion
- gives no useful response after the retry limit

Example:

```text
Customer: No, I am not interested.
Agent: Thanks for letting me know. I will not take more of your time. Goodbye.
call_control: end-call
next_action: close-politely
```

## Escalate Instead Of Hanging Up

The agent should not hang up immediately when the customer is still open to help but needs a human or specialist.

Use `transfer-or-escalate` when the customer:

- directly asks for a human
- asks a complex product, pricing, legal, privacy, medical, coverage, technical, or contract question
- asks for a guarantee or unsupported claim
- identifies the correct decision-maker or referral path
- is interested but needs specialist support before continuing

Example:

```text
Customer: Please have a person call me about this.
Agent: Of course. I will route this to a specialist instead of guessing. Goodbye for now.
call_control: transfer-or-escalate
next_action: escalate
```

## Schedule And End

Use `schedule-and-end` only when the appointment or callback is confirmed clearly enough for the campaign.

Requirements:

- clear date or callback window according to campaign rules
- clear customer agreement
- appointment or callback record created

If timing is vague, use `create-follow-up-task` and `end-call` instead.

Example:

```text
Customer: Wednesday at 10 works.
Agent: Confirmed. I will record Wednesday at 10 for the specialist callback. Goodbye.
call_control: schedule-and-end
next_action: confirm-scheduling
```

## Bridge Then Continue

Use `bridge-then-continue` when the agent needs slower lookup but should not leave the customer in silence.

Good fit:

- approved product detail lookup
- availability check
- campaign disclosure retrieval
- CRM lookup
- non-sensitive fact confirmation

Example:

```text
Customer: Which exact plan is this?
Agent: One moment, I want to check the approved information.
call_control: bridge-then-continue
next_action: continue
```

## Repeated Silence

If the customer is silent or the transcript is empty:

- retry once with a short check-in
- if still silent, close politely and end the call
- log the outcome as no response or unreachable

Example:

```text
Agent: Hello, are you still there?
Customer: [silence]
Agent: I will end the call for now. Goodbye.
call_control: end-call
next_action: close-politely
```

## Voicemail

If voicemail or answering machine is detected:

- do not continue qualification
- follow campaign rules for voicemail message or no-message policy
- end the call after the approved message or no-message decision

Example:

```text
Detected: voicemail
Agent: [approved voicemail message, if campaign allows it]
call_control: end-call
next_action: create-follow-up-task
```

## Policy Position In The Pipeline

The termination layer comes after state and next-action selection, but before the agent speaks.

```text
customer answer
  -> campaign rules
  -> emotion
  -> sales difficulty
  -> interest state
  -> strategy
  -> next action
  -> call-control / termination policy
  -> response
  -> continue, bridge, transfer, schedule-and-end, or hang up
```

## Product Rule

The agent should never keep a customer on the phone just because it can generate another question.

If the customer is done, unsafe to continue, ineligible, not interested, or has requested suppression, the correct sales behavior is to close cleanly and end the call.
