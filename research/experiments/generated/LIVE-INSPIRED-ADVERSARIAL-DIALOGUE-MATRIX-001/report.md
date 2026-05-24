# LIVE-INSPIRED-ADVERSARIAL-DIALOGUE-MATRIX-001

## Summary
- Status: `red_findings`
- Scenario count: `729`
- Multi-turn conversations: `398`
- Core gate failures: `0`
- Exploratory red findings: `263`

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
- `passed`: `466`
- `failed_or_red`: `263`
- `core_gate_failures`: `0`
- `exploratory_red_findings`: `263`

## Top Failure Clusters
- `repeated_full_menu`: `174`
- `hostile_response_not_deescalated`: `27`
- `repeated_response`: `24`
- `appointment_too_early`: `12`
- `out_of_scope_reset_after_relevant_context`: `12`
- `asr_near_miss_not_clarified`: `9`
- `campaign_contamination`: `4`
- `internal_wording_leak`: `3`
- `too_long_for_live_voice`: `1`
- `false_assumption_not_repaired`: `1`

## Failures By Scenario Family
- `asr_near_miss_gap_phrases`: `4`
- `asr_near_miss_invented_transcript_stress`: `6`
- `buyer_correction_contradiction_stress`: `2`
- `buyer_says_agent_is_wrong`: `24`
- `callback_time_too_early_or_ambiguous`: `24`
- `campaign_selector_wrong_campaign_contamination`: `8`
- `commercial_pressure_close_strength_stress`: `16`
- `commercial_quality_stress`: `8`
- `direct_product_value_challenge_loops`: `6`
- `disallowed_persistence_after_stop`: `6`
- `early_callback_premature_scheduling`: `6`
- `hostile_challenging_buyer`: `21`
- `human_context_interruption_pressure`: `6`
- `impact_before_clean_pain`: `16`
- `long_conversation_state_drift`: `5`
- `multi_campaign_contamination_stress`: `17`
- `permission_weak_acknowledgement_variants`: `15`
- `price_budget_affordability_stress`: `6`
- `repeated_answer_variation_anti_loop`: `18`
- `repeated_challenge_escalation`: `3`
- `repeated_product_detail_scope_questions`: `21`
- `sales_realism_score_heuristics`: `12`
- `scope_boundary_regulated_detail_stress`: `6`
- `vague_affirmative_after_context`: `7`

## Failures By Campaign
- `routesignal_live_demo`: `40`
- `synthetic-automotive-service-review`: `51`
- `synthetic-b2b-saas-operations`: `41`
- `synthetic-insurance-review`: `45`
- `synthetic-membership-plan-review`: `38`
- `synthetic-telecom-plan-review`: `48`

## Failures By Selected Action Source
- `contextual_buyer_semantics`: `12`
- `dialogue_pragmatics`: `6`
- `live_voice_session_policy`: `19`
- `pre_speech_conversation_stability_guard`: `134`
- `terminal_call_control`: `6`
- `universal_response_shape`: `86`

## Examples Of Worst Conversations
### adv-multi-campaign-contamination-stress-synthetic-automotive-service-review-02
- Family: `multi_campaign_contamination_stress`
- Campaign: `synthetic-automotive-service-review`
- Priority: `critical`
- Flags: `internal_wording_leak`
- Buyer script: `['__agent_open__', 'I need insurance coverage', 'why are you talking about something else']`
- Final response: Fair question. This call is about a short human review around repair timing. If that is not relevant, I should stop here.

### adv-multi-campaign-contamination-stress-synthetic-insurance-review-02
- Family: `multi_campaign_contamination_stress`
- Campaign: `synthetic-insurance-review`
- Priority: `critical`
- Flags: `internal_wording_leak`
- Buyer script: `['__agent_open__', 'I need insurance coverage', 'why are you talking about something else']`
- Final response: Fair question. This call is about a short human review around premium pressure. If that is not relevant, I should stop here.

### adv-multi-campaign-contamination-stress-synthetic-telecom-plan-review-02
- Family: `multi_campaign_contamination_stress`
- Campaign: `synthetic-telecom-plan-review`
- Priority: `critical`
- Flags: `internal_wording_leak`
- Buyer script: `['__agent_open__', 'I need insurance coverage', 'why are you talking about something else']`
- Final response: Fair question. This call is about a short human review around plan fit. If that is not relevant, I should stop here.

### adv-buyer-correction-contradiction-stress-synthetic-automotive-service-review-04
- Family: `buyer_correction_contradiction_stress`
- Campaign: `synthetic-automotive-service-review`
- Priority: `medium`
- Flags: `false_assumption_not_repaired, repeated_full_menu`
- Buyer script: `['__agent_open__', 'yeah', "that's not my issue"]`
- Final response: The quick check is whether any of these areas is worth a short service advisor inspection review: vehicle issue, repair timing, or warranty or estimate. If not, I can stop here; which part should I check first?

