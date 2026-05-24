# BROAD-MENU-SUPPRESSION-AUDIT-001

## Summary
- Source checkpoint: `LIVE-INSPIRED-ADVERSARIAL-DIALOGUE-MATRIX-001`
- Source red findings: `64`
- Audited red findings: `64`
- True defects: `61`
- False positives / expectation artifacts: `2`

## Classification Counts
- `acceptable_scope_boundary`: `2`
- `needs_human_review`: `1`
- `true_appointment_too_early`: `6`
- `true_campaign_contamination`: `4`
- `true_hostile_challenge_not_deescalated`: `18`
- `true_out_of_scope_reset_after_relevant_context`: `10`
- `true_repeated_response_without_progress`: `23`

## Root Cause Counts
- `acceptable_scope_boundary`: `2`
- `needs_human_review`: `1`
- `true_appointment_too_early`: `6`
- `true_campaign_contamination`: `4`
- `true_hostile_challenge_not_deescalated`: `18`
- `true_out_of_scope_reset_after_relevant_context`: `10`
- `true_repeated_response_without_progress`: `23`

## Counts By Selected Action Source
- `contextual_buyer_semantics`: `3`
- `live_voice_session_policy`: `5`
- `pre_speech_conversation_stability_guard`: `5`
- `universal_response_shape`: `51`

## Counts By Scenario Family
- `buyer_correction_contradiction_stress`: `1`
- `buyer_says_agent_is_wrong`: `18`
- `callback_time_too_early_or_ambiguous`: `6`
- `campaign_selector_wrong_campaign_contamination`: `5`
- `commercial_quality_stress`: `5`
- `multi_campaign_contamination_stress`: `9`
- `repeated_answer_variation_anti_loop`: `18`
- `scope_boundary_regulated_detail_stress`: `2`

## Counts By Campaign
- `routesignal_live_demo`: `12`
- `synthetic-automotive-service-review`: `11`
- `synthetic-b2b-saas-operations`: `11`
- `synthetic-insurance-review`: `11`
- `synthetic-membership-plan-review`: `8`
- `synthetic-telecom-plan-review`: `11`

## Top True Defects
### adv-callback-time-too-early-or-ambiguous-routesignal_live_demo-02
- Classification: `true_appointment_too_early`
- Root cause: `true_appointment_too_early`
- Campaign: `routesignal_live_demo`
- Family: `callback_time_too_early_or_ambiguous`
- Source: `universal_response_shape`
- Flags: `appointment_too_early`
- Buyer script: `['__agent_open__', 'tomorrow works']`
- Final response: Got it. I'll note that time for the verified implementation reviewer to follow up.

### adv-callback-time-too-early-or-ambiguous-synthetic-insurance-review-02
- Classification: `true_appointment_too_early`
- Root cause: `true_appointment_too_early`
- Campaign: `synthetic-insurance-review`
- Family: `callback_time_too_early_or_ambiguous`
- Source: `universal_response_shape`
- Flags: `appointment_too_early`
- Buyer script: `['__agent_open__', 'tomorrow works']`
- Final response: Got it. I'll note that time for the licensed insurance specialist to follow up.

### adv-callback-time-too-early-or-ambiguous-synthetic-telecom-plan-review-02
- Classification: `true_appointment_too_early`
- Root cause: `true_appointment_too_early`
- Campaign: `synthetic-telecom-plan-review`
- Family: `callback_time_too_early_or_ambiguous`
- Source: `universal_response_shape`
- Flags: `appointment_too_early`
- Buyer script: `['__agent_open__', 'tomorrow works']`
- Final response: Got it. I'll note that time for the telecom account specialist to follow up.

### adv-callback-time-too-early-or-ambiguous-synthetic-automotive-service-review-02
- Classification: `true_appointment_too_early`
- Root cause: `true_appointment_too_early`
- Campaign: `synthetic-automotive-service-review`
- Family: `callback_time_too_early_or_ambiguous`
- Source: `universal_response_shape`
- Flags: `appointment_too_early`
- Buyer script: `['__agent_open__', 'tomorrow works']`
- Final response: Got it. I'll note that time for the service advisor to follow up.

