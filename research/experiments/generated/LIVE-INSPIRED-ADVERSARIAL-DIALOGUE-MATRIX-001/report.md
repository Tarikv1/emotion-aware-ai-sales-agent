# LIVE-INSPIRED-ADVERSARIAL-DIALOGUE-MATRIX-001

## Summary
- Status: `red_findings`
- Scenario count: `729`
- Multi-turn conversations: `398`
- Core gate failures: `0`
- Exploratory red findings: `352`

## Scenario Count
- Total scenario runs: `729`
- Core gate: `9`
- Exploratory: `720`

## Campaign Coverage
- `routesignal_live_demo`: `125`
- `synthetic-automotive-service-review`: `120`
- `synthetic-b2b-saas-operations`: `120`
- `synthetic-insurance-review`: `122`
- `synthetic-membership-plan-review`: `120`
- `synthetic-telecom-plan-review`: `122`

## Scenario Family Coverage
- `agent_looping_complaints`: `24`
- `asr_near_miss_gap_phrases`: `26`
- `asr_near_miss_invented_transcript_stress`: `24`
- `buyer_correction_contradiction_stress`: `24`
- `buyer_says_agent_is_wrong`: `24`
- `callback_time_too_early_or_ambiguous`: `24`
- `campaign_selector_wrong_campaign_contamination`: `24`
- `commercial_pressure_close_strength_stress`: `25`
- `commercial_quality_stress`: `24`
- `direct_product_value_challenge_loops`: `25`
- `disallowed_persistence_after_stop`: `24`
- `early_callback_premature_scheduling`: `24`
- `false_assumption_correction`: `25`
- `hostile_challenging_buyer`: `24`
- `human_context_interruption_pressure`: `24`
- `human_context_sales_intent_hybrids`: `24`
- `impact_before_clean_pain`: `24`
- `long_conversation_state_drift`: `24`
- `mixed_intent_buyer_turns`: `24`
- `multi_campaign_contamination_stress`: `24`
- `permission_weak_acknowledgement_variants`: `25`
- `price_budget_affordability_stress`: `24`
- `repeated_answer_variation_anti_loop`: `24`
- `repeated_challenge_escalation`: `24`
- `repeated_product_detail_scope_questions`: `25`
- `sales_realism_score_heuristics`: `24`
- `scope_boundary_regulated_detail_stress`: `25`
- `stop_refusal_pressure_test`: `24`
- `vague_affirmative_after_context`: `25`
- `why_human_review_challenge`: `24`

## Pass/Fail Counts
- `passed`: `377`
- `failed_or_red`: `352`
- `core_gate_failures`: `0`
- `exploratory_red_findings`: `352`

## Top Failure Clusters
- `repeated_full_menu`: `266`
- `repeated_response`: `18`
- `false_assumption_not_repaired`: `14`
- `out_of_scope_reset_after_relevant_context`: `14`
- `did_not_answer_direct_question`: `13`
- `asr_near_miss_not_clarified`: `12`
- `appointment_too_early`: `12`
- `hostile_response_not_deescalated`: `12`
- `campaign_contamination`: `11`
- `internal_wording_leak`: `6`
- `too_long_for_live_voice`: `4`

## Failures By Scenario Family
- `agent_looping_complaints`: `5`
- `asr_near_miss_gap_phrases`: `10`
- `asr_near_miss_invented_transcript_stress`: `8`
- `buyer_correction_contradiction_stress`: `10`
- `buyer_says_agent_is_wrong`: `24`
- `callback_time_too_early_or_ambiguous`: `24`
- `campaign_selector_wrong_campaign_contamination`: `14`
- `commercial_pressure_close_strength_stress`: `16`
- `commercial_quality_stress`: `8`
- `direct_product_value_challenge_loops`: `6`
- `disallowed_persistence_after_stop`: `6`
- `early_callback_premature_scheduling`: `6`
- `false_assumption_correction`: `7`
- `hostile_challenging_buyer`: `21`
- `human_context_interruption_pressure`: `6`
- `impact_before_clean_pain`: `16`
- `long_conversation_state_drift`: `7`
- `mixed_intent_buyer_turns`: `6`
- `multi_campaign_contamination_stress`: `21`
- `permission_weak_acknowledgement_variants`: `15`
- `price_budget_affordability_stress`: `6`
- `repeated_answer_variation_anti_loop`: `23`
- `repeated_challenge_escalation`: `24`
- `repeated_product_detail_scope_questions`: `22`
- `sales_realism_score_heuristics`: `12`
- `scope_boundary_regulated_detail_stress`: `6`
- `vague_affirmative_after_context`: `12`
- `why_human_review_challenge`: `11`

