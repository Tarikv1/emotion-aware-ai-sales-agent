# GENERIC-CAMPAIGN-LONG-CONVERSATION-STRESS-001

Status: pass
Failure count: 0

## Behavior Before Patch
{
  "clusters": [
    "A deep insurance next-step turn after send-info used the RouteSignal/Northstar appointment close fallback.",
    "A B2B SaaS password/support question after right-person capture reopened diagnostics instead of keeping the contact boundary.",
    "A retail time confirmation after a refund guarantee caution was ignored because the previous question was not typed as appointment_time.",
    "The first validator draft treated repeated terminal stop text as a loop even though it was justified terminal persistence."
  ],
  "red_run_failure_count": 6
}

## Scenarios Covered
- A insurance clear one gap, confirm another, send info, capture email
- B telecom possible pain, clarification, confirmed pain, callback time
- C B2B SaaS right-person handoff, department, contact capture
- D home services regulated caution, refusal, terminal stop
- E membership all gaps clear, final save, polite close
- F retail pain, price question, risky guarantee, time capture
- G automotive fallback loop resistance
- H RouteSignal live-demo preservation

## Failures Found
- None.

## Patches Made
- Made the shared appointment close response campaign-aware when a non-RouteSignal campaign is passed.
- Passed campaign context into the dialogue-pragmatics appointment close path.
- Added a handoff-state account-support boundary so right-person routing does not fall back to product diagnostics.
- Accepted usable appointment time after confirmed generic pain even when a later caution changed the previous question type.
- Allowed duplicate terminal stop text only when the repeated response is the intended end-call persistence.

## Safety Flags
{
  "creates_calendar_event": false,
  "local_llm_calls_made": false,
  "opens_prod_102": false,
  "provider_calls_made": false,
  "sends_email": false,
  "writes_crm": false
}

## RouteSignal Preservation
[
  {
    "audio_url": null,
    "call_control": "continue-call",
    "campaign_id": "campaign-prod-005-b2b-software",
    "campaign_playbook_id": null,
    "creates_calendar_event": false,
    "durable_provider_agent_created": false,
    "final_response": "Sure. What email should I note for the summary, or what callback time should I use?",
    "handoff_target_state": null,
    "lead_followup_state": {
      "appointment": {
        "confirmation_text": null,
        "confirmed": false,
        "type": "send_info_followup"
      },
      "callback": {
        "needs_clarification": false,
        "normalized": {
          "confidence": 0.0,
          "date_text": null,
          "day_text": null,
          "meridiem": null,
          "relative_date": null,
          "time_text": null
        },
        "raw_text_redacted": null
      },
      "capture_status": "needs_contact",
      "contact": {
        "email_hash": null,
        "email_redacted": null,
        "email_source": "none",
        "email_valid": false,
        "raw_email_stored_in_public_evidence": false
      },
      "lead_status": "open_send_info",
      "requested_summary_type": "workflow_review",
      "safety": {
        "creates_calendar_event": false,
        "local_llm_calls_made": false,
        "provider_calls_made": false,
        "sends_email": false,
        "stores_private_contact_in_public_evidence": false,
        "writes_crm": false
      },
      "schema_version": 1
    },
    "local_llm_calls_made": false,
    "opens_prod_102": false,
    "outgoing_candidate_gaps": [],
    "playbook_id": "ROUTESIGNAL-DIAGNOSTIC-PLAYBOOK-001",
    "playbook_review_focus": null,
    "provider_agent_used": false,
    "provider_calls_made": false,
    "semantic": "send_info_affirmed_without_contact",
    "send_info_state": {
      "capture_status": "needs_email_or_callback_time",
      "captured_callback_time": null,
      "captured_email_redacted": null,
      "human_followup_needed": true,
      "lead_status": "open_send_info",
      "requested": true,
      "requested_at_turn": 5,
      "requested_summary_type": "workflow_review",
      "stores_private_contact_in_public_evidence": false
    },
    "sends_email": false,
    "target_gap": null,
    "transcript": "yes send it",
    "tts_input_text": "Sure. Um, what email should I note for the summary, <break time=\"0.24s\" /> or what callback time should I use?",
    "voice_cloning_used": false,
    "writes_crm": false
  },
  {
    "audio_url": null,
    "call_control": "schedule-and-end",
    "campaign_id": "campaign-prod-005-b2b-software",
    "campaign_playbook_id": null,
    "creates_calendar_event": false,
    "durable_provider_agent_created": false,
    "final_response": "Confirmed. I will record that callback time for the specialist. Goodbye.",
    "handoff_target_state": null,
    "lead_followup_state": {
      "appointment": {
        "confirmation_text": "send-info callback time captured",
        "confirmed": true,
        "type": "send_info_followup"
      },
      "callback": {
        "needs_clarification": false,
        "normalized": {
          "confidence": 0.9,
          "date_text": "tomorrow",
          "day_text": null,
          "meridiem": "unknown",
          "relative_date": "tomorrow",
          "time_text": "3"
        },
        "raw_text_redacted": "tomorrow at 3 works"
      },
      "capture_status": "callback_time_captured",
      "contact": {
        "email_hash": null,
        "email_redacted": null,
        "email_source": "none",
        "email_valid": false,
        "raw_email_stored_in_public_evidence": false
      },
      "lead_status": "open_callback",
      "requested_summary_type": "workflow_review",
      "safety": {
        "creates_calendar_event": false,
        "local_llm_calls_made": false,
        "provider_calls_made": false,
        "sends_email": false,
        "stores_private_contact_in_public_evidence": false,
        "writes_crm": false
      },
      "schema_version": 1
    },
    "local_llm_calls_made": false,
    "opens_prod_102": false,
    "outgoing_candidate_gaps": [],
    "playbook_id": "ROUTESIGNAL-DIAGNOSTIC-PLAYBOOK-001",
    "playbook_review_focus": null,
    "provider_agent_used": false,
    "provider_calls_made": false,
    "semantic": "callback_time_provided",
    "send_info_state": {
      "capture_status": "callback_time_captured",
      "captured_callback_time": "tomorrow at 3 works",
      "captured_email_redacted": null,
      "human_followup_needed": true,
      "lead_status": "open_callback",
      "requested": true,
      "requested_at_turn": 5,
      "requested_summary_type": "workflow_review",
      "stores_private_contact_in_public_evidence": false
    },
    "sends_email": false,
    "target_gap": null,
    "transcript": "tomorrow at 3 works",
    "tts_input_text": "Confirmed. I will record that callback time for the specialist. Goodbye.",
    "voice_cloning_used": false,
    "writes_crm": false
  }
]
