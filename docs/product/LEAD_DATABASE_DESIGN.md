# Lead Database Design

## Purpose

Define the first product database shape for storing leads, qualification answers, call outcomes, appointments, and escalation records.

The goal is to support an autonomous qualification agent that remembers the current customer context during a call and saves useful structured outcomes after the call.

This is a product design document, not an instruction to store real customer data in the repository.

## Design Principles

- keep the live call state accumulated across turns
- separate lead identity from call-specific observations
- store qualification answers as structured records, not only free text
- record explicit consent, do-not-call, and contact-status information
- never mark an appointment as scheduled without a confirmed time
- keep escalation reasons visible and auditable
- avoid storing unnecessary personal data
- keep raw transcripts optional and controlled

## Core Entities

```text
Lead
  -> CallSession
      -> QualificationAnswer
      -> TurnDecision
      -> CallOutcome
      -> Appointment
      -> Escalation
```

## Lead

Stores stable information about a person or company contact.

```text
Lead
  lead_id
  full_name
  phone_number
  email
  company_name
  role_title
  source
  region
  language
  contact_status
  consent_status
  do_not_call
  do_not_call_reason
  preferred_contact_time
  owner_user_id
  created_at
  updated_at
```

Suggested `contact_status` values:

- `new`
- `called`
- `qualified`
- `not-interested`
- `needs-human`
- `appointment-scheduled`
- `do-not-call`

Suggested `consent_status` values:

- `unknown`
- `allowed`
- `limited`
- `revoked`

Notes:

- `do_not_call` must override normal outreach.
- `phone_number` should be normalized before storage.
- If the lead asks not to be called again, record it immediately.

## CallSession

Stores one call attempt or simulated call.

```text
CallSession
  call_id
  lead_id
  channel
  started_at
  ended_at
  call_status
  current_stage
  current_interest_state
  current_emotion_label
  current_strategy
  confidence
  transcript_storage_mode
  transcript_text
  call_summary
  created_by
  created_at
```

Suggested `channel` values:

- `simulation`
- `phone`
- `manual-entry`
- `imported-transcript`

Suggested `call_status` values:

- `in-progress`
- `completed`
- `escalated`
- `needs-follow-up`
- `ready-for-scheduling`
- `failed`

Important:

- During a live call, `CallSession` is the accumulated state object.
- The agent should use prior turns and current fields before deciding the next action.
- `transcript_text` should be optional and controlled because it may contain personal data.

## QualificationAnswer

Stores customer answers to the qualification flow.

```text
QualificationAnswer
  answer_id
  call_id
  lead_id
  stage
  question_text
  answer_text
  normalized_answer
  detected_emotion
  interest_state_after_answer
  selected_strategy
  confidence
  created_at
```

Suggested `stage` values:

- `opening-permission`
- `relevance-check`
- `pain-point-check`
- `timing-openness-check`
- `scheduling`
- `close-or-escalate`

Notes:

- This table is the main bridge between the simulation cases and the real product.
- For analytics, `normalized_answer` can capture simple structured facts such as `handles_lead_followup=true` or `pain_point=slow_response`.

## TurnDecision

Stores the agent's decision at each turn.

```text
TurnDecision
  decision_id
  call_id
  lead_id
  turn_index
  stage
  detected_emotion
  interest_state
  selected_strategy
  next_action
  agent_response
  confidence
  rationale
  guardrail_flags
  created_at
```

Suggested `next_action` values:

- `continue`
- `ask-follow-up`
- `offer-scheduling`
- `confirm-scheduling`
- `close-politely`
- `escalate`
- `suppress-contact`
- `create-follow-up-task`

Notes:

- This mirrors the per-turn output in `SIMULATION_CONTRACT.md`.
- Keeping these records makes agent behavior auditable.
- Future sales-expert feedback can point to a specific `decision_id`.

## CallOutcome

Stores the final outcome for a call.

```text
CallOutcome
  outcome_id
  call_id
  lead_id
  call_status
  interest_state
  selected_strategy
  appointment_scheduled
  appointment_time
  escalation_reason
  call_summary
  next_action
  created_at
```

This should match the final output contract used in the product simulation.

Rules:

- `appointment_scheduled=true` requires a non-empty `appointment_time`.
- `interest_state=do-not-call` should update `Lead.do_not_call=true`.
- `interest_state=needs-human` should create or link to an `Escalation`.
- `call_status=escalated` should include an `escalation_reason`.