## Failures By Campaign
- `routesignal_live_demo`: `57`
- `synthetic-automotive-service-review`: `64`
- `synthetic-b2b-saas-operations`: `58`
- `synthetic-insurance-review`: `59`
- `synthetic-membership-plan-review`: `54`
- `synthetic-telecom-plan-review`: `60`

## Failures By Selected Action Source
- `contextual_buyer_semantics`: `16`
- `dialogue_pragmatics`: `6`
- `live_voice_session_policy`: `37`
- `pre_speech_conversation_stability_guard`: `223`
- `terminal_call_control`: `6`
- `universal_response_shape`: `64`

## Examples Of Worst Conversations
### adv-multi-campaign-contamination-stress-routesignal_live_demo-02
- Family: `multi_campaign_contamination_stress`
- Campaign: `routesignal_live_demo`
- Priority: `critical`
- Flags: `internal_wording_leak`
- Buyer script: `['__agent_open__', 'I need insurance coverage', 'why are you talking about something else']`
- Final response: Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?

### adv-multi-campaign-contamination-stress-synthetic-automotive-service-review-02
- Family: `multi_campaign_contamination_stress`
- Campaign: `synthetic-automotive-service-review`
- Priority: `critical`
- Flags: `internal_wording_leak`
- Buyer script: `['__agent_open__', 'I need insurance coverage', 'why are you talking about something else']`
- Final response: Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?

### adv-multi-campaign-contamination-stress-synthetic-b2b-saas-operations-02
- Family: `multi_campaign_contamination_stress`
- Campaign: `synthetic-b2b-saas-operations`
- Priority: `critical`
- Flags: `internal_wording_leak`
- Buyer script: `['__agent_open__', 'I need insurance coverage', 'why are you talking about something else']`
- Final response: Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?

### adv-multi-campaign-contamination-stress-synthetic-insurance-review-02
- Family: `multi_campaign_contamination_stress`
- Campaign: `synthetic-insurance-review`
- Priority: `critical`
- Flags: `internal_wording_leak`
- Buyer script: `['__agent_open__', 'I need insurance coverage', 'why are you talking about something else']`
- Final response: Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?

### adv-multi-campaign-contamination-stress-synthetic-membership-plan-review-02
- Family: `multi_campaign_contamination_stress`
- Campaign: `synthetic-membership-plan-review`
- Priority: `critical`
- Flags: `internal_wording_leak`
- Buyer script: `['__agent_open__', 'I need insurance coverage', 'why are you talking about something else']`
- Final response: Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?

### adv-multi-campaign-contamination-stress-synthetic-telecom-plan-review-02
- Family: `multi_campaign_contamination_stress`
- Campaign: `synthetic-telecom-plan-review`
- Priority: `critical`
- Flags: `internal_wording_leak`
- Buyer script: `['__agent_open__', 'I need insurance coverage', 'why are you talking about something else']`
- Final response: Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?

### adv-direct-product-value-challenge-loops-routesignal_live_demo-02
- Family: `direct_product_value_challenge_loops`
- Campaign: `routesignal_live_demo`
- Priority: `high`
- Flags: `did_not_answer_direct_question, repeated_full_menu`
- Buyer script: `['__agent_open__', 'what are you selling', 'explain it plainly', 'say it in one sentence']`
- Final response: If callback reminders for demo follow-up sit in a spreadsheet, they can slip. Which part is more familiar: manual tracking or missed callbacks?

### adv-direct-product-value-challenge-loops-synthetic-automotive-service-review-02
- Family: `direct_product_value_challenge_loops`
- Campaign: `synthetic-automotive-service-review`
- Priority: `high`
- Flags: `did_not_answer_direct_question, repeated_full_menu`
- Buyer script: `['__agent_open__', 'what are you selling', 'explain it plainly', 'say it in one sentence']`
- Final response: I may not be the right contact for that question. Should I note a callback path, or stop here?

### adv-direct-product-value-challenge-loops-synthetic-b2b-saas-operations-02
- Family: `direct_product_value_challenge_loops`
- Campaign: `synthetic-b2b-saas-operations`
- Priority: `high`
- Flags: `did_not_answer_direct_question, repeated_full_menu`
- Buyer script: `['__agent_open__', 'what are you selling', 'explain it plainly', 'say it in one sentence']`
- Final response: I may not be the right contact for that question. Should I note a callback path, or stop here?

