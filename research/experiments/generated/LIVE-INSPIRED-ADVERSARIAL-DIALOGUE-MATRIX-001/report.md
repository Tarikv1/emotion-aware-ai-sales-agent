# LIVE-INSPIRED-ADVERSARIAL-DIALOGUE-MATRIX-001

## Summary
- Status: `red_findings`
- Scenario count: `729`
- Multi-turn conversations: `398`
- Core gate failures: `0`
- Exploratory red findings: `64`

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
- `passed`: `665`
- `failed_or_red`: `64`
- `core_gate_failures`: `0`
- `exploratory_red_findings`: `64`

## Top Failure Clusters
- `repeated_response`: `23`
- `hostile_response_not_deescalated`: `18`
- `out_of_scope_reset_after_relevant_context`: `12`
- `appointment_too_early`: `6`
- `campaign_contamination`: `4`
- `too_long_for_live_voice`: `1`

## Failures By Scenario Family
- `buyer_correction_contradiction_stress`: `1`
- `buyer_says_agent_is_wrong`: `18`
- `callback_time_too_early_or_ambiguous`: `6`
- `campaign_selector_wrong_campaign_contamination`: `5`
- `commercial_quality_stress`: `5`
- `multi_campaign_contamination_stress`: `9`
- `repeated_answer_variation_anti_loop`: `18`
- `scope_boundary_regulated_detail_stress`: `2`

## Failures By Campaign
- `routesignal_live_demo`: `12`
- `synthetic-automotive-service-review`: `11`
- `synthetic-b2b-saas-operations`: `11`
- `synthetic-insurance-review`: `11`
- `synthetic-membership-plan-review`: `8`
- `synthetic-telecom-plan-review`: `11`

## Failures By Selected Action Source
- `contextual_buyer_semantics`: `3`
- `live_voice_session_policy`: `5`
- `pre_speech_conversation_stability_guard`: `5`
- `universal_response_shape`: `51`

## Examples Of Worst Conversations
### adv-buyer-correction-contradiction-stress-routesignal_live_demo-02
- Family: `buyer_correction_contradiction_stress`
- Campaign: `routesignal_live_demo`
- Priority: `medium`
- Flags: `too_long_for_live_voice`
- Buyer script: `['__agent_open__', 'yeah', 'callbacks are a problem', 'I said inbound demo follow-up, not callbacks']`
- Final response: Got it, you already said that is the problem: missed callbacks. RouteSignal helps demo leads stay assigned, reminded, and followed up before callback gaps turn into lost opportunities. The next step is a short workflow review with someone from Northstar. They would check missed callback reminders against your actual follow-up flow. What time works for a quick call?

### adv-buyer-says-agent-is-wrong-routesignal_live_demo-01
- Family: `buyer_says_agent_is_wrong`
- Campaign: `routesignal_live_demo`
- Priority: `medium`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that's wrong"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a non-binding workflow review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-routesignal_live_demo-02
- Family: `buyer_says_agent_is_wrong`
- Campaign: `routesignal_live_demo`
- Priority: `medium`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that doesn't make sense"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a non-binding workflow review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-routesignal_live_demo-03
- Family: `buyer_says_agent_is_wrong`
- Campaign: `routesignal_live_demo`
- Priority: `medium`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "you're making assumptions"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a non-binding workflow review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-automotive-service-review-01
- Family: `buyer_says_agent_is_wrong`
- Campaign: `synthetic-automotive-service-review`
- Priority: `medium`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that's wrong"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a service advisor inspection review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-automotive-service-review-02
- Family: `buyer_says_agent_is_wrong`
- Campaign: `synthetic-automotive-service-review`
- Priority: `medium`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that doesn't make sense"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a service advisor inspection review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-automotive-service-review-03
- Family: `buyer_says_agent_is_wrong`
- Campaign: `synthetic-automotive-service-review`
- Priority: `medium`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "you're making assumptions"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a service advisor inspection review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-b2b-saas-operations-01
- Family: `buyer_says_agent_is_wrong`
- Campaign: `synthetic-b2b-saas-operations`
- Priority: `medium`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that's wrong"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether an operations fit review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-b2b-saas-operations-02
- Family: `buyer_says_agent_is_wrong`
- Campaign: `synthetic-b2b-saas-operations`
- Priority: `medium`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that doesn't make sense"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether an operations fit review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-b2b-saas-operations-03
- Family: `buyer_says_agent_is_wrong`
- Campaign: `synthetic-b2b-saas-operations`
- Priority: `medium`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "you're making assumptions"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether an operations fit review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-insurance-review-01
- Family: `buyer_says_agent_is_wrong`
- Campaign: `synthetic-insurance-review`
- Priority: `medium`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that's wrong"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a licensed coverage review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-insurance-review-02
- Family: `buyer_says_agent_is_wrong`
- Campaign: `synthetic-insurance-review`
- Priority: `medium`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that doesn't make sense"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a licensed coverage review is useful. Is there any issue here you actually want reviewed?

## Stability Guard Override Findings

## Direct Question/Challenge Findings

## ASR Near-Miss Findings

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
