# Tool State Machine

## States

- `not_available`: the tool does not exist for this campaign.
- `planned_future`: the tool is modeled but not enabled.
- `manual_human_process`: a human operator can perform the follow-up outside the agent.
- `configured_disabled`: the tool exists in configuration but is disabled.
- `configured_enabled`: the tool is available for the agent to call under policy.
- `tool_called_pending`: the tool call has been started and no success or failure result is available yet.
- `tool_success`: the tool completed successfully and returned success.
- `tool_failure`: the tool failed, timed out, or returned an error.

## Rules

Future commitments are allowed in manual_human_process.

Completed-action claims require tool_success or confirmed human process.

In current Atlas testing, email, calendar, CRM, and payment tools are `planned_future`, so completed-action claims are forbidden.

Human follow-up commitments are allowed because Atlas mode is `manual_human_followup_allowed`.

## Transitions

| From | To | Meaning |
| --- | --- | --- |
| `not_available` | `planned_future` | A tool category is recognized as future architecture. |
| `planned_future` | `configured_disabled` | Tool configuration exists but remains off. |
| `configured_disabled` | `configured_enabled` | A reviewed operator enables the tool. |
| `configured_enabled` | `tool_called_pending` | Agent calls the enabled tool. |
| `tool_called_pending` | `tool_success` | Tool returns success. |
| `tool_called_pending` | `tool_failure` | Tool returns failure or times out. |
| `manual_human_process` | `manual_human_process` | Agent may commit to human follow-up, not claim completion. |

## Claim Mapping

| Claim type | Required state |
| --- | --- |
| "We can send it" | `manual_human_process` or an enabled future tool policy |
| "We'll be in touch" | `manual_human_process` or an enabled future tool policy |
| "What email should we use?" | `manual_human_process` or email-capable mode |
| "I can call back Tuesday" | `manual_human_process` plus enough buyer details |
| "I sent it" | email `tool_success` or confirmed human process |
| "The meeting is booked" | calendar `tool_success` or confirmed human process |
| "I updated the CRM" | CRM `tool_success` |
| "Payment is processed" | payment `tool_success` plus explicit buyer consent |

## Failure Handling

If a tool is pending, failed, disabled, planned, or unavailable, the agent must not claim completion. It can say a human can follow up only when the selected fulfillment mode allows manual follow-up.
