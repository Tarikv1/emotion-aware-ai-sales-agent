# Fulfillment Architecture Overview

## Problem

Sales agents need to handle realistic next steps: sending a mockup later, asking for an email, scheduling a callback, or recording interest. Blocking all future-follow-up language makes the agent less useful and less natural.

The real failure is narrower: the agent must not claim a completed action happened unless there is evidence that it happened.

## Architecture

Fulfillment behavior is controlled by a campaign-level `fulfillment_mode` and per-tool state. The mode decides what kind of commitment is allowed. The tool state decides whether the agent can claim an action happened.

The reusable core stays universal. Campaigns supply:

- selected fulfillment mode
- enabled or disabled tool states
- allowed manual follow-up process
- required collection fields before commitment
- forbidden completed-action claims
- approved contact path behavior

## Fulfillment Modes

- `no_fulfillment`
- `interest_capture_only`
- `manual_human_followup_allowed`
- `simulated_manual_followup_for_internal_tests`
- `tool_enabled_email`
- `tool_enabled_calendar`
- `tool_enabled_crm`
- `tool_enabled_payment`
- `live_autonomous_followup`

## Tool States

- `not_available`
- `planned_future`
- `manual_human_process`
- `configured_disabled`
- `configured_enabled`
- `tool_called_pending`
- `tool_success`
- `tool_failure`

## Atlas Setting

Atlas Web Studio uses `manual_human_followup_allowed`.

This allows Emma to say future-oriented lines such as "we can send the mockup over", "what email should we use?", "we'll be in touch", and "I can call back Tuesday" after she has enough buyer context.

It does not allow Emma to say "I just sent it", "the meeting is booked", "I updated our CRM", "payment is processed", or "the mockup is already created" unless a future enabled tool succeeds or a human operator confirms completion.