### adv-callback-time-too-early-or-ambiguous-synthetic-membership-plan-review-02
- Classification: `true_appointment_too_early`
- Root cause: `true_appointment_too_early`
- Campaign: `synthetic-membership-plan-review`
- Family: `callback_time_too_early_or_ambiguous`
- Source: `universal_response_shape`
- Flags: `appointment_too_early`
- Buyer script: `['__agent_open__', 'tomorrow works']`
- Final response: Got it. I'll note that time for the account support specialist to follow up.

### adv-callback-time-too-early-or-ambiguous-synthetic-b2b-saas-operations-02
- Classification: `true_appointment_too_early`
- Root cause: `true_appointment_too_early`
- Campaign: `synthetic-b2b-saas-operations`
- Family: `callback_time_too_early_or_ambiguous`
- Source: `universal_response_shape`
- Flags: `appointment_too_early`
- Buyer script: `['__agent_open__', 'tomorrow works']`
- Final response: Got it. I'll note that time for the implementation specialist to follow up.

### adv-campaign-selector-wrong-campaign-contamination-routesignal_live_demo-01
- Classification: `true_out_of_scope_reset_after_relevant_context`
- Root cause: `true_out_of_scope_reset_after_relevant_context`
- Campaign: `routesignal_live_demo`
- Family: `campaign_selector_wrong_campaign_contamination`
- Source: `universal_response_shape`
- Flags: `out_of_scope_reset_after_relevant_context`
- Buyer script: `['__agent_open__', 'premium pressure is the issue']`
- Final response: That may be outside this call's scope. The quick check here is whether inbound demo follow-up slipping is causing any issue now.

### adv-campaign-selector-wrong-campaign-contamination-synthetic-insurance-review-01
- Classification: `true_out_of_scope_reset_after_relevant_context`
- Root cause: `true_out_of_scope_reset_after_relevant_context`
- Campaign: `synthetic-insurance-review`
- Family: `campaign_selector_wrong_campaign_contamination`
- Source: `universal_response_shape`
- Flags: `out_of_scope_reset_after_relevant_context`
- Buyer script: `['__agent_open__', 'callbacks are a problem']`
- Final response: That may be outside this call's scope. The quick check here is whether premium pressure is causing any issue now.

### adv-campaign-selector-wrong-campaign-contamination-synthetic-telecom-plan-review-01
- Classification: `true_out_of_scope_reset_after_relevant_context`
- Root cause: `true_out_of_scope_reset_after_relevant_context`
- Campaign: `synthetic-telecom-plan-review`
- Family: `campaign_selector_wrong_campaign_contamination`
- Source: `universal_response_shape`
- Flags: `out_of_scope_reset_after_relevant_context`
- Buyer script: `['__agent_open__', 'repair timings are usually pretty long']`
- Final response: That may be outside this call's scope. The quick check here is whether plan fit is causing any issue now.

### adv-campaign-selector-wrong-campaign-contamination-synthetic-automotive-service-review-01
- Classification: `true_out_of_scope_reset_after_relevant_context`
- Root cause: `true_out_of_scope_reset_after_relevant_context`
- Campaign: `synthetic-automotive-service-review`
- Family: `campaign_selector_wrong_campaign_contamination`
- Source: `universal_response_shape`
- Flags: `out_of_scope_reset_after_relevant_context`
- Buyer script: `['__agent_open__', 'coverage availability is the issue']`
- Final response: That may be outside this call's scope. The quick check here is whether repair timing is causing any issue now.

### adv-campaign-selector-wrong-campaign-contamination-synthetic-b2b-saas-operations-01
- Classification: `true_out_of_scope_reset_after_relevant_context`
- Root cause: `true_out_of_scope_reset_after_relevant_context`
- Campaign: `synthetic-b2b-saas-operations`
- Family: `campaign_selector_wrong_campaign_contamination`
- Source: `universal_response_shape`
- Flags: `out_of_scope_reset_after_relevant_context`
- Buyer script: `['__agent_open__', 'premium pressure is the issue']`
- Final response: That may be outside this call's scope. The quick check here is whether manual work is causing any issue now.