### adv-direct-product-value-challenge-loops-synthetic-insurance-review-02
- Family: `direct_product_value_challenge_loops`
- Campaign: `synthetic-insurance-review`
- Priority: `high`
- Flags: `did_not_answer_direct_question, repeated_full_menu`
- Buyer script: `['__agent_open__', 'what are you selling', 'explain it plainly', 'say it in one sentence']`
- Final response: I may not be the right contact for that question. Should I note a callback path, or stop here?

### adv-direct-product-value-challenge-loops-synthetic-membership-plan-review-02
- Family: `direct_product_value_challenge_loops`
- Campaign: `synthetic-membership-plan-review`
- Priority: `high`
- Flags: `did_not_answer_direct_question, repeated_full_menu`
- Buyer script: `['__agent_open__', 'what are you selling', 'explain it plainly', 'say it in one sentence']`
- Final response: I may not be the right contact for that question. Should I note a callback path, or stop here?

### adv-direct-product-value-challenge-loops-synthetic-telecom-plan-review-02
- Family: `direct_product_value_challenge_loops`
- Campaign: `synthetic-telecom-plan-review`
- Priority: `high`
- Flags: `did_not_answer_direct_question, repeated_full_menu`
- Buyer script: `['__agent_open__', 'what are you selling', 'explain it plainly', 'say it in one sentence']`
- Final response: I may not be the right contact for that question. Should I note a callback path, or stop here?

## Stability Guard Override Findings

## Direct Question/Challenge Findings
- `adv-direct-product-value-challenge-loops-routesignal_live_demo-02`
- `adv-direct-product-value-challenge-loops-synthetic-insurance-review-02`
- `adv-direct-product-value-challenge-loops-synthetic-telecom-plan-review-02`
- `adv-direct-product-value-challenge-loops-synthetic-automotive-service-review-02`
- `adv-direct-product-value-challenge-loops-synthetic-membership-plan-review-02`
- `adv-direct-product-value-challenge-loops-synthetic-b2b-saas-operations-02`
- `adv-repeated-challenge-escalation-routesignal_live_demo-04`
- `adv-why-human-review-challenge-routesignal_live_demo-04`
- `adv-why-human-review-challenge-synthetic-insurance-review-01`
- `adv-why-human-review-challenge-synthetic-telecom-plan-review-01`
- `adv-why-human-review-challenge-synthetic-automotive-service-review-01`
- `adv-why-human-review-challenge-synthetic-membership-plan-review-01`
- `adv-why-human-review-challenge-synthetic-b2b-saas-operations-01`

## ASR Near-Miss Findings
- `adv-asr-near-miss-gap-phrases-routesignal_live_demo-04`
- `adv-asr-near-miss-gap-phrases-synthetic-telecom-plan-review-03`
- `adv-asr-near-miss-gap-phrases-synthetic-membership-plan-review-01`
- `adv-asr-near-miss-gap-phrases-synthetic-membership-plan-review-02`
- `adv-asr-near-miss-gap-phrases-synthetic-b2b-saas-operations-03`
- `adv-asr-near-miss-invented-transcript-stress-routesignal_live_demo-01`
- `adv-asr-near-miss-invented-transcript-stress-synthetic-insurance-review-01`
- `adv-asr-near-miss-invented-transcript-stress-synthetic-telecom-plan-review-01`
- `adv-asr-near-miss-invented-transcript-stress-synthetic-automotive-service-review-01`
- `adv-asr-near-miss-invented-transcript-stress-synthetic-membership-plan-review-01`
- `adv-asr-near-miss-invented-transcript-stress-synthetic-membership-plan-review-02`
- `adv-asr-near-miss-invented-transcript-stress-synthetic-b2b-saas-operations-01`

## Stop/Refusal Preservation
- Explicit-stop red findings: `0`

## Side-Effect Boundary Summary
- `provider_calls_made`: `false`
- `local_llm_calls_made`: `false`
- `live_tts_used`: `false`
- `tts_provider_calls_made`: `false`
- `audio_file_created`: `false`
- `sends_email`: `false`
- `creates_calendar_event`: `false`
- `writes_crm`: `false`
- `opens_prod_102`: `false`
- `customer_audio_uploaded_to_python_server`: `false`
- `customer_audio_uploaded_to_tts_provider`: `false`

## Recommendation
- `needs human review and ranked follow-up patches`
