# ADVERSARIAL-MATRIX-RED-FINDINGS-AUDIT-001

## Summary
- Source checkpoint: `LIVE-INSPIRED-ADVERSARIAL-DIALOGUE-MATRIX-001`
- Source red findings: `217`
- Audited red findings: `217`

## Count By Root Cause
- `appointment_too_early`: `6`
- `asr_near_miss_gap_not_recognized`: `6`
- `campaign_contamination`: `4`
- `hostile_challenge_not_deescalated`: `18`
- `needs_human_review`: `38`
- `out_of_campaign_relevance_bad_fallback`: `12`
- `repeated_response_without_progress`: `24`
- `stability_guard_menu_reset`: `109`

## Count By Source
- `contextual_buyer_semantics`: `6`
- `dialogue_pragmatics`: `6`
- `live_voice_session_policy`: `6`
- `pre_speech_conversation_stability_guard`: `109`
- `terminal_call_control`: `6`
- `universal_response_shape`: `84`

## Count By Scenario Family
- `asr_near_miss_gap_phrases`: `1`
- `asr_near_miss_invented_transcript_stress`: `6`
- `buyer_correction_contradiction_stress`: `1`
- `buyer_says_agent_is_wrong`: `18`
- `callback_time_too_early_or_ambiguous`: `18`
- `campaign_selector_wrong_campaign_contamination`: `8`
- `commercial_pressure_close_strength_stress`: `16`
- `commercial_quality_stress`: `8`
- `direct_product_value_challenge_loops`: `6`
- `disallowed_persistence_after_stop`: `6`
- `human_context_interruption_pressure`: `6`
- `impact_before_clean_pain`: `16`
- `long_conversation_state_drift`: `5`
- `multi_campaign_contamination_stress`: `14`
- `permission_weak_acknowledgement_variants`: `15`
- `price_budget_affordability_stress`: `6`
- `repeated_answer_variation_anti_loop`: `18`
- `repeated_challenge_escalation`: `3`
- `repeated_product_detail_scope_questions`: `21`
- `sales_realism_score_heuristics`: `12`
- `scope_boundary_regulated_detail_stress`: `6`
- `vague_affirmative_after_context`: `7`

## Count By Campaign
- `routesignal_live_demo`: `34`
- `synthetic-automotive-service-review`: `42`
- `synthetic-b2b-saas-operations`: `34`
- `synthetic-insurance-review`: `37`
- `synthetic-membership-plan-review`: `31`
- `synthetic-telecom-plan-review`: `39`

## Top Examples
### adv-asr-near-miss-gap-phrases-synthetic-automotive-service-review-04
- Root cause: `stability_guard_menu_reset`
- Campaign: `synthetic-automotive-service-review`
- Family: `asr_near_miss_gap_phrases`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `repeated_full_menu`
- Buyer script: `['__agent_open__', 'yeah', 'service timing is long', 'it wastes time']`
- Final response: If vehicle issue, repair timing, or warranty or estimate are actually relevant, a service advisor can do a short service advisor inspection review. If not, I can stop here; should I ask one quick fit question?

### adv-asr-near-miss-invented-transcript-stress-routesignal_live_demo-01
- Root cause: `asr_near_miss_gap_not_recognized`
- Campaign: `routesignal_live_demo`
- Family: `asr_near_miss_invented_transcript_stress`
- Source: `universal_response_shape`
- Flags: `asr_near_miss_not_clarified`
- Buyer script: `['__agent_open__', 'what should I care']`
- Final response: Fair question. Only if inbound demo follow-up slipping is costing time, creating delays, or hurting follow-up quality. If that is happening, a short review can confirm whether it is worth fixing. Is that showing up now?

### adv-asr-near-miss-invented-transcript-stress-synthetic-automotive-service-review-01
- Root cause: `asr_near_miss_gap_not_recognized`
- Campaign: `synthetic-automotive-service-review`
- Family: `asr_near_miss_invented_transcript_stress`
- Source: `universal_response_shape`
- Flags: `asr_near_miss_not_clarified`
- Buyer script: `['__agent_open__', 'what should I care']`
- Final response: Fair question. Only if repair timing is costing time, creating delays, or hurting follow-up quality. If that is happening, a short review can confirm whether it is worth fixing. Is that showing up now?

### adv-asr-near-miss-invented-transcript-stress-synthetic-b2b-saas-operations-01
- Root cause: `asr_near_miss_gap_not_recognized`
- Campaign: `synthetic-b2b-saas-operations`
- Family: `asr_near_miss_invented_transcript_stress`
- Source: `universal_response_shape`
- Flags: `asr_near_miss_not_clarified`
- Buyer script: `['__agent_open__', 'what should I care']`
- Final response: Fair question. Only if manual work is costing time, creating delays, or hurting follow-up quality. If that is happening, a short review can confirm whether it is worth fixing. Is that showing up now?

### adv-asr-near-miss-invented-transcript-stress-synthetic-insurance-review-01
- Root cause: `asr_near_miss_gap_not_recognized`
- Campaign: `synthetic-insurance-review`
- Family: `asr_near_miss_invented_transcript_stress`
- Source: `universal_response_shape`
- Flags: `asr_near_miss_not_clarified`
- Buyer script: `['__agent_open__', 'what should I care']`
- Final response: Fair question. Only if premium pressure is costing time, creating delays, or hurting follow-up quality. If that is happening, a short review can confirm whether it is worth fixing. Is that showing up now?