## Appointment

Stores confirmed or pending human follow-up calls.

```text
Appointment
  appointment_id
  lead_id
  call_id
  scheduled_time
  timezone
  assigned_sales_agent_id
  appointment_status
  confirmation_text
  calendar_event_id
  created_at
  updated_at
```

Suggested `appointment_status` values:

- `pending`
- `confirmed`
- `rescheduled`
- `completed`
- `cancelled`
- `no-show`

Rules:

- Create a confirmed appointment only after the lead chooses or accepts a clear time.
- Vague windows such as "next week" should create a follow-up task, not a confirmed appointment.
- Calendar integration can be added later through `calendar_event_id`.

## Escalation

Stores cases that need human attention.

```text
Escalation
  escalation_id
  lead_id
  call_id
  escalation_reason
  severity
  assigned_to
  status
  notes
  created_at
  resolved_at
```

Suggested `escalation_reason` values:

- `lead requested human contact`
- `complex integration question`
- `pricing or contract question`
- `privacy or compliance-sensitive topic`
- `angry or risky lead`
- `low confidence`
- `scheduling failure`
- `wrong contact with referral path`

Suggested `severity` values:

- `low`
- `medium`
- `high`

## SalesExpertFeedback Link

The existing feedback concept can attach to a call, turn, or generated response.

```text
SalesExpertFeedbackRecord
  feedback_id
  call_id
  decision_id
  outcome_id
  reviewer_id
  rating_fields...
  correction_fields...
  created_at
```

This allows expert review to improve prompts, rules, examples, and future training data.

## Minimal MVP Schema

For the first implementation, start with only:

```text
Lead
CallSession
QualificationAnswer
TurnDecision
CallOutcome
Appointment
Escalation
```

Do not add a complex CRM model yet.

## Example Happy-Path Record Flow

```text
Lead created
  -> CallSession started
  -> QualificationAnswer saved for relevance check
  -> TurnDecision saved with inquiry strategy
  -> QualificationAnswer saved for pain-point check
  -> TurnDecision saved with inquiry or evidence strategy
  -> QualificationAnswer saved for openness check
  -> TurnDecision saved with direct ask strategy
  -> Appointment created after confirmed time
  -> CallOutcome saved as interested and scheduled
  -> Lead contact_status updated to appointment-scheduled
```

## Example Do-Not-Call Flow

```text
Lead receives call
  -> lead says do not call again
  -> TurnDecision saved with suppress-contact
  -> CallOutcome saved with interest_state=do-not-call
  -> Lead.do_not_call set to true
  -> Lead.contact_status set to do-not-call
```

## Privacy And Data Boundaries

Do not commit real leads, phone numbers, transcripts, or call records to the repository.

For local development:

- use synthetic or anonymized records
- keep real customer data in a restricted database or local secure store
- separate public thesis artifacts from private product records
- document when private data influences product behavior

For production:

- define retention rules before launch
- restrict access by role
- log who viewed or changed customer records
- support deletion or suppression workflows
- avoid storing raw transcripts unless there is a clear product and legal reason

## Relationship To Simulation

The simulation should eventually write candidate outputs into the same shape:

- per-turn output -> `TurnDecision`
- lead answer -> `QualificationAnswer`
- final output -> `CallOutcome`
- confirmed schedule -> `Appointment`
- human fallback -> `Escalation`

This keeps the product path coherent: the simulation tests the same structures the product will later persist.

## Simulation Export

The simulation runner can export database-shaped synthetic records:

```text
python scripts/run_product_simulation.py \
  --cases research/experiments/cases/prod-001-qualification-simulation.json \
  --out research/experiments/generated/PROD-001-evaluation-packet.md \
  --export-records research/experiments/generated/PROD-001-db-records.json
```

The export contains:

- `leads`
- `call_sessions`
- `qualification_answers`
- `turn_decisions`
- `call_outcomes`
- `appointments`
- `escalations`

These records are synthetic reference records, not real customer records.

## Next Implementation Step

After the synthetic export is stable, choose the first persistence layer for the product prototype.

Likely first options:

- SQLite for a local prototype
- Postgres for a production-like backend
- JSON files only for short-term simulation debugging

Current choice:

- SQLite is the first local prototype layer.
- See `SQLITE_PROTOTYPE.md`.
