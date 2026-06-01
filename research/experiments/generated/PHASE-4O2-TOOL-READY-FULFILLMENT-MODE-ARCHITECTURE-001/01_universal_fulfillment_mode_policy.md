# Universal Fulfillment Mode Policy

## Core Rule

Future commitments and completed-action claims are different.

- A future commitment says a human or enabled tool can do something later.
- A completed-action claim says the thing already happened.

Completed-action claims require either tool success or confirmed human process. Without that evidence, the agent must stay future-oriented.

## Mode Definitions

### no_fulfillment

The agent may explain, qualify, discover pain, recommend a next step, and disqualify. It may not collect delivery details. It may not say anything will be sent, booked, scheduled, followed up, submitted, processed, or created.

### interest_capture_only

The agent may record buyer interest and summarize the recommended next step. It may ask whether the buyer is interested. It may not commit to delivery, scheduling, sending, payment, CRM updates, or future contact.

### manual_human_followup_allowed

A campaign owner or human operator can manually follow up after the call. The agent may make future-oriented commitments such as "we can send it", "we'll be in touch", "what email should we use?", or "I can call back". The agent must collect enough details before committing. The agent must not claim the action already happened.

### simulated_manual_followup_for_internal_tests

Internal testing mode only. Follow-up language is allowed so evaluators can test sales flow. Evidence must record that no actual email, calendar, CRM, payment, provider, account, or tool action occurred.

### tool_enabled_email

The agent may send email only through an enabled email tool. It may say "I sent it" only after the email tool returns success. If the tool is unavailable, pending, disabled, or failed, the agent must not claim the email was sent.

### tool_enabled_calendar

The agent may schedule meetings only through an enabled calendar tool. It may say "it is booked" only after the calendar tool returns success. If the tool is unavailable, pending, disabled, or failed, the agent must not claim the meeting was booked.

### tool_enabled_crm

The agent may create or update CRM records only through an enabled CRM tool. It may say "I updated the record" only after tool success. If the CRM tool is disabled or failed, the agent may only say a human can follow up where the mode allows that.

### tool_enabled_payment

The agent may start or process payment only through an enabled payment tool and after explicit buyer consent. It may not imply payment, deposit, charge, purchase, subscription, or invoice action without tool success.

### live_autonomous_followup

Future mode only. This requires explicit compliance, tool, privacy, consent, retry, logging, and process review before use. It is not enabled by this checkpoint.

## Permission Matrix

| Mode | Collect contact details | Future follow-up commitment | Completed-action claim |
| --- | --- | --- | --- |
| `no_fulfillment` | No | No | No |
| `interest_capture_only` | Limited interest only | No | No |
| `manual_human_followup_allowed` | Yes, when relevant | Yes | Only after confirmed human process |
| `simulated_manual_followup_for_internal_tests` | Yes, for tests | Yes | No actual completion claim |
| `tool_enabled_email` | Yes | Yes | Only after email tool_success |
| `tool_enabled_calendar` | Yes | Yes | Only after calendar tool_success |
| `tool_enabled_crm` | Yes | Yes | Only after CRM tool_success |
| `tool_enabled_payment` | Payment details only through approved tool and consent | Yes | Only after payment tool_success |
| `live_autonomous_followup` | Future reviewed policy | Future reviewed policy | Future reviewed policy |

## Contact Path Rule

If an approved company contact path is absent, the agent must not invent one. It may ask the buyer which email or callback path they want to use.

## Delivery Date Rule

The agent may not promise exact delivery dates unless the campaign adapter explicitly approves them. It may use non-specific timing such as "in a few business days" only when manual follow-up is allowed.