### adv-asr-near-miss-invented-transcript-stress-synthetic-membership-plan-review-01
- Root cause: `asr_near_miss_gap_not_recognized`
- Campaign: `synthetic-membership-plan-review`
- Family: `asr_near_miss_invented_transcript_stress`
- Source: `universal_response_shape`
- Flags: `asr_near_miss_not_clarified`
- Buyer script: `['__agent_open__', 'what should I care']`
- Final response: Fair question. Only if plan fit is costing time, creating delays, or hurting follow-up quality. If that is happening, a short review can confirm whether it is worth fixing. Is that showing up now?

### adv-asr-near-miss-invented-transcript-stress-synthetic-telecom-plan-review-01
- Root cause: `asr_near_miss_gap_not_recognized`
- Campaign: `synthetic-telecom-plan-review`
- Family: `asr_near_miss_invented_transcript_stress`
- Source: `universal_response_shape`
- Flags: `asr_near_miss_not_clarified`
- Buyer script: `['__agent_open__', 'what should I care']`
- Final response: Fair question. Only if plan fit is costing time, creating delays, or hurting follow-up quality. If that is happening, a short review can confirm whether it is worth fixing. Is that showing up now?

### adv-buyer-correction-contradiction-stress-routesignal_live_demo-02
- Root cause: `needs_human_review`
- Campaign: `routesignal_live_demo`
- Family: `buyer_correction_contradiction_stress`
- Source: `contextual_buyer_semantics`
- Flags: `too_long_for_live_voice`
- Buyer script: `['__agent_open__', 'yeah', 'callbacks are a problem', 'I said inbound demo follow-up, not callbacks']`
- Final response: Got it, you already said that is the problem: missed callbacks. RouteSignal helps demo leads stay assigned, reminded, and followed up before callback gaps turn into lost opportunities. The next step is a short workflow review with someone from Northstar. They would check missed callback reminders against your actual follow-up flow. What time works for a quick call?

### adv-buyer-says-agent-is-wrong-routesignal_live_demo-01
- Root cause: `hostile_challenge_not_deescalated`
- Campaign: `routesignal_live_demo`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that's wrong"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a non-binding workflow review is useful.

### adv-buyer-says-agent-is-wrong-routesignal_live_demo-02
- Root cause: `hostile_challenge_not_deescalated`
- Campaign: `routesignal_live_demo`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that doesn't make sense"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a non-binding workflow review is useful.

### adv-buyer-says-agent-is-wrong-routesignal_live_demo-03
- Root cause: `hostile_challenge_not_deescalated`
- Campaign: `routesignal_live_demo`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "you're making assumptions"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a non-binding workflow review is useful.

### adv-buyer-says-agent-is-wrong-synthetic-automotive-service-review-01
- Root cause: `hostile_challenge_not_deescalated`
- Campaign: `synthetic-automotive-service-review`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that's wrong"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a service advisor inspection review is useful.

### adv-buyer-says-agent-is-wrong-synthetic-automotive-service-review-02
- Root cause: `hostile_challenge_not_deescalated`
- Campaign: `synthetic-automotive-service-review`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that doesn't make sense"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a service advisor inspection review is useful.

### adv-buyer-says-agent-is-wrong-synthetic-automotive-service-review-03
- Root cause: `hostile_challenge_not_deescalated`
- Campaign: `synthetic-automotive-service-review`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "you're making assumptions"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a service advisor inspection review is useful.

### adv-buyer-says-agent-is-wrong-synthetic-b2b-saas-operations-01
- Root cause: `hostile_challenge_not_deescalated`
- Campaign: `synthetic-b2b-saas-operations`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that's wrong"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether an operations fit review is useful.

### adv-buyer-says-agent-is-wrong-synthetic-b2b-saas-operations-02
- Root cause: `hostile_challenge_not_deescalated`
- Campaign: `synthetic-b2b-saas-operations`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that doesn't make sense"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether an operations fit review is useful.

### adv-buyer-says-agent-is-wrong-synthetic-b2b-saas-operations-03
- Root cause: `hostile_challenge_not_deescalated`
- Campaign: `synthetic-b2b-saas-operations`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "you're making assumptions"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether an operations fit review is useful.

### adv-buyer-says-agent-is-wrong-synthetic-insurance-review-01
- Root cause: `hostile_challenge_not_deescalated`
- Campaign: `synthetic-insurance-review`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that's wrong"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a licensed coverage review is useful.

### adv-buyer-says-agent-is-wrong-synthetic-insurance-review-02
- Root cause: `hostile_challenge_not_deescalated`
- Campaign: `synthetic-insurance-review`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that doesn't make sense"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a licensed coverage review is useful.

### adv-buyer-says-agent-is-wrong-synthetic-insurance-review-03
- Root cause: `hostile_challenge_not_deescalated`
- Campaign: `synthetic-insurance-review`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "you're making assumptions"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a licensed coverage review is useful.

## Recommended Patch Scope
- Patch stability_guard_menu_reset for near configured gaps before broad exploratory work.
- Patch internal_wording_source_live_policy where customer-facing boundary text leaks implementation wording.
- Patch direct question / why-human-review only after the menu reset slice is green.
- Leave callback ambiguity, repeated-response style, and broad hostile-challenge polish as follow-up unless focused validators reproduce a low-risk fix.

## Runtime Behavior Changed
- `false`