### adv-commercial-quality-stress-synthetic-insurance-review-04
- Classification: `true_repeated_response_without_progress`
- Root cause: `true_repeated_response_without_progress`
- Campaign: `synthetic-insurance-review`
- Family: `commercial_quality_stress`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `repeated_response`
- Buyer script: `['__agent_open__', 'yeah', 'premium is a problem', 'that would be useful', 'okay what now']`
- Final response: Quick check for a short licensed coverage review: Is premium pressure causing any issue right now?

### adv-commercial-quality-stress-synthetic-telecom-plan-review-04
- Classification: `true_repeated_response_without_progress`
- Root cause: `true_repeated_response_without_progress`
- Campaign: `synthetic-telecom-plan-review`
- Family: `commercial_quality_stress`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `repeated_response`
- Buyer script: `['__agent_open__', 'yeah', 'plan fit is a problem', 'that would be useful', 'okay what now']`
- Final response: Quick check for a short human plan and availability review: Is plan fit causing any issue right now?

### adv-commercial-quality-stress-synthetic-automotive-service-review-04
- Classification: `true_repeated_response_without_progress`
- Root cause: `true_repeated_response_without_progress`
- Campaign: `synthetic-automotive-service-review`
- Family: `commercial_quality_stress`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `repeated_response`
- Buyer script: `['__agent_open__', 'yeah', 'repair timings are usually pretty long', 'that would be useful', 'okay what now']`
- Final response: Quick check for a short service advisor inspection review: Is repair timing causing any issue right now?

### adv-commercial-quality-stress-synthetic-membership-plan-review-04
- Classification: `true_repeated_response_without_progress`
- Root cause: `true_repeated_response_without_progress`
- Campaign: `synthetic-membership-plan-review`
- Family: `commercial_quality_stress`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `repeated_response`
- Buyer script: `['__agent_open__', 'yeah', 'plan fit is a problem', 'that would be useful', 'okay what now']`
- Final response: Quick check for a short account support or plan-fit review: Is plan fit causing any issue right now?

### adv-commercial-quality-stress-synthetic-b2b-saas-operations-04
- Classification: `true_repeated_response_without_progress`
- Root cause: `true_repeated_response_without_progress`
- Campaign: `synthetic-b2b-saas-operations`
- Family: `commercial_quality_stress`
- Source: `pre_speech_conversation_stability_guard`
- Flags: `repeated_response`
- Buyer script: `['__agent_open__', 'yeah', 'manual work is a problem', 'that would be useful', 'okay what now']`
- Final response: Quick check for a short operations fit review: Is manual work causing any issue right now?

