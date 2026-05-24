# ADVERSARIAL-MATRIX-RED-FINDINGS-AUDIT-001

## Summary
- Source checkpoint: `LIVE-INSPIRED-ADVERSARIAL-DIALOGUE-MATRIX-001`
- Source red findings: `263`
- Audited red findings: `263`

## Count By Root Cause
- `appointment_too_early`: `12`
- `asr_near_miss_gap_not_recognized`: `9`
- `campaign_contamination`: `4`
- `hostile_challenge_not_deescalated`: `24`
- `internal_wording_source_universal`: `3`
- `needs_human_review`: `41`
- `out_of_campaign_relevance_bad_fallback`: `12`
- `repeated_response_without_progress`: `24`
- `stability_guard_menu_reset`: `134`

## Count By Source
- `contextual_buyer_semantics`: `12`
- `dialogue_pragmatics`: `6`
- `live_voice_session_policy`: `19`
- `pre_speech_conversation_stability_guard`: `134`
- `terminal_call_control`: `6`
- `universal_response_shape`: `86`

## Count By Scenario Family
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

## Count By Campaign
- `routesignal_live_demo`: `40`
- `synthetic-automotive-service-review`: `51`
- `synthetic-b2b-saas-operations`: `41`
- `synthetic-insurance-review`: `45`
- `synthetic-membership-plan-review`: `38`
- `synthetic-telecom-plan-review`: `48`

## Top Examples
### adv-multi-campaign-contamination-stress-synthetic-automotive-service-review-02
- Root cause: `internal_wording_source_universal`
- Campaign: `synthetic-automotive-service-review`
- Family: `multi_campaign_contamination_stress`
- Source: `universal_response_shape`
- Flags: `internal_wording_leak`
- Buyer script: `['__agent_open__', 'I need insurance coverage', 'why are you talking about something else']`
- Final response: Fair question. This call is about a short human review around repair timing. If that is not relevant, I should stop here.

### adv-multi-campaign-contamination-stress-synthetic-insurance-review-02
- Root cause: `internal_wording_source_universal`
- Campaign: `synthetic-insurance-review`
- Family: `multi_campaign_contamination_stress`
- Source: `universal_response_shape`
- Flags: `internal_wording_leak`
- Buyer script: `['__agent_open__', 'I need insurance coverage', 'why are you talking about something else']`
- Final response: Fair question. This call is about a short human review around premium pressure. If that is not relevant, I should stop here.

### adv-multi-campaign-contamination-stress-synthetic-telecom-plan-review-02
- Root cause: `internal_wording_source_universal`
- Campaign: `synthetic-telecom-plan-review`
- Family: `multi_campaign_contamination_stress`
- Source: `universal_response_shape`
- Flags: `internal_wording_leak`
- Buyer script: `['__agent_open__', 'I need insurance coverage', 'why are you talking about something else']`
- Final response: Fair question. This call is about a short human review around plan fit. If that is not relevant, I should stop here.

### adv-buyer-correction-contradiction-stress-synthetic-automotive-service-review-04
- Root cause: `stability_guard_menu_reset`
- Campaign: `synthetic-automotive-service-review`
- Family: `buyer_correction_contradiction_stress`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `false_assumption_not_repaired, repeated_full_menu`
- Buyer script: `['__agent_open__', 'yeah', "that's not my issue"]`
- Final response: The quick check is whether any of these areas is worth a short service advisor inspection review: vehicle issue, repair timing, or warranty or estimate. If not, I can stop here; which part should I check first?

### adv-buyer-says-agent-is-wrong-routesignal_live_demo-04
- Root cause: `stability_guard_menu_reset`
- Campaign: `routesignal_live_demo`
- Family: `buyer_says_agent_is_wrong`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `hostile_response_not_deescalated, repeated_full_menu`
- Buyer script: `['__agent_open__', 'this sounds automated']`
- Final response: This is about inbound demo follow-up: one person should be responsible for the next reply. That prevents missed follow-up. Which part is least clear today?

### adv-hostile-challenging-buyer-routesignal_live_demo-03
- Root cause: `stability_guard_menu_reset`
- Campaign: `routesignal_live_demo`
- Family: `hostile_challenging_buyer`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `hostile_response_not_deescalated, repeated_full_menu`
- Buyer script: `['__agent_open__', 'this is pointless']`
- Final response: This is about inbound demo follow-up: one person should be responsible for the next reply. That prevents missed follow-up. Which part is least clear today?

### adv-hostile-challenging-buyer-routesignal_live_demo-04
- Root cause: `stability_guard_menu_reset`
- Campaign: `routesignal_live_demo`
- Family: `hostile_challenging_buyer`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `hostile_response_not_deescalated, repeated_full_menu`
- Buyer script: `['__agent_open__', 'prove this is useful']`
- Final response: This is about inbound demo follow-up: one person should be responsible for the next reply. That prevents missed follow-up. Which part is least clear today?

### adv-asr-near-miss-gap-phrases-synthetic-automotive-service-review-04
- Root cause: `stability_guard_menu_reset`
- Campaign: `synthetic-automotive-service-review`
- Family: `asr_near_miss_gap_phrases`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `repeated_full_menu`
- Buyer script: `['__agent_open__', 'yeah', 'service timing is long', 'it wastes time']`
- Final response: If vehicle issue, repair timing, or warranty or estimate are actually relevant, a service advisor can do a short service advisor inspection review. If not, I can stop here; should I ask one quick fit question?

### adv-asr-near-miss-gap-phrases-synthetic-b2b-saas-operations-03
- Root cause: `asr_near_miss_gap_not_recognized`
- Campaign: `synthetic-b2b-saas-operations`
- Family: `asr_near_miss_gap_phrases`
- Source: `universal_response_shape`
- Flags: `asr_near_miss_not_clarified`
- Buyer script: `['__agent_open__', 'yeah', 'integration thing is confusing']`
- Final response: Maybe integration, understood. Is that an active concern now, or just something you might want checked later?

### adv-asr-near-miss-gap-phrases-synthetic-membership-plan-review-03
- Root cause: `asr_near_miss_gap_not_recognized`
- Campaign: `synthetic-membership-plan-review`
- Family: `asr_near_miss_gap_phrases`
- Source: `universal_response_shape`
- Flags: `asr_near_miss_not_clarified`
- Buyer script: `['__agent_open__', 'yeah', 'usage thing is unclear']`
- Final response: Maybe usage or value, understood. Is that an active concern now, or just something you might want checked later?

### adv-asr-near-miss-gap-phrases-synthetic-telecom-plan-review-03
- Root cause: `asr_near_miss_gap_not_recognized`
- Campaign: `synthetic-telecom-plan-review`
- Family: `asr_near_miss_gap_phrases`
- Source: `universal_response_shape`
- Flags: `asr_near_miss_not_clarified`
- Buyer script: `['__agent_open__', 'yeah', 'contact switching is confusing']`
- Final response: Maybe contract or switching, understood. Is that an active concern now, or just something you might want checked later?

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

## Recommended Patch Scope
- Patch stability_guard_menu_reset for near configured gaps before broad exploratory work.
- Patch internal_wording_source_live_policy where customer-facing boundary text leaks implementation wording.
- Patch direct question / why-human-review only after the menu reset slice is green.
- Leave callback ambiguity, repeated-response style, and broad hostile-challenge polish as follow-up unless focused validators reproduce a low-risk fix.

## Runtime Behavior Changed
- `false`
