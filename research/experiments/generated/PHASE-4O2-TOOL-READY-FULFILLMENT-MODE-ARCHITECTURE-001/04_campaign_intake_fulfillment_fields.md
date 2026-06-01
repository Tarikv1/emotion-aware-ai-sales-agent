# Campaign Intake Fulfillment Fields

Add these fields to campaign intake or adapter material when fulfillment behavior matters.

## Required Fields

- `fulfillment_mode`: one of the universal fulfillment modes.
- `manual_followup_allowed`: whether a campaign owner or operator can manually follow up after the call.
- `manual_followup_owner`: the role responsible for manual follow-up.
- `required_details_before_followup_commitment`: minimum details the agent must collect before promising manual follow-up.
- `approved_followup_language`: future-oriented phrases the agent may use.
- `forbidden_completed_action_claims`: completed-action claims that require evidence.
- `approved_contact_paths`: company contact paths the agent may disclose.
- `invented_contact_path_policy`: what to say when no approved contact path exists.
- `approved_timing_language`: allowed timing phrases.
- `unapproved_exact_delivery_date_policy`: rule for refusing exact dates that are not approved.
- `email_tool_state`: email state from the tool state machine.
- `calendar_tool_state`: calendar state from the tool state machine.
- `crm_tool_state`: CRM state from the tool state machine.
- `payment_tool_state`: payment state from the tool state machine.
- `payment_consent_policy`: explicit consent required before any payment action.
- `completed_action_claim_policy`: rule requiring tool success or confirmed human process.

## Atlas Values For This Phase

- `fulfillment_mode`: `manual_human_followup_allowed`
- `manual_followup_allowed`: true
- `manual_followup_owner`: Atlas Web Studio human operator
- `email_tool_state`: `planned_future`
- `calendar_tool_state`: `planned_future`
- `crm_tool_state`: `planned_future`
- `payment_tool_state`: `planned_future`
- `approved_contact_paths`: none
- `invented_contact_path_policy`: do not invent Atlas email, phone, URL, or address
- `approved_timing_language`: "in a few business days", "I can call back Tuesday" when buyer agrees

## Minimum Details Before Atlas Follow-Up

- business name
- business type or vertical
- location or service area if relevant
- main customer action desired
- reviewer or contact method
- email or callback preference if buyer provides it

If information is missing, Emma should ask one concise question instead of making a premature commitment.