### adv-buyer-says-agent-is-wrong-routesignal_live_demo-01
- Classification: `true_hostile_challenge_not_deescalated`
- Root cause: `true_hostile_challenge_not_deescalated`
- Campaign: `routesignal_live_demo`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that's wrong"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a non-binding workflow review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-routesignal_live_demo-02
- Classification: `true_hostile_challenge_not_deescalated`
- Root cause: `true_hostile_challenge_not_deescalated`
- Campaign: `routesignal_live_demo`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that doesn't make sense"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a non-binding workflow review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-routesignal_live_demo-03
- Classification: `true_hostile_challenge_not_deescalated`
- Root cause: `true_hostile_challenge_not_deescalated`
- Campaign: `routesignal_live_demo`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "you're making assumptions"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a non-binding workflow review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-insurance-review-01
- Classification: `true_hostile_challenge_not_deescalated`
- Root cause: `true_hostile_challenge_not_deescalated`
- Campaign: `synthetic-insurance-review`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that's wrong"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a licensed coverage review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-insurance-review-02
- Classification: `true_hostile_challenge_not_deescalated`
- Root cause: `true_hostile_challenge_not_deescalated`
- Campaign: `synthetic-insurance-review`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that doesn't make sense"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a licensed coverage review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-insurance-review-03
- Classification: `true_hostile_challenge_not_deescalated`
- Root cause: `true_hostile_challenge_not_deescalated`
- Campaign: `synthetic-insurance-review`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "you're making assumptions"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a licensed coverage review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-telecom-plan-review-01
- Classification: `true_hostile_challenge_not_deescalated`
- Root cause: `true_hostile_challenge_not_deescalated`
- Campaign: `synthetic-telecom-plan-review`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that's wrong"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a human plan and availability review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-telecom-plan-review-02
- Classification: `true_hostile_challenge_not_deescalated`
- Root cause: `true_hostile_challenge_not_deescalated`
- Campaign: `synthetic-telecom-plan-review`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that doesn't make sense"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a human plan and availability review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-telecom-plan-review-03
- Classification: `true_hostile_challenge_not_deescalated`
- Root cause: `true_hostile_challenge_not_deescalated`
- Campaign: `synthetic-telecom-plan-review`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "you're making assumptions"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a human plan and availability review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-automotive-service-review-01
- Classification: `true_hostile_challenge_not_deescalated`
- Root cause: `true_hostile_challenge_not_deescalated`
- Campaign: `synthetic-automotive-service-review`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that's wrong"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a service advisor inspection review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-automotive-service-review-02
- Classification: `true_hostile_challenge_not_deescalated`
- Root cause: `true_hostile_challenge_not_deescalated`
- Campaign: `synthetic-automotive-service-review`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that doesn't make sense"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a service advisor inspection review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-automotive-service-review-03
- Classification: `true_hostile_challenge_not_deescalated`
- Root cause: `true_hostile_challenge_not_deescalated`
- Campaign: `synthetic-automotive-service-review`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "you're making assumptions"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether a service advisor inspection review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-membership-plan-review-01
- Classification: `true_hostile_challenge_not_deescalated`
- Root cause: `true_hostile_challenge_not_deescalated`
- Campaign: `synthetic-membership-plan-review`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that's wrong"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether an account support or plan-fit review is useful. Is there any issue here you actually want reviewed?

### adv-buyer-says-agent-is-wrong-synthetic-membership-plan-review-02
- Classification: `true_hostile_challenge_not_deescalated`
- Root cause: `true_hostile_challenge_not_deescalated`
- Campaign: `synthetic-membership-plan-review`
- Family: `buyer_says_agent_is_wrong`
- Source: `universal_response_shape`
- Flags: `hostile_response_not_deescalated`
- Buyer script: `['__agent_open__', "that doesn't make sense"]`
- Final response: Understood. I won't assume that. Let me reset: this call can only check whether an account support or plan-fit review is useful. Is there any issue here you actually want reviewed?

## Top False Positives / Artifacts
### adv-scope-boundary-regulated-detail-stress-routesignal_live_demo-01
- Classification: `acceptable_scope_boundary`
- Campaign: `routesignal_live_demo`
- Family: `scope_boundary_regulated_detail_stress`
- Source: `contextual_buyer_semantics`
- Flags: `out_of_scope_reset_after_relevant_context`
- Buyer script: `['__agent_open__', 'can you tell me exactly what coverage I need']`
- Final response: I can't give coverage advice on this call; that is outside this call's scope. This call is about inbound demo follow-up, so the useful check is whether follow-up is slipping now.

### adv-scope-boundary-regulated-detail-stress-routesignal_live_demo-03
- Classification: `acceptable_scope_boundary`
- Campaign: `routesignal_live_demo`
- Family: `scope_boundary_regulated_detail_stress`
- Source: `contextual_buyer_semantics`
- Flags: `out_of_scope_reset_after_relevant_context`
- Buyer script: `['__agent_open__', 'is coverage available at my address']`
- Final response: I can't give coverage advice on this call; that is outside this call's scope. This call is about inbound demo follow-up, so the useful check is whether follow-up is slipping now.

## Recommended Patch Scope
- Route weak permission and time-constrained permission into one primary diagnostic question before stability guard repair.
- Replace correction/challenge reset text with acknowledge-plus-one-neutral-reset, not diagnostic gap menus.
- Answer product/scope loop complaints in new wording and avoid fallback menu or wrong-contact escape.
- Treat early callback requests as callback preference capture plus one relevance check unless pain/readiness is already established.
- Calibrate ASR red-finding heuristic so 'what should I care' direct value answers are not counted as ASR near-miss failures.

## Runtime Behavior Changed
- `false`
