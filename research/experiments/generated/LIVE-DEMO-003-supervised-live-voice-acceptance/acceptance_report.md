# LIVE-DEMO-003 Supervised Live Voice Acceptance

- Checkpoint: `LIVE-DEMO-003-supervised-live-voice-acceptance`
- Demo session: `LIVE-DEMO-003-synthetic-sample`
- Campaign: `campaign-prod-005-b2b-software`
- Acceptance status: `pending_manual_review`
- Provider TTS used: `false`
- Provider LLM call occurred: `false`
- Browser fallback voice used: `true`
- Turn count: `13`

This is a supervised live voice acceptance packet. Passing it does not mean production readiness.
Failing it should produce narrow follow-up tickets, not broad runtime rewrites.
The recommended spoken path and optional stress turns are sample scenarios only, not runtime caps.

## Hard Gates

- `no_provider_hosted_durable_agent`: `true`
- `no_voice_cloning`: `true`
- `no_customer_audio_upload_to_python_server`: `true`
- `no_llm_blocking_live_spoken_response`: `true`
- `no_llm_mutation_of_final_response`: `true`
- `no_payment_collection`: `true`
- `no_bare_workflow_callback_treated_as_scheduling`: `true`
- `explicit_call_me_back_later_still_schedules`: `true`
- `terminal_call_control_stops_listening_restart`: `true`
- `no_exact_repeated_final_response`: `true`
- `no_obvious_customer_sentence_echoing`: `true`
- `no_internal_wording_leaked`: `true`

## Human Gates

- `turn_taking_average_min`: `4`
- `latency_acceptability_average_min`: `4`
- `voice_consistency_average_min`: `4`
- `response_naturalness_average_min`: `3`
- `sales_steering_average_min`: `4`
- `buyer_agency_preserved_required`: `True`
- `accepted_for_next_iteration_required`: `True`

## Manual Review Status

- Manual review is incomplete. Fill `manual_review` for every turn before accepting this checkpoint.

## Recommended Spoken Test Path

- 1. agent: Start Conversation (agent opening)
- 2. buyer: hmm okay (vague acknowledgement)
- 3. buyer: I didn't understand what you asked (previous-question clarification)
- 4. buyer: callbacks are probably the problem (callback workflow gap)
- 5. buyer: what do you mean by callbacks? (callback definition)
- 6. buyer: tell me more (follow-up continuity)
- 7. buyer: why does that matter? (value mapping)
- 8. buyer: what does it cost? (price question)
- 9. buyer: I am not sure it fits our workflow (fit objection)
- 10. buyer: no (ambiguous negative)
- 11. buyer: what next? (safe next step)
- 12. buyer: call me back later (callback scheduling request)
- 13. buyer: tomorrow at 3 works (callback time confirmation after scheduling context)

## Optional Stress Turns

- you called me
- I don't have a question
- I don't know what you're talking about
- does it replace my CRM?
- does it have SOC 2?
- send me a short summary
- tomorrow at 3 works

## Next Recommendation

- Run the supervised live call and fill every manual review field before accepting LIVE-DEMO-003.