### adv-buyer-says-agent-is-wrong-routesignal_live_demo-04
- Family: `buyer_says_agent_is_wrong`
- Campaign: `routesignal_live_demo`
- Priority: `medium`
- Flags: `hostile_response_not_deescalated, repeated_full_menu`
- Buyer script: `['__agent_open__', 'this sounds automated']`
- Final response: This is about inbound demo follow-up: one person should be responsible for the next reply. That prevents missed follow-up. Which part is least clear today?

### adv-hostile-challenging-buyer-routesignal_live_demo-03
- Family: `hostile_challenging_buyer`
- Campaign: `routesignal_live_demo`
- Priority: `medium`
- Flags: `hostile_response_not_deescalated, repeated_full_menu`
- Buyer script: `['__agent_open__', 'this is pointless']`
- Final response: This is about inbound demo follow-up: one person should be responsible for the next reply. That prevents missed follow-up. Which part is least clear today?

### adv-hostile-challenging-buyer-routesignal_live_demo-04
- Family: `hostile_challenging_buyer`
- Campaign: `routesignal_live_demo`
- Priority: `medium`
- Flags: `hostile_response_not_deescalated, repeated_full_menu`
- Buyer script: `['__agent_open__', 'prove this is useful']`
- Final response: This is about inbound demo follow-up: one person should be responsible for the next reply. That prevents missed follow-up. Which part is least clear today?

### adv-asr-near-miss-gap-phrases-synthetic-automotive-service-review-04
- Family: `asr_near_miss_gap_phrases`
- Campaign: `synthetic-automotive-service-review`
- Priority: `medium`
- Flags: `repeated_full_menu`
- Buyer script: `['__agent_open__', 'yeah', 'service timing is long', 'it wastes time']`
- Final response: If vehicle issue, repair timing, or warranty or estimate are actually relevant, a service advisor can do a short service advisor inspection review. If not, I can stop here; should I ask one quick fit question?

### adv-asr-near-miss-gap-phrases-synthetic-b2b-saas-operations-03
- Family: `asr_near_miss_gap_phrases`
- Campaign: `synthetic-b2b-saas-operations`
- Priority: `medium`
- Flags: `asr_near_miss_not_clarified`
- Buyer script: `['__agent_open__', 'yeah', 'integration thing is confusing']`
- Final response: Maybe integration, understood. Is that an active concern now, or just something you might want checked later?

### adv-asr-near-miss-gap-phrases-synthetic-membership-plan-review-03
- Family: `asr_near_miss_gap_phrases`
- Campaign: `synthetic-membership-plan-review`
- Priority: `medium`
- Flags: `asr_near_miss_not_clarified`
- Buyer script: `['__agent_open__', 'yeah', 'usage thing is unclear']`
- Final response: Maybe usage or value, understood. Is that an active concern now, or just something you might want checked later?

### adv-asr-near-miss-gap-phrases-synthetic-telecom-plan-review-03
- Family: `asr_near_miss_gap_phrases`
- Campaign: `synthetic-telecom-plan-review`
- Priority: `medium`
- Flags: `asr_near_miss_not_clarified`
- Buyer script: `['__agent_open__', 'yeah', 'contact switching is confusing']`
- Final response: Maybe contract or switching, understood. Is that an active concern now, or just something you might want checked later?

### adv-asr-near-miss-invented-transcript-stress-routesignal_live_demo-01
- Family: `asr_near_miss_invented_transcript_stress`
- Campaign: `routesignal_live_demo`
- Priority: `medium`
- Flags: `asr_near_miss_not_clarified`
- Buyer script: `['__agent_open__', 'what should I care']`
- Final response: Fair question. Only if inbound demo follow-up slipping is costing time, creating delays, or hurting follow-up quality. If that is happening, a short review can confirm whether it is worth fixing. Is that showing up now?

## Stability Guard Override Findings

## Direct Question/Challenge Findings

## ASR Near-Miss Findings
- `adv-asr-near-miss-gap-phrases-synthetic-telecom-plan-review-03`
- `adv-asr-near-miss-gap-phrases-synthetic-membership-plan-review-03`
- `adv-asr-near-miss-gap-phrases-synthetic-b2b-saas-operations-03`
- `adv-asr-near-miss-invented-transcript-stress-routesignal_live_demo-01`
- `adv-asr-near-miss-invented-transcript-stress-synthetic-insurance-review-01`
- `adv-asr-near-miss-invented-transcript-stress-synthetic-telecom-plan-review-01`
- `adv-asr-near-miss-invented-transcript-stress-synthetic-automotive-service-review-01`
- `adv-asr-near-miss-invented-transcript-stress-synthetic-membership-plan-review-01`
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